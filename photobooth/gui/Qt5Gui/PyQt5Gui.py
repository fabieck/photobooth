#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import subprocess

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from PIL import Image, ImageQt

from ...Config import Config
from ...StateMachine import GuiEvent, TeardownEvent
from ...Threading import Workers

from ..GuiSkeleton import GuiSkeleton
from ..GuiPostprocessor import GuiPostprocessor

from . import styles
from . import Frames
from . import Receiver
from . import Worker


class PyQt5Gui(GuiSkeleton):

    def __init__(self, argv, config, comm):

        super().__init__(comm)

        self._cfg = config

        self._initUI(argv)
        self._initReceiver()
        self._initWorker()

        self._picture = None
        self._postprocess = GuiPostprocessor(self._cfg)

    def run(self):

        exit_code = self._app.exec_()
        self._gui = None
        return exit_code

    def _initUI(self, argv):

        self._disableTrigger()

        # Load stylesheet
        style = self._cfg.get('Gui', 'style')
        filename = next((file for name, file in styles if name == style))
        with open(os.path.join(os.path.dirname(__file__), filename), 'r') as f:
            stylesheet = f.read()

        # Create application and main window
        self._app = QtWidgets.QApplication(argv)
        self._app.setStyleSheet(stylesheet)
        self._gui = PyQt5MainWindow(self._cfg, self._handleKeypressEvent)

        # Load additional fonts
        fonts = ['photobooth/gui/Qt5Gui/fonts/AmaticSC-Regular.ttf',
                 'photobooth/gui/Qt5Gui/fonts/AmaticSC-Bold.ttf']
        self._fonts = QtGui.QFontDatabase()
        for font in fonts:
            self._fonts.addApplicationFont(font)

    def _initReceiver(self):


        # Create receiver thread
        self._receiver = Receiver.Receiver(self._comm)
        self._receiver.notify.connect(self.handleState)
        self._receiver.start()

    def _initWorker(self):

        # Create worker thread for time consuming tasks to keep gui responsive
        self._worker = Worker.Worker(self._comm)
        self._worker.start()

    def _enableEscape(self):

        self._is_escape = True

    def _disableEscape(self):

        self._is_escape = False

    def _enableTrigger(self):

        self._is_trigger = True

    def _disableTrigger(self):

        self._is_trigger = False

    def _setWidget(self, widget):

        self._gui.setCentralWidget(widget)

    def close(self):

        if self._gui.close():
            self._comm.send(Workers.MASTER, TeardownEvent(TeardownEvent.EXIT))

    def teardown(self, state):

        if state.target == TeardownEvent.WELCOME:
            self._comm.send(Workers.MASTER, GuiEvent('welcome'))
        elif state.target in (TeardownEvent.EXIT, TeardownEvent.RESTART):
            self._worker.put(None)
            self._app.exit(0)

    def showError(self, state):

        logging.error('%s: %s', state.origin, state.message)

        err_msg = self._cfg.get('Photobooth', 'overwrite_error_message')
        if len(err_msg) > 0:
            message = err_msg
        else:
            message = 'Error: ' + state.message

        reply = QtWidgets.QMessageBox.critical(
            self._gui, state.origin, message,
            QtWidgets.QMessageBox.Retry | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Cancel)

        if reply == QtWidgets.QMessageBox.Retry:
            self._comm.send(Workers.MASTER, GuiEvent('retry'))
        else:
            self._comm.send(Workers.MASTER, GuiEvent('abort'))

    def showWelcome(self, state):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.Welcome(
            lambda: self._comm.send(Workers.MASTER, GuiEvent('start')),
            self._showSetDateTime, self._showSettings, self.close))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()

    def showFormatSelection(self, state):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.FormatSelection(
            lambda: self._comm.send(Workers.MASTER, GuiEvent('start')), self._cfg, lambda: self._comm.send(Workers.MASTER, GuiEvent('grau'))))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()
        if self._cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def showFormatSelectionGrau(self, state):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.FormatSelectionGrau(
            lambda: self._comm.send(Workers.MASTER, GuiEvent('start')), self._cfg, lambda: self._comm.send(Workers.MASTER, GuiEvent('farbe'))))
        if QtWidgets.QApplication.overrideCursor() != 0:
            QtWidgets.QApplication.restoreOverrideCursor()
        if self._cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def showStartup(self, state):

        self._disableTrigger()
        self._enableEscape()
        self._setWidget(Frames.WaitMessage(_('Starting the photobooth...')))
        if self._cfg.getBool('Gui', 'hide_cursor'):
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.BlankCursor)

    def showIdle(self, state):

        self._enableEscape()
        self._enableTrigger()
        self._setWidget(Frames.IdleMessage(
            lambda: self._comm.send(Workers.MASTER, GuiEvent('trigger'))))

    def showGreeter(self, state):

        self._enableEscape()
        self._disableTrigger()

        num_pic = (self._cfg.getInt('Picture', 'num_x'),
                   self._cfg.getInt('Picture', 'num_y'))
        skip_last = self._cfg.getBool('Picture', 'skip_last')
        greeter_time = self._cfg.getInt('Photobooth', 'greeter_time') * 1000

        self._setWidget(Frames.GreeterMessage(
            *num_pic, skip_last,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('countdown'))))
        QtCore.QTimer.singleShot(
            greeter_time,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('countdown')))

    def showCountdown(self, state):

        countdown_time = self._cfg.getInt('Photobooth', 'countdown_time')
        self._setWidget(Frames.CountdownMessage(
            countdown_time,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('capture'))))

    def updateCountdown(self, event):

        picture = Image.open(event.picture)
        config = Config('photobooth.cfg')
        grayscale = config.getInt('Picture', 'picture_grayscale')
        if(grayscale == 1):
            picture = picture.convert("L")
        self._gui.centralWidget().picture = ImageQt.ImageQt(picture)
        self._gui.centralWidget().update()

    def showCapture(self, state):

        num_pic = (self._cfg.getInt('Picture', 'num_x'),
                   self._cfg.getInt('Picture', 'num_y'))
        skip_last = self._cfg.getBool('Picture', 'skip_last')
        self._setWidget(Frames.CaptureMessage(state.num_picture, *num_pic,
                                              skip_last))

    def showAssemble(self, state):
        #x = subprocess.Popen(["python3", "/Users/fabianeckert/git/photobooth/photobooth/gui/Qt5Gui/test.py"])

        self._setWidget(Frames.WaitMessage(_('Processing picture...')))

    def showReview(self, state):
        config = Config('photobooth.cfg')
        grayscale = config.getInt('Picture', 'picture_grayscale')
        picture_main, pic_list = state.picture
        picture = Image.open(picture_main)
        self._picture = ImageQt.ImageQt(picture)
        self._picture_single = []
        if (len(pic_list) > 2):
            for i in range(0,len(pic_list)):
                single_picture = Image.open(pic_list[i]).convert('RGB')
                self._picture_single.append(ImageQt.ImageQt(single_picture))

        review_time = self._cfg.getInt('Photobooth', 'display_time') * 1000
        tasks = self._postprocess.get(self._picture, self._comm)
        postproc_t = self._cfg.getInt('Photobooth', 'postprocess_time')
        self._setWidget(Frames.PictureMessage(self._picture, self._picture_single, tasks, self._worker, state.just_printed,
            lambda: self._comm.send(Workers.MASTER, GuiEvent('idle')), lambda: self._comm.send(Workers.MASTER, GuiEvent('download')),
            postproc_t * 1000))
        #QtCore.QTimer.singleShot(
       #     review_time,
        #    lambda: self._comm.send(Workers.MASTER, GuiEvent('postprocess')))
        self._postprocess.do(self._picture)

    def showDownload(self, state):
        postproc_t = self._cfg.getInt('Photobooth', 'postprocess_time')
        self._setWidget(Frames.DownloadPictureMessage(state.num_picture, lambda: self._comm.send(Workers.MASTER, GuiEvent('review')),
            postproc_t * 1000))


    def showPrinting(self, state):
        self._setWidget(Frames.WaitMessage(_('Bild wird gedruckt...')))

    def showPrintingNoPaper(self, state):

        self._setWidget(Frames.PrintNoPaper(lambda: self._comm.send(Workers.MASTER, GuiEvent('review'))))


    def showPrinterNoConnection(self, state):

        self._setWidget(Frames.PrintNoConMessage(_('Drucker hat ein Problem oder kann nicht gefunden werden :(')))



    def _handleKeypressEvent(self, event):

        if self._is_escape and event.key() == QtCore.Qt.Key_Escape:
            self._comm.send(Workers.MASTER,
                            TeardownEvent(TeardownEvent.WELCOME))
        elif self._is_trigger and event.key() == QtCore.Qt.Key_Space:
            self._comm.send(Workers.MASTER, GuiEvent('trigger'))

    def _showSetDateTime(self):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.SetDateTime(
            self.showWelcome,
            lambda: self._comm.send(Workers.MASTER,
                                    TeardownEvent(TeardownEvent.RESTART))))

    def _showSettings(self):

        self._disableTrigger()
        self._disableEscape()
        self._setWidget(Frames.Settings(
            self._cfg, self._showSettings, self.showWelcome,
            lambda: self._comm.send(Workers.MASTER,
                                    TeardownEvent(TeardownEvent.RESTART))))


class PyQt5MainWindow(QtWidgets.QMainWindow):

    def __init__(self, config, keypress_handler):

        super().__init__()

        self._cfg = config
        self._handle_key = keypress_handler
        self._initUI()

    def _initUI(self):

        self.setWindowTitle('Photobooth')

        if self._cfg.getBool('Gui', 'fullscreen'):
            self.showFullScreen()
            #self.showMaximized()
        else:
            self.setFixedSize(self._cfg.getInt('Gui', 'width'),
                              self._cfg.getInt('Gui', 'height'))
            self.show()

    def closeEvent(self, e):

        reply = QtWidgets.QMessageBox.question(self, _('Confirmation'),
                                               _('Quit Photobooth?'),
                                               QtWidgets.QMessageBox.Yes |
                                               QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()

    def keyPressEvent(self, event):

        self._handle_key(event)
