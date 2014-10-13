## description

Project allows easy control of spectroscope through rs232 serial port. 
Simple GUI provides ways to configure connection and run .

Most of the texts are in polish for now.

### prerequisites

1. Qt 4.8
2. Python 2+ (PySerial seems to have problems with Python 3+)
  * PySide
  * PySerial
  * PyQtGraph

You can install Python libraries using pip command after installing Python:

`pip install pyside` for each library

Or just use provided requirements file:

`pip install -r requirements.txt`

##### known issues:

* if there is problem with SciPy/NumPy installation for PyQtGraph - try using official installers:
 * [SciPy](http://www.scipy.org/install.html)
 * [NumPy](http://docs.scipy.org/doc/numpy/user/install.html)

#### MIT license