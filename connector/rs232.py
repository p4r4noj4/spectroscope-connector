__author__ = 'Igor Jurkowski'

from serial.tools.list_ports import comports
from serial import Serial
import serial


def get_ports():
    return sorted(comports())


def get_baud_rates():
    return Serial.BAUDRATES


def get_serial():
    try:
        get_serial.ser
    except AttributeError:
        get_serial.ser = Serial(timeout=5)
    return get_serial.ser


def get_parities():
    return ["None", "Even", "Odd", "Space", "Mark"]


parity_dictionary = {
    "None": serial.PARITY_NONE,
    "Even": serial.PARITY_EVEN,
    "Odd": serial.PARITY_ODD,
    "Space": serial.PARITY_SPACE,
    "Mark": serial.PARITY_MARK
}


def close_serial():
    get_serial().close()
