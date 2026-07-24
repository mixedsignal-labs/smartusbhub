# Description: Real-time voltage & current oscilloscope for SmartUSBHub.
#              Uses V1/V2 request-response per channel. For V3 stream version
#              see oscilloscope_stream.py.
# copyright: (c) 2026 MixedSignalLab
# license: Apache-2.0
# author: zhang <mixedsignallab@outlook.com>
# email: mixedsignallab@outlook.com
# website: https://www.mixedsignallab.com

import sys
import os
import time
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from smartusbhub import SmartUSBHub

# pyinstaller -w oscilloscope.py --name Oscilloscope --paths=.. --distpath ../app

HISTORY_LEN = 100
COLORS = {"voltage": (255, 220, 0), "current": (218, 0, 102)}


class OscilloscopeApp(QtWidgets.QWidget):
    def __init__(self, hub, poll_interval_ms=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub = hub
        self.poll_interval_ms = poll_interval_ms

        # Resolve channel count from device
        product_info = SmartUSBHub.get_product_info(hub.product_type)
        if not product_info or not product_info.get("enable_adc", False):
            raise RuntimeError(
                f"Product '{getattr(product_info, 'name', 'unknown')}' "
                "does not support voltage/current monitoring."
            )
        n_ch = hub.max_channels or product_info["channels"]
        self.channels = list(range(1, n_ch + 1))

        self.data = {
            "voltage": np.zeros((n_ch, HISTORY_LEN)),
            "current": np.zeros((n_ch, HISTORY_LEN)),
        }

        self.setWindowTitle(
            f"SmartUSBHub Oscilloscope — {product_info['name']} ({n_ch} ch)"
        )
        self._build_ui()

        # Interlock mode blocks CMD_SET_CHANNEL_POWER — switch to normal mode
        mode = self.hub.get_operate_mode()
        if mode == 1:
            print("[oscilloscope] Hub is in interlock mode — switching to normal mode")
            self.hub.set_operate_mode(0)

        self.get_channels_status()

        self.timer = QtCore.QTimer()
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(self.poll_interval_ms)

        self.reconnect_timer = QtCore.QTimer()
        self.reconnect_timer.setInterval(500)
        self.reconnect_timer.timeout.connect(self.try_reconnect)
        self.alert_box = None

    def _build_ui(self):
        root_layout = QtWidgets.QVBoxLayout()
        self.setLayout(root_layout)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose, True)

        # Scrollable area for channels
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QVBoxLayout(container)
        scroll.setWidget(container)
        root_layout.addWidget(scroll)

        self.plots, self.curves, self.labels = [], {"voltage": [], "current": []}, {"voltage": [], "current": []}
        self.buttons, self.checkboxes = [], {"voltage": [], "current": []}

        for i, ch in enumerate(self.channels):
            row = QtWidgets.QHBoxLayout()

            plot_widget = pg.PlotWidget()
            plot_widget.setYRange(0, 5500)
            plot_widget.setLabel("left", f"CH{ch}")
            plot_widget.setMaximumHeight(140)

            for key in ("voltage", "current"):
                label = pg.TextItem("", color=COLORS[key], anchor=(0, 1))
                plot_widget.addItem(label)
                self.labels[key].append(label)
                curve = plot_widget.plot(pen=pg.mkPen(color=COLORS[key], width=1))
                self.curves[key].append(curve)

            self.plots.append(plot_widget)

            # Side controls
            ctrl = QtWidgets.QVBoxLayout()
            ctrl.setSpacing(4)

            btn = QtWidgets.QPushButton(f"CH{ch}")
            btn.setCheckable(True)
            btn.setChecked(True)
            btn.setFixedWidth(55)
            btn.clicked.connect(lambda _, idx=i: self.toggle_channel(idx))
            self.buttons.append(btn)
            ctrl.addWidget(btn)

            for key in ("voltage", "current"):
                cb = QtWidgets.QCheckBox(key.capitalize())
                cb.setChecked(True)
                cb.stateChanged.connect(lambda _, idx=i, k=key: self.toggle_curve(idx, k))
                self.checkboxes[key].append(cb)
                ctrl.addWidget(cb)

            ctrl.addStretch()
            row.addLayout(ctrl)
            row.addWidget(plot_widget)
            container_layout.addLayout(row)

        container_layout.addStretch()

    # ── channel control ──────────────────────────────────────────────────────

    def get_channels_status(self):
        for i, ch in enumerate(self.channels):
            status = self.hub.get_channel_power_status(ch)
            if status is not None:
                self.buttons[i].setChecked(bool(status))

    def toggle_curve(self, idx, key):
        vis = self.checkboxes[key][idx].isChecked()
        self.curves[key][idx].setVisible(vis)
        self.labels[key][idx].setVisible(vis)

    def toggle_channel(self, idx):
        state = 1 if self.buttons[idx].isChecked() else 0
        self.hub.set_channel_power(self.channels[idx], state=state)
        self.get_channels_status()

    # ── data update ──────────────────────────────────────────────────────────

    def update_data(self):
        if not self.hub.is_connected():
            self.on_connection_lost()
            return

        # Batch-query all channels in one V3 request
        measurements = self.hub.get_channel_measurements(*self.channels)
        if measurements is None:
            return

        for i, ch in enumerate(self.channels):
            info = measurements.get(ch, {})
            v = info.get("voltage")
            c = info.get("current")

            if v is not None:
                self.data["voltage"][i] = np.roll(self.data["voltage"][i], -1)
                self.data["voltage"][i, -1] = v
                self.curves["voltage"][i].setData(self.data["voltage"][i])
                self.labels["voltage"][i].setText(f"{v/1000:.3f} V")
                self.labels["voltage"][i].setPos(0, max(v - 300, 0))

            if c is not None:
                self.data["current"][i] = np.roll(self.data["current"][i], -1)
                self.data["current"][i, -1] = c
                self.curves["current"][i].setData(self.data["current"][i])
                self.labels["current"][i].setText(f"{c/1000:.3f} A")
                self.labels["current"][i].setPos(0, max(c - 300, 0))

    # ── reconnect ────────────────────────────────────────────────────────────

    def on_connection_lost(self):
        self.timer.stop()
        if self.alert_box is None:
            self.alert_box = QtWidgets.QMessageBox(self)
            self.alert_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.alert_box.setWindowTitle("Connection Lost")
            self.alert_box.setText("Device disconnected. Trying to reconnect…")
            self.alert_box.setStandardButtons(QtWidgets.QMessageBox.Close)
            self.alert_box.button(QtWidgets.QMessageBox.Close).clicked.connect(
                QtWidgets.QApplication.quit
            )
            self.alert_box.show()
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start()

    def on_connection_restored(self):
        if self.alert_box:
            self.alert_box.close()
            self.alert_box = None
        self.reconnect_timer.stop()
        self.timer.start(self.poll_interval_ms)

    def try_reconnect(self):
        hub = SmartUSBHub.scan_and_connect()
        if hub:
            self.hub = hub
            self.on_connection_restored()
            self.get_channels_status()

    def closeEvent(self, event):
        self.hub.disconnect()
        super().closeEvent(event)


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.lastWindowClosed.connect(app.quit)

    hub = None
    while hub is None:
        hub = SmartUSBHub.scan_and_connect()
        if hub is None:
            time.sleep(0.2)

    osc = OscilloscopeApp(hub)
    osc.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
