# Description: Real-time voltage & current oscilloscope — V3 stream protocol.
#              A background thread blocks on get_stream_channel_measurements() and
#              emits a Qt signal for every frame the MCU pushes — the UI updates
#              at exactly the MCU stream rate (no fixed display timer).
#              For the request-response version see oscilloscope.py.
# copyright: (c) 2026 MixedSignalLab
# license: Apache-2.0
# author: zhang <mixedsignallab@outlook.com>
# email: mixedsignallab@outlook.com
# website: https://www.mixedsignallab.com

import sys
import os
import time
import threading
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

HISTORY_LEN = 200
COLORS_V = [(255,220,0),(0,220,255),(0,255,100),(255,120,0),(180,0,255),(255,60,60),(100,255,200)]
COLORS_I = [(218,0,102),(0,120,255),(0,180,60),(200,80,0),(120,0,200),(200,30,30),(60,200,140)]


class StreamWorker(QtCore.QThread):
    data_arrived = QtCore.pyqtSignal(dict)

    def __init__(self, hub, channels):
        super().__init__()
        self.hub = hub
        self.channels = channels
        self._running = True

    def run(self):
        while self._running:
            data = self.hub.get_stream_channel_measurements(
                *self.channels, timeout=1.0, wait_new_sample=True)
            if data:
                self.data_arrived.emit(data)

    def stop(self):
        self._running = False
        self.wait(2000)


