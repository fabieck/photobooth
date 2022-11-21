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
from PIL import Image, ImageQt
from PyQt5 import QtCore, QtGui
from PyQt5.QtPrintSupport import QPrinter
import cups
from ..Threading import Workers
from .. import StateMachine

from . import Printer

import time


class PrinterPyQt5(Printer):

    def __init__(self, page_size, print_pdf=False):

        super().__init__(page_size)
        self._printer = QPrinter(QPrinter.HighResolution)
        self._printer.setPageSize(QtGui.QPageSize(QtCore.QSizeF(*page_size),
                                                  QtGui.QPageSize.Millimeter))
        self._printer.setColorMode(QPrinter.Color)

        logging.info('Using printer "%s"', self._printer.printerName())

        self._print_pdf = print_pdf
        if self._print_pdf:
            logging.info('Using PDF printer')
            self._counter = 0
            self._printer.setOutputFormat(QPrinter.PdfFormat)
            self._printer.setFullPage(True)

    def print(self, picture, _comm):
        _comm.send(Workers.MASTER, StateMachine.GuiEvent('print'))

        picture.save('temp_file.jpg', format='JPEG')

        if self._print_pdf:
            self._printer.setOutputFileName('print_%d.pdf' % self._counter)
            self._counter += 1
        #list = (os.listdir("webserver/static/people_photo"))  # returns list
        #path_to_photo = "webserver/static/people_photo/" + list[0]
        #print("path_to_photo ", path_to_photo)
        imageWidth = 2330
        imageHeight = 3496
        ##create white box because otherwise photo is not printed completely

        act_picture = Image.open('temp_file.jpg')
        width, height = act_picture.size
        print("width", width)
        if(width==2000):#2000 1165
            temp_img_width = 4206 #4206 2450
            temp_img_height = 6230 #6230 3630
            im = Image.new("RGB", (temp_img_width, temp_img_height), (255, 255, 255))
            bilda = Image.open('temp_file.jpg')
            bildb = Image.open('temp_file.jpg')
            im.paste(bilda, box=(100, 17)) #100, 17  58, 10
            im.paste(bildb, box=(2094,17)) ##2094,17 58+width-3, 10
          #  im.paste(bilda, box=(int((temp_img_width/2-width+58)/2), 10))
          #  im.paste(bildb, box=(int((temp_img_width/2-width+55)/2)+1165, 10))
            #im.paste(bildb, (1165, 0))
            test = im
            test.save("temp_file.jpg", "JPEG")
            fileName = "temp_file.jpg"
        else:
            #temp_img_width = 3550
            #temp_img_height = 2366
            #act_picture = Image.open('temp_file.jpg')
            #im = Image.new("RGB", (temp_img_width, temp_img_height), (255, 255, 255))
            #im.paste(act_picture, box=(10, 10))
            #test = im
            #test.save("temp_file.jpg", "JPEG")
            fileName = "temp_file.jpg"

        ##connect Printer
        conn = cups.Connection()
        print("connect ptirnt:", conn)
        actual_jobs = conn.getJobs()
        actual_jobs_str = str(actual_jobs)  # covert to string
        # find number of jobs
        newstr = ''.join((ch if ch in '0123456789' else ' ') for ch in actual_jobs_str)
        listOfNumbers = [int(i) for i in newstr.split()]
        print(listOfNumbers)
        if (listOfNumbers != []):
            conn.cancelJob(listOfNumbers[0], purge_job=False)
        if (conn.getJobs() == {}):
            print('keine jobs offen')
        # name of printer
        printer_name = QPrinter(QPrinter.HighResolution).printerName()
        print("printer_name: ", printer_name)
        # name of file
        os.system("lp -o media='4x6.bl' -o mediatype='photopaper' " + fileName)
        # printid = conn.printFile(printer_name, fileName, " ", {"media": "4x6.bl","photopaper": "True"})
        print_job_succeed = False
        loop = True
        no_paper = False
        time.sleep(20)
        loop_counter = 0
        while (loop):
            time.sleep(2)
            loop_counter +=1
            printers = conn.getPrinters()
            self._printer = QPrinter(QPrinter.HighResolution)
            try:
                status = printers[printer_name]['printer-state-message']
            except:
                status = "kein Drucker vorhanden"
            prepare = "Vorbereitung zum Drucken..."
            error_no_paper_ge = '[Supportcode: 1000] Das Papier w. nicht richtig eingelegt.'
            error_no_paper_en = '[Support Code: 1000] The paper is not set correctly.'
            #no_connection = 'Drucker suchen.'
            #no_printer = "kein Drucker vorhanden"

            if (status == error_no_paper_ge or status == error_no_paper_en):
                print("Kein Papier eingelget")
                time.sleep(1)
                actual_jobs = conn.getJobs()
                actual_jobs_str = str(actual_jobs)  # covert to string
                # find number of jobs
                newstr = ''.join((ch if ch in '0123456789' else ' ') for ch in actual_jobs_str)
                listOfNumbers = [int(i) for i in newstr.split()]
                print(listOfNumbers)
                if (listOfNumbers != []):
                    conn.cancelJob(listOfNumbers[0], purge_job=False)
                if (conn.getJobs() == {}):
                    print('keine jobs offen')
                time.sleep(1)
                print_job_succeed = False
                no_paper = True
                loop = False
            elif (status == ''):
                print_job_succeed = True
                loop = False
                no_paper = False

            elif(loop_counter==8):
                print("no_connection_state")
                print_job_succeed = False
                no_paper = False
                loop = False

        logging.info('Printing picture')
        if(print_job_succeed):
            _comm.send(Workers.MASTER, StateMachine.GuiEvent('print_ready'))
        elif(no_paper):
            _comm.send(Workers.MASTER, StateMachine.GuiEvent('no_paper'))
        else:
            _comm.send(Workers.MASTER, StateMachine.GuiEvent('no_printer_connection'))
            time.sleep(5)
            _comm.send(Workers.MASTER, StateMachine.GuiEvent('cancel_print'))



