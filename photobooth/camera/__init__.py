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

from PIL import Image, ImageOps, ImageDraw, ImageStat

from io import BytesIO

from ..Config import Config
from .PictureDimensions import PictureDimensions
from .. import StateMachine
from ..Threading import Workers
import os
# Available camera modules as tuples of (config name, module name, class name)
modules = (
    ('python-gphoto2', 'CameraGphoto2', 'CameraGphoto2'),
    ('gphoto2-cffi', 'CameraGphoto2Cffi', 'CameraGphoto2Cffi'),
    ('gphoto2-commandline', 'CameraGphoto2CommandLine',
     'CameraGphoto2CommandLine'),
    ('opencv', 'CameraOpenCV', 'CameraOpenCV'),
    ('picamera', 'CameraPicamera', 'CameraPicamera'),
    ('dummy', 'CameraDummy', 'CameraDummy'))

class Camera:
    counter =0
    def __init__(self, config, comm, CameraModule):

        super().__init__()

        self._comm = comm
        self._cfg = config
        self._cam = CameraModule

        self._cap = None
        self._pic_dims = None

        self._is_preview = self._cfg.getBool('Photobooth', 'show_preview')
        self._is_keep_pictures = self._cfg.getBool('Storage', 'keep_pictures')

        rot_vals = {0: None, 90: Image.ROTATE_90, 180: Image.ROTATE_180,
                    270: Image.ROTATE_270}
        self._rotation = rot_vals[self._cfg.getInt('Camera', 'rotation')]
        self._mode_automatic = self._cfg.getBool('Camera', 'auto_enable')

    def startup(self):

        self.counter+=1
        #print("counter", self.counter)
        camera_default_size = (6000, 4000)
        if(self.counter<2):
            self._cap = self._cam()

            logging.info('Using camera {} preview functionality'.format(
                'with' if self._is_preview else 'without'))

            test_picture = self._cap.getPicture(self._mode_automatic)
            if self._rotation is not None:
                test_picture = test_picture.transpose(self._rotation)

            self._is_preview = self._is_preview and self._cap.hasPreview
            camera_default_size = test_picture.size
            print("test_picture.size", test_picture.size)
        self._pic_dims = PictureDimensions(self._cfg, camera_default_size)
        cwd = os.getcwd()
        background = self._cfg.get('Picture', 'background')
        if len(background) > 0:
            logging.info('Using background "{}"'.format(background))
            bg_picture = Image.open(cwd + '/' + background)
            self._template = bg_picture.resize(self._pic_dims.outputSize)
            print(self._template)
        else:
            self._template = Image.new('RGB', self._pic_dims.outputSize,
                                       (255, 255, 255))

        self.setIdle()
        self._comm.send(Workers.MASTER, StateMachine.CameraEvent('ready'))

    def teardown(self, state):

        if self._cap is not None:
            self._cap.cleanup()

    def run(self):

        for state in self._comm.iter(Workers.CAMERA):
            self.handleState(state)

        return True

    def handleState(self, state):

        if isinstance(state, StateMachine.StartupState):
            self.startup()
        elif isinstance(state, StateMachine.GreeterState):
            self.prepareCapture()
        elif isinstance(state, StateMachine.CountdownState):
            self.capturePreview()
        elif isinstance(state, StateMachine.CaptureState):
            self.capturePicture(state)
        elif isinstance(state, StateMachine.AssembleState):
            self.assemblePicture()
        elif isinstance(state, StateMachine.TeardownState):
            self.teardown(state)

    def setActive(self):

        self._cap.setActive()

    def setIdle(self):

        if self._cap.hasIdle:
            self._cap.setIdle()

    def prepareCapture(self):

        self.setActive()
        self._pictures = []

    def capturePreview(self):
        self.iso = "3200"

        if self._is_preview:
            while self._comm.empty(Workers.CAMERA):

                picture = self._cap.getPreview(self._mode_automatic, self.iso)
                ##check brightness
                #im = picture.convert('L') #convert to black white
                #stat = ImageStat.Stat(im)
                #mean_brightness = stat.mean[0]
                #if(mean_brightness>150):

                ##
                if self._rotation is not None:
                    picture = picture.transpose(self._rotation)
                #picture = picture.resize(self._pic_dims.previewSize)
                picture = ImageOps.mirror(picture)
                byte_data = BytesIO()
                picture.save(byte_data, format='jpeg')
                self._comm.send(Workers.GUI,
                                StateMachine.CameraEvent('preview', byte_data))

    def capturePicture(self, state):

        self.setIdle()
        picture = self._cap.getPicture(self._mode_automatic)
        print("picture format: ", picture)
        config = Config('photobooth.cfg')

        grayscale = config.getInt('Picture', 'picture_grayscale')
        if(grayscale == 1):
            picture =picture.convert('L')
        if self._rotation is not None:
            picture = picture.transpose(self._rotation)
        byte_data = BytesIO()
        picture.save(byte_data, format='jpeg')
        self._pictures.append(byte_data)
        self.setActive()

        if self._is_keep_pictures:
            self._comm.send(Workers.WORKER,
                            StateMachine.CameraEvent('capture', byte_data))

        if state.num_picture < self._pic_dims.totalNumPictures:
            self._comm.send(Workers.MASTER,
                            StateMachine.CameraEvent('countdown'))
        else:
            self._comm.send(Workers.MASTER,
                            StateMachine.CameraEvent('assemble'))

    def add_corners(self, im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    def assemblePicture(self):
        #print("getinfo_background", .getBackgroundInfo())
        #laod background info from config
        config = Config('photobooth.cfg')
        self._cfg = config
        background_image = False
        background = self._cfg.get('Picture', 'background')
        print("self._pic_dims.totalNumPictures: ", self._pic_dims.totalNumPictures)
        if(self._pic_dims.totalNumPictures<=1):
            background = ""
        else:
            background = self._cfg.get('Picture', 'background')
        print("background length: ", (background))
        if len(background) > 0:
            background_image = True
            logging.info('Using background "{}"'.format(background))
            bg_picture = Image.open(background)
            self._template = bg_picture.resize(self._pic_dims.outputSize, Image.ANTIALIAS)
        else:
            self._template = Image.new('RGB', self._pic_dims.thumbnailSize,
                                       (255, 255, 255))

        self.setIdle()
        grayscale = config.getInt('Picture', 'picture_grayscale')
        picture = self._template.copy()
        for i in range(self._pic_dims.totalNumPictures):
            shot = Image.open(self._pictures[i])

            if(background_image):
                shot = self.add_corners(shot, 150)


            resized = shot.resize(self._pic_dims.thumbnailSize)
            if(background_image):
                width, height = resized.size
                offset = 54
                resized_ = resized
                if (grayscale == 1):
                    resized_ = resized.convert('RGBA')
                    #resized_ = resized_.resize((1863, 1242), Image.ANTIALIAS)

                white_border = Image.new('RGBA', (width + offset, height + offset), "white")
                print("bild groesse: ",resized_.size)
                white_border.paste(resized_, (int(offset/2), int(offset/2)), resized_)
                resized = self.add_corners(white_border, 60)
            if(background_image):
                picture.paste(resized, (self._pic_dims.thumbnailOffset[i][0]-int(offset/2),
                                        self._pic_dims.thumbnailOffset[i][1]-int(offset/2)), resized)
            else:
                logo = Image.open("logo_fotobox.png")
                widthl, heightl = logo.size
                widthp, heightp = resized.size
                ratio_logo = heightl/widthl
                ratio_logo_fotostripe = 5
                logo_res = logo.resize((int(widthp/ratio_logo_fotostripe), int(ratio_logo*widthp/ratio_logo_fotostripe)), Image.ANTIALIAS)
                resized.paste(logo_res, (int(widthp*0.8), int(heightp*0.70)), logo_res)
                picture.paste(resized, (0,0))
           # if(grayscale == 1):
             #   picture = picture.convert("L")


        byte_data = BytesIO()
        picture = picture.convert('RGB')
        picture.save(byte_data, format='JPEG')

        self._comm.send(Workers.MASTER,
                         StateMachine.CameraEvent('review', byte_data, self._pictures))

                        #StateMachine.CameraEvent('review', byte_data))
        self._pictures = []
