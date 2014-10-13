__author__ = 'Igor Jurkowski'

from serial.tools.list_ports import comports
from serial import Serial
import serial


def get_ports():
    global port_dictionary
    ports = comports()
    port_dictionary = dict([(x, y) for y, x, _ in ports])  # dictionary Readable -> Name accepted py Serial
    return sorted(port_dictionary.keys())


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


data_formats = [str(x)+str(y) for x, y in zip("0"*5, [x for x in range(0, 9, 2)])] + [str(x) for x in range(10, 99, 2)]


def close_serial():
    get_serial().close()


def send(command):
    if get_serial().isOpen():
        print("Sending: " + command)
        get_serial().write(command)
        return True
    else:
        return False

