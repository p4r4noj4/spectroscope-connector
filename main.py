import sys
import shelve
import threading

from PySide import QtGui

from connector.rs232 import close_serial
from ui.interactions import GlobalElements, setup_main_window, setup_settings_dialog, setup_serial_port, \
    setup_serial_reader
from helpers import load_ui_widget


def fill_defaults():
    GlobalElements.Config.setdefault("baudrate", 9600)
    GlobalElements.Config.setdefault("parity", "Even")
    GlobalElements.Config.setdefault("stopbits", 2)
    GlobalElements.Config.setdefault("bytesize", 7)
    GlobalElements.Config.setdefault("port", 0)


def main():
    app = QtGui.QApplication(sys.argv)
    GlobalElements.Config = shelve.open("config")
    fill_defaults()
    MainWindow = load_ui_widget("ui/mainwindow.ui")
    setup_main_window(MainWindow, app)
    setup_settings_dialog(MainWindow)
    GlobalElements.StatusBar = MainWindow.statusBar()
    setup_serial_port()
    setup_serial_reader()
    GlobalElements.StatusBar.showMessage("Gotowy")

    try:
        MainWindow.show()
        sys.exit(app.exec_())
    finally:
        # cleanup
        print("Cleaning up!")
        GlobalElements.StatusBar.showMessage("Wyłączanie")
        GlobalElements.ReaderThread.stop()
        GlobalElements.ReaderThread.join()
        close_serial()
        GlobalElements.Config.close()


if __name__ == "__main__":
    main()