__author__ = 'Igor Jurkowski'

from PySide import QtCore, QtUiTools


def load_ui_widget(uifilename, parent=None):
    loader = QtUiTools.QUiLoader()
    uifile = QtCore.QFile(uifilename)
    uifile.open(QtCore.QFile.ReadOnly)
    ui = loader.load(uifile, parent)
    uifile.close()
    return ui


def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)