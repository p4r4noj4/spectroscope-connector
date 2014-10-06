# coding=utf-8
from connector import rs232

__author__ = 'Igor Jurkowski'

from threading import Thread, Lock
import time
import sys

from PySide.QtGui import QAction, QPushButton, QComboBox, QButtonGroup, QLineEdit, QPlainTextEdit
from PySide.QtGui import QSortFilterProxyModel, QIntValidator
from PySide import QtCore

from connector.rs232 import get_ports, get_baud_rates, get_serial, get_parities, parity_dictionary
from helpers import load_ui_widget, num


class IntegerSorterProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):

        left_s = self.sourceModel().data(left)
        right_s = self.sourceModel().data(right)
        try:
            left_i = int(left_s)
            right_i = int(right_s)
            return left_i < right_i
        except ValueError:
            return False


class GlobalElements:
    StatusBar = None
    SettingsDialog = None
    MainWindow = None
    Config = None
    ReaderThread = None
    ReaderLock = Lock()


def open_settings():
    GlobalElements.SettingsDialog.show()
    setup_port_combobox()
    baud_rate_combo_box = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxBaudrate")
    baud_rate_combo_box.setEditText(str(GlobalElements.Config["baudrate"]))
    GlobalElements.StatusBar.showMessage(u"Zmiana ustawień")


def close_settings():
    GlobalElements.StatusBar.showMessage(u"Ustawienia odrzucone")
    GlobalElements.SettingsDialog.reject()


def update_baud_rate():
    baud_rate_combo_box = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxBaudrate")
    current = baud_rate_combo_box.currentText()
    if baud_rate_combo_box.validator().validate(current, 0)[0] == QIntValidator.State.Acceptable:
        if baud_rate_combo_box.findText(current) == -1:
            baud_rate_combo_box.addItem(current)
    GlobalElements.Config["baudrate"] = int(current)

    baud_rate_combo_box.model().sort(0)


def accept_settings():
    update_baud_rate()
    GlobalElements.Config["parity"] = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxParity").currentText()
    GlobalElements.Config["port"] = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxPort").currentText()
    GlobalElements.Config["bytesize"] = int(GlobalElements.SettingsDialog.findChild(QButtonGroup, "buttonGroupByteSize") \
                                            .checkedButton().text())
    GlobalElements.Config["stopbits"] = num(GlobalElements.SettingsDialog.findChild(QButtonGroup, "buttonGroupStopBits") \
                                            .checkedButton().text())
    setup_serial_port()
    GlobalElements.StatusBar.showMessage("Ustawienia zaakceptowane")
    GlobalElements.SettingsDialog.accept()


def send_command():
    if get_serial().isOpen():
        get_serial().write(GlobalElements.MainWindow.findChild(QLineEdit, "commandText").text().encode())
        GlobalElements.StatusBar.showMessage(u"Polecenie wysłane")
    else:
        GlobalElements.StatusBar.showMessage(u"Port zamknięty!")


def setup_main_window(MainWindow, app):
    MainWindow.findChild(QAction, "actionExit").triggered.connect(app.quit)
    MainWindow.findChild(QAction, "actionSettings").triggered.connect(open_settings)
    MainWindow.findChild(QPushButton, "commandSendButton").clicked.connect(send_command)
    GlobalElements.MainWindow = MainWindow


def setup_port_combobox():
    port_combo_box = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxPort")
    port_combo_box.clear()
    port_combo_box.addItems(get_ports())
    port_combo_box.setCurrentIndex(port_combo_box.findText(str(GlobalElements.Config["port"])))


def setup_settings_dialog(MainWindow):
    GlobalElements.SettingsDialog = load_ui_widget("ui/settingsDialog.ui", MainWindow)
    GlobalElements.SettingsDialog.findChild(QPushButton, "okSettingsButton").clicked.connect(accept_settings)
    GlobalElements.SettingsDialog.findChild(QPushButton, "cancelSettingsButton").clicked.connect(close_settings)

    setup_port_combobox()

    #baud rate combo box settings
    baud_rate_combo_box = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxBaudrate")
    proxy_model = IntegerSorterProxyModel()
    proxy_model.setSourceModel(baud_rate_combo_box.model())
    baud_rate_combo_box.model().setParent(proxy_model)
    baud_rate_combo_box.setModel(proxy_model)

    baud_rate_combo_box.addItems([str(x) for x in get_baud_rates()])
    baud_rate_combo_box.setEditable(True)

    baud_rate_combo_box.setValidator(QIntValidator(50, 4000000))
    config_baud_rate = GlobalElements.Config["baudrate"]
    if config_baud_rate not in get_baud_rates():
        baud_rate_combo_box.addItem(str(config_baud_rate))
        baud_rate_combo_box.model().sort(0)
    baud_rate_combo_box.setCurrentIndex(baud_rate_combo_box.findText(str(config_baud_rate)))

    #parity combo box settings
    parity_combo_box = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxParity")
    parity_combo_box.addItems(get_parities())
    parity_combo_box.setCurrentIndex(parity_combo_box.findText(GlobalElements.Config["parity"]))

    #radio buttons settings
    btns = GlobalElements.SettingsDialog.findChild(QButtonGroup, "buttonGroupByteSize").buttons()
    for btn in btns:
        if btn.text() == str(GlobalElements.Config["bytesize"]):
            btn.click()
            break

    btns = GlobalElements.SettingsDialog.findChild(QButtonGroup, "buttonGroupStopBits").buttons()
    for btn in btns:
        if btn.text() == str(GlobalElements.Config["stopbits"]):
            btn.click()


def update_port_description(config_field, text_field):
    GlobalElements.MainWindow.findChild(QLineEdit, text_field).setText(str(GlobalElements.Config[config_field]))


def setup_serial_port():
    ser = get_serial()
    if GlobalElements.Config["port"] in rs232.port_dictionary and \
                    ser.port != rs232.port_dictionary[GlobalElements.Config["port"]]:
        ser.close()
        ser.port = rs232.port_dictionary[GlobalElements.Config["port"]]
        ser.open()
    ser.baudrate = GlobalElements.Config["baudrate"]
    ser.parity = parity_dictionary[GlobalElements.Config["parity"]]
    ser.bytesize = GlobalElements.Config["bytesize"]
    ser.stopbits = GlobalElements.Config["stopbits"]
    update_port_description("port", "textPort")
    update_port_description("baudrate", "textBaudRate")
    update_port_description("parity", "textParity")
    update_port_description("bytesize", "textByteSize")
    update_port_description("stopbits", "textStopBits")


class Reader(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.reader_alive = True

    def run(self):
        ser = get_serial()
        data_received_box = GlobalElements.MainWindow.findChild(QPlainTextEdit, "dataReceived")
        while self.reader_alive:
            with GlobalElements.ReaderLock:
                if ser.isOpen():
                    bytes_to_read = ser.inWaiting()
                    if bytes_to_read:
                        print("Reading " + str(bytes_to_read) + "B")
                        data = ser.read(bytes_to_read)
                        print("Received: " + str(data))
                        if data:
                            data_received_box.appendPlainText(data)
                    else:
                        time.sleep(0.5)
                else:
                    time.sleep(0.5)

    def stop(self):
        self.reader_alive = False


def setup_serial_reader():
    GlobalElements.ReaderThread = Reader()
    GlobalElements.ReaderThread.reader_alive = True
    GlobalElements.ReaderThread.start()