class StreamOscilloscopeApp(QtWidgets.QMainWindow):
    def __init__(self, hub: SmartUSBHub, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub = hub

        product_info = SmartUSBHub.get_product_info(hub.product_type)
        if not product_info or not product_info.get("enable_adc", False):
            raise RuntimeError("Product does not support voltage/current monitoring.")

        n_ch = hub.max_channels or product_info["channels"]
        self.channels = list(range(1, n_ch + 1))

        self.setWindowTitle(
            f"SmartUSBHub Stream Oscilloscope — {product_info['name']} ({n_ch} ch)")

        self._v_buf = np.full((n_ch, HISTORY_LEN), np.nan)
        self._i_buf = np.full((n_ch, HISTORY_LEN), np.nan)
        self._frame_count = 0
        self._last_fps_time = time.perf_counter()

        self._build_ui()

        # Interlock mode blocks CMD_SET_CHANNEL_POWER — switch to normal mode
        mode = self.hub.get_operate_mode()
        if mode == 1:
            print("[oscilloscope] Switching from interlock to normal mode")
            self.hub.set_operate_mode(0)

        # Sync initial button states from device
        for i, ch in enumerate(self.channels):
            status = self.hub.get_channel_power_status(ch)
            if status is not None:
                self._ch_buttons[i].setChecked(bool(status))

        self.hub.set_channel_measurement_stream(*self.channels, enabled=True)

        self._worker = StreamWorker(self.hub, self.channels)
        self._worker.data_arrived.connect(self._on_data)
        self._worker.start()

    def _set_power(self, ch: int, turn_on: bool):
        threading.Thread(
            target=self.hub.set_channel_power,
            args=(ch,),
            kwargs={"state": 1 if turn_on else 0},
            daemon=True,
        ).start()

    def _build_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QVBoxLayout(central)

        toolbar = QtWidgets.QHBoxLayout()
        root.addLayout(toolbar)
        toolbar.addWidget(QtWidgets.QLabel("Channels:"))

        self._ch_buttons = []
        for ch in self.channels:
            btn = QtWidgets.QPushButton(f"CH{ch}")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedWidth(44)
            btn.clicked.connect(lambda checked, c=ch: self._set_power(c, checked))
            self._ch_buttons.append(btn)
            toolbar.addWidget(btn)

        toolbar.addSpacing(16)
        self._show_v = QtWidgets.QCheckBox("Voltage")
        self._show_v.setChecked(True)
        self._show_v.stateChanged.connect(
            lambda s: [c.setVisible(bool(s)) for c in self._curves_v])
        self._show_i = QtWidgets.QCheckBox("Current")
        self._show_i.setChecked(True)
        self._show_i.stateChanged.connect(
            lambda s: [c.setVisible(bool(s)) for c in self._curves_i])
        toolbar.addWidget(self._show_v)
        toolbar.addWidget(self._show_i)
        toolbar.addStretch()

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        root.addWidget(scroll)
        container = QtWidgets.QWidget()
        grid = QtWidgets.QGridLayout(container)
        grid.setSpacing(3)
        scroll.setWidget(container)

        for col, title in enumerate(("Voltage (mV)", "Current (mA)")):
            lbl = QtWidgets.QLabel(title)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            grid.addWidget(lbl, 0, col)

        self._curves_v, self._curves_i = [], []
        self._labels_v, self._labels_i = [], []
        self._fresh_leds = []

        for idx, ch in enumerate(self.channels):
            cv = COLORS_V[idx % len(COLORS_V)]
            ci = COLORS_I[idx % len(COLORS_I)]

            for col, (curves, labels, color, y_max, unit) in enumerate([
                (self._curves_v, self._labels_v, cv, 5500, "mV"),
                (self._curves_i, self._labels_i, ci, 3000, "mA"),
            ]):
                pw = pg.PlotWidget()
                pw.setYRange(0, y_max)
                pw.setLabel("left", f"CH{ch}", units=unit)
                pw.setMaximumHeight(120)
                pw.showGrid(x=False, y=True, alpha=0.25)
                lbl = pg.TextItem("—", color=color, anchor=(0, 1))
                pw.addItem(lbl)
                curve = pw.plot(pen=pg.mkPen(color=color, width=1.5))
                curves.append(curve)
                labels.append(lbl)
                grid.addWidget(pw, idx + 1, col)

            led = QtWidgets.QLabel("●")
            led.setFixedWidth(14)
            led.setToolTip("Green=fresh, Red=stale")
            self._fresh_leds.append(led)
            grid.addWidget(led, idx + 1, 2, QtCore.Qt.AlignVCenter)

        self.statusBar().showMessage("Waiting for stream…")

    @QtCore.pyqtSlot(dict)
    def _on_data(self, measurements: dict):
        self._frame_count += 1
        for idx, ch in enumerate(self.channels):
            info = measurements.get(ch, {})
            v, c, fresh = info.get("voltage"), info.get("current"), info.get("fresh", False)

            if v is not None:
                self._v_buf[idx] = np.roll(self._v_buf[idx], -1)
                self._v_buf[idx, -1] = v
                self._curves_v[idx].setData(self._v_buf[idx])
                self._labels_v[idx].setText(f"{v/1000:.3f} V")
                self._labels_v[idx].setPos(0, max(v - 250, 0))

            if c is not None:
                self._i_buf[idx] = np.roll(self._i_buf[idx], -1)
                self._i_buf[idx, -1] = c
                self._curves_i[idx].setData(self._i_buf[idx])
                self._labels_i[idx].setText(f"{c:.0f} mA")
                self._labels_i[idx].setPos(0, max(c - 150, 0))

            self._fresh_leds[idx].setStyleSheet(
                "color: #00cc44;" if fresh else "color: #cc2200;")

        now = time.perf_counter()
        if now - self._last_fps_time >= 1.0:
            fps = self._frame_count / (now - self._last_fps_time)
            self.statusBar().showMessage(f"Stream: {fps:.0f} frames/s")
            self._frame_count = 0
            self._last_fps_time = now

    def closeEvent(self, event):
        self._worker.stop()
        try:
            self.hub.set_channel_measurement_stream(*self.channels, enabled=False)
            self.hub.disconnect()
        except Exception:
            pass
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.lastWindowClosed.connect(app.quit)

    hub = None
    while hub is None:
        hub = SmartUSBHub.scan_and_connect()
        if hub is None:
            time.sleep(0.2)

    osc = StreamOscilloscopeApp(hub)
    osc.resize(900, 700)
    osc.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
