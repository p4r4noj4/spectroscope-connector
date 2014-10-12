__author__ = 'Igor Jurkowski'

from PySide import QtCore, QtUiTools


def load_ui_widget(uifilename, parent=None, custom_widgets=None):
    custom_widgets = [] if custom_widgets is None else custom_widgets
    loader = QtUiTools.QUiLoader()
    for widget in custom_widgets:
        loader.registerCustomWidget(widget)
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