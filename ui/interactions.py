# coding=utf-8
import os
from connector import rs232

__author__ = 'Igor Jurkowski'

from threading import Thread, Lock
import time
import sys

from PySide.QtGui import QAction, QPushButton, QComboBox, QButtonGroup, QLineEdit, QPlainTextEdit, QFileDialog, \
    QToolButton, QMessageBox, QSpinBox, QCheckBox
from PySide.QtGui import QSortFilterProxyModel, QIntValidator
from PySide import QtCore

from connector.rs232 import get_ports, get_baud_rates, get_serial, get_parities, parity_dictionary, send
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
    LoadFilesDialog = None
    MainWindow = None
    Config = None
    ReaderThread = None
    ReaderLock = Lock()


def open_file_dialog():
    dir_name = QFileDialog.getExistingDirectory(GlobalElements.MainWindow,
                                                u"Wybierz folder",
                                                GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditDirectory").text())
    if dir_name:
        print("Directory changed to: " + dir_name)
        GlobalElements.StatusBar.showMessage(u"Zmiana folderu na " + dir_name)
        GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditDirectory").setText(dir_name)


def setup_load_data_dialog():
    combo_box_format = GlobalElements.LoadFilesDialog.findChild(QComboBox, "comboBoxOutputFormat")
    combo_box_format.clear()
    combo_box_format.addItems(rs232.data_formats)
    GlobalElements.LoadFilesDialog.findChild(QToolButton, "toolButtonDirectory").clicked.connect(open_file_dialog)
    GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditDirectory").setText(GlobalElements.Config["directory"])


def open_load_data():
    setup_load_data_dialog()
    GlobalElements.LoadFilesDialog.show()


def open_settings():
    GlobalElements.SettingsDialog.show()
    setup_port_combobox()
    baud_rate_combo_box = GlobalElements.SettingsDialog.findChild(QComboBox, "comboBoxBaudrate")
    baud_rate_combo_box.setEditText(str(GlobalElements.Config["baudrate"]))
    GlobalElements.StatusBar.showMessage(u"Zmiana ustawień")


def update_load_data_config():
    GlobalElements.Config["directory"] = GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditDirectory").text()
    GlobalElements.Config["start_channel"] = GlobalElements.LoadFilesDialog.findChild(QSpinBox, "spinBoxChannelStart").value()
    GlobalElements.Config["end_channel"] = GlobalElements.LoadFilesDialog.findChild(QSpinBox, "spinBoxChannelEnd").value()
    GlobalElements.Config["output_format"] = GlobalElements.LoadFilesDialog.findChild(QComboBox, "comboBoxOutputFormat").currentText()
    GlobalElements.Config["line_numbers"] = GlobalElements.LoadFilesDialog.findChild(QCheckBox, "checkBoxLineNumbers").isChecked()


def load_data():
    file_name = GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditFilename").text()
    dir_path = GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditDirectory").text()
    file_path = os.path.join(dir_path, file_name)
    if os.path.isfile(file_path):
        msgBox = QMessageBox()
        msgBox.setText(u"Plik o podanej nazwie już istnieje.")
        msgBox.setInformativeText(u"Czy chcesz go nadpisać?")
        msgBox.addButton("Tak", QMessageBox.AcceptRole)
        abortButton = msgBox.addButton("Nie", QMessageBox.Abort)
        msgBox.exec_()
        if msgBox.buttonClicked() == abortButton:
            return
    if file_name:
        update_load_data_config()
        data_reader = DataReader(GlobalElements.Config["start_channel"],
                                 GlobalElements.Config["end_channel"],
                                 GlobalElements.Config["output_format"],
                                 GlobalElements.Config["line_numbers"],
                                 file_path,
                                 GlobalElements.LoadFilesDialog.findChild(QPlainTextEdit, "plainTextEditDescription").toPlainText())
        data_reader.start()
        GlobalElements.LoadFilesDialog.findChild(QLineEdit, "lineEditFilename").clear()
        GlobalElements.LoadFilesDialog.findChild(QPlainTextEdit, "plainTextEditDescription").clear()
        GlobalElements.LoadFilesDialog.accept()
    else:
        msgBox = QMessageBox()
        msgBox.setText(U"Niepoprawna nazwa pliku!")
        msgBox.exec_()


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
    if send(GlobalElements.MainWindow.findChild(QLineEdit, "commandText").text().encode()):
        GlobalElements.StatusBar.showMessage(u"Polecenie wysłane")
    else:
        GlobalElements.StatusBar.showMessage(u"Port zamknięty!")


def setup_main_window(MainWindow, app):
    MainWindow.findChild(QAction, "actionExit").triggered.connect(app.quit)
    MainWindow.findChild(QAction, "actionSettings").triggered.connect(open_settings)
    MainWindow.findChild(QPushButton, "commandSendButton").clicked.connect(send_command)
    MainWindow.findChild(QPushButton, "openLoadData").clicked.connect(open_load_data)
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

    GlobalElements.LoadFilesDialog = load_ui_widget("ui/loadSpectrDataDialog.ui", MainWindow)
    GlobalElements.LoadFilesDialog.findChild(QPushButton, "buttonCancelLoad").clicked.connect(
        GlobalElements.LoadFilesDialog.reject)
    GlobalElements.LoadFilesDialog.findChild(QPushButton, "buttonApproveLoad").clicked.connect(load_data)

    setup_port_combobox()

    # baud rate combo box settings
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

    # parity combo box settings
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


def clean_buffer(ser, data_received_box):
    time.sleep(0.5)
    if ser.isOpen():
        bytes_to_read = ser.inWaiting()
        print("Cleaning buffer of " + str(bytes_to_read) + "B")
        data = ser.read(bytes_to_read)
        print("Received: " + str(data))
        if data:
            data_received_box.appendPlainText(data)


class DataReader(Thread):
    def __init__(self, start_channel, end_channel, output_format, line_numbers, file_path, description):
        Thread.__init__(self)
        self.start_channel = start_channel
        self.end_channel = end_channel
        self.output_format = output_format
        self.line_numbers = line_numbers
        self.file_path = file_path
        self.description = description

    def run(self):
        ser = get_serial()
        data_received_box = GlobalElements.MainWindow.findChild(QPlainTextEdit, "dataReceived")
        end_counter = 0
        with GlobalElements.ReaderLock:
            GlobalElements.StatusBar.showMessage(u"Pobieranie i zapisywanie danych")
            send("PR")
            clean_buffer(ser, data_received_box)
            send(str(self.start_channel))
            send(str(self.end_channel))
            send(str(self.output_format))
            send("Y" if self.line_numbers else "N")
            while True:
                if end_counter > 3:
                    print("Timeout")
                    break
                if ser.isOpen():
                    bytes_to_read = ser.inWaiting()
                    if bytes_to_read:
                        end_counter = 0
                        print("Reading " + str(bytes_to_read) + "B")
                        data = ser.read(bytes_to_read)
                        print("Received: " + str(data))
                        if data:
                            data_received_box.appendPlainText(data)
                            if "\x03" in data:
                                print("End of text received")
                                break
                    else:
                        time.sleep(0.5)
                        end_counter += 1
                else:
                    time.sleep(0.5)
                    end_counter += 1

            GlobalElements.StatusBar.showMessage(u"Dane pobrane")


def setup_serial_reader():
    GlobalElements.ReaderThread = Reader()
    GlobalElements.ReaderThread.reader_alive = True
    GlobalElements.ReaderThread.start()

