# Description: A GUI application that displays the voltage and current of each channel of the SmartUSBHub in real-time.
# copyright: (c) 2024 EmbeddedTec studio
# license: Apache-2.0
# version: 1.0
# author: EmbeddedTec studio
# email:embeddedtec@outlook.com

import sys
import os

# 添加项目根目录到路径，以便导入smartusbhub模块
# 这样可以从任何目录运行脚本
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from smartusbhub import SmartUSBHub
import time
import pyqtgraph as pg
import numpy as np
import sys
from PyQt5 import QtWidgets, QtCore

# pyinstaller -w oscilloscope.py --name Oscilloscope --paths=.. --distpath ../app

class OscilloscopeApp(QtWidgets.QWidget):
    def __init__(self, hub, delay_interval=1, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hub = hub
        self.delay_interval = delay_interval
        self.channels = [1, 2, 3, 4]
        self.data = {
            "current": np.zeros((len(self.channels), 100)),
            "voltage": np.zeros((len(self.channels), 100)),
        }
        # Set window title
        self.setWindowTitle("Smart USB Hub Oscilloscope")
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)
        self.setAttribute(QtCore.Qt.WA_QuitOnClose, True)

        self.plots = []
        self.curves = {"voltage": [], "current": []}
        self.labels = {"voltage": [], "current": []}
        self.buttons = []
        self.checkboxes = {"voltage": [], "current": []}
        colors = {"voltage": (255, 255, 0), "current": (218, 0, 102)}

        for i in range(len(self.channels)):
            # Create sub-layout for each channel
            row_layout = QtWidgets.QHBoxLayout()

            # Create PlotWidget and add to layout
            plot_widget = pg.PlotWidget()
            plot_widget.setYRange(0, 5500)  # Voltage range 0 - 5500 mV
            plot_widget.setLabel("left", f"Channel {self.channels[i]}")

            # Create label
            label = pg.TextItem("", color=colors["voltage"], anchor=(0, 1))
            plot_widget.addItem(label)
            self.labels["voltage"].append(label)

            label = pg.TextItem("", color=colors["current"], anchor=(0, 1))
            plot_widget.addItem(label)
            self.labels["current"].append(label)

            self.plots.append(plot_widget)

            # Create curves
            for key in ["voltage", "current"]:
                curve = plot_widget.plot(pen=pg.mkPen(color=colors[key], width=1))
                self.curves[key].append(curve)

            # Create a vertical layout for checkboxes
            checkbox_layout = QtWidgets.QVBoxLayout()
            checkbox_layout.insertSpacing(0, 50)

            # Create button for channels toggle
            button = QtWidgets.QPushButton(f"Channel {self.channels[i]}")
            button.setCheckable(True)
            button.setChecked(True)
            button.clicked.connect(lambda _, idx=i: self.toggle_channel(idx))
            self.buttons.append(button)
            checkbox_layout.addWidget(button)

            # Create checkboxes for toggling visibility
            for key in ["voltage", "current"]:
                checkbox = QtWidgets.QCheckBox(f"{key.capitalize()}")
                checkbox.setChecked(True)
                checkbox.stateChanged.connect(
                    lambda _, idx=i, k=key: self.toggle_curve(idx, k)
                )
                self.checkboxes[key].append(checkbox)
                checkbox_layout.addWidget(checkbox)

            row_layout.addLayout(checkbox_layout)
            row_layout.addWidget(plot_widget)
            self.layout.addLayout(row_layout)

        # Get initial channel power status
        self.get_channels_status()
        # Start timer to update data periodically
        self.timer = QtCore.QTimer()
        self.timer.setTimerType(QtCore.Qt.PreciseTimer)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(int(self.delay_interval))
        # Add reconnect timer
        self.reconnect_timer = QtCore.QTimer()
        self.reconnect_timer.setInterval(100)  # 每1秒尝试重连
        self.reconnect_timer.timeout.connect(self.try_reconnect)

    def on_connection_lost(self):
        """Handle device disconnection."""
        if not hasattr(self, "alert_box") or self.alert_box is None:
            self.alert_box = QtWidgets.QMessageBox(self)
            self.alert_box.setIcon(QtWidgets.QMessageBox.Warning)
            self.alert_box.setWindowTitle("Connection Lost!")
            self.alert_box.setText("Connection Lost. Trying to reconnect...")
            self.alert_box.setStandardButtons(QtWidgets.QMessageBox.Close)
            self.alert_box.button(QtWidgets.QMessageBox.Close).clicked.connect(
                self.close_application
            )
            self.alert_box.show()
        if not self.reconnect_timer.isActive():
            self.reconnect_timer.start()

    def on_connection_restored(self):
        """Handle device reconnection."""
        if hasattr(self, "alert_box") and self.alert_box is not None:
            self.alert_box.close()
            self.alert_box = None
        if self.reconnect_timer.isActive():
            self.reconnect_timer.stop()

    def try_reconnect(self):
        new_hub = auto_connect_to_hub()
        if new_hub:
            self.hub = new_hub
            print("[INFO] Reconnected successfully.")
            self.on_connection_restored()
            self.get_channels_status()

    def close_application(self):
        """Handle application close action."""
        QtWidgets.QApplication.quit()

    def closeEvent(self, event):
        self.hub.disconnect()
        QtWidgets.QApplication.quit()

    def get_channels_status(self):
        # Get the status of each channel and update the buttons
        for i, channel in enumerate(self.channels):
            status = self.hub.get_channel_power_status(channel)

            if status:
                print(f"Channel {channel} is on")
            else:
                print(f"Channel {channel} is off")

            if status is not None:
                self.buttons[i].setChecked(status == 1)

    def toggle_curve(self, channel_idx, data_type):
        # Toggle the visibility of the selected curve
        visible = self.checkboxes[data_type][channel_idx].isChecked()
        self.curves[data_type][channel_idx].setVisible(visible)
        self.labels[data_type][channel_idx].setVisible(visible)

    def toggle_channel(self, channel_idx):
        # Toggle the state of the selected channel
        state = 1 if self.buttons[channel_idx].isChecked() else 0
        self.hub.set_channel_power(self.channels[channel_idx], state=state)
        self.get_channels_status()

    def update_data(self):
        if self.hub.is_connected() is False:
            self.on_connection_lost()
            return
        # Update voltage data, curve, and label
        for i, channel in enumerate(self.channels):
            # Fetch new value
            new_voltage = self.hub.get_channel_voltage(channel)
            if new_voltage is not None:
                # Update data arrays
                self.data["voltage"][i] = np.roll(self.data["voltage"][i], -1)
                self.data["voltage"][i, -1] = new_voltage
                # Update curves
                self.curves["voltage"][i].setData(self.data["voltage"][i])

                # Update voltage label
                voltage_in_volts = new_voltage / 1000.0
                self.labels["voltage"][i].setText(f"{voltage_in_volts:.3f} V")
                self.labels["voltage"][i].setPos(0, new_voltage - 300)

            # Fetch new value
            new_current = self.hub.get_channel_current(channel)
            if new_current is not None:
                # Update data arrays
                self.data["current"][i] = np.roll(self.data["current"][i], -1)
                self.data["current"][i, -1] = new_current
                # Update curves
                self.curves["current"][i].setData(self.data["current"][i])

                # Update current label
                current_in_ma = new_current / 1000.0
                self.labels["current"][i].setText(f"{current_in_ma:.3f} A")
                self.labels["current"][i].setPos(0, new_current - 300)


def auto_connect_to_hub():
    return SmartUSBHub.scan_and_connect()
def main():
    app = QtWidgets.QApplication(sys.argv)
    app.lastWindowClosed.connect(app.quit)
    #pop up a window to scan for hub and connect
    while True:
        hub = SmartUSBHub.scan_and_connect()
        if hub:
            break
        time.sleep(0.1)


    # Start the oscilloscope application
    oscilloscope = OscilloscopeApp(hub)
    oscilloscope.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
