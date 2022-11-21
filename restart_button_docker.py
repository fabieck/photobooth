#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
ZetCode PyQt5 tutorial

This example shows a tooltip on
a window and a button.

Author: Jan Bodnar
Website: zetcode.com
Last edited: August 2017
"""
import signal
import subprocess
import sys
from PyQt5 import  QtCore, QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton, QApplication, QMainWindow)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QSize
import time
signal.signal(signal.SIGINT, signal.SIG_DFL)
class MainWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)

        self.setMinimumSize(QSize(100, 30))
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setWindowTitle("PyQt button example - pythonprogramminglanguage.com")

        pybutton = QPushButton('Neustart', self)
        pybutton.setFont(QFont('SansSerif', 15))
        pybutton.clicked.connect(self.clickMethod)
        pybutton.resize(pybutton.sizeHint())
        pybutton.move(0, 0)
        self.setGeometry(1366-99, 0, 99, 33)

    def clickMethod(self):
        bashCommand = "cd /home/fabian/PycharmProjects/photobooth && ./run_restart.sh"

        bashCommand_kill = "docker kill docker_photobooth"
        try:
            output = subprocess.call(['bash', '-c', bashCommand_kill])
        except:
            print("fotobox is not running")
        time.sleep(1)
        output = subprocess.Popen(['bash', '-c', bashCommand])

def sigint_handler(*args):
    """Handler for the SIGINT signal."""
    sys.stderr.write('\r')
    if QMessageBox.question(None, '', "Are you sure you want to quit?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No) == QMessageBox.Yes:
        QApplication.quit()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QtWidgets.QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit( app.exec_() )
