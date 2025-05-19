# -*- coding: utf-8 -*-

import pibooth
import os
import cv2
from pibooth.utils import LOGGER


class PrinterPlugin(object):

    """Plugin to manage the printer.
    """

    name = 'pibooth-core:printer'

    def __init__(self, plugin_manager):
        self._pm = plugin_manager

    def print_picture(self, cfg, app):
        picture_file = app.previous_picture_file
        border_size = cfg.getint('PICTURE', 'borderless_additional_border')
        
        if border_size > 0:
            LOGGER.info("Adding border of size %d to the picture", border_size)
            image_path = picture_file
            image = cv2.imread(image_path)
            bordered_image = cv2.copyMakeBorder(image, border_size, border_size, border_size, border_size, cv2.BORDER_CONSTANT, value=[255, 255, 255])
            
            output_dir = os.path.join(os.path.dirname(image_path), 'bordered_pictures')
            os.makedirs(output_dir, exist_ok=True)
            picture_file = os.path.join(output_dir, os.path.basename(image_path))
            cv2.imwrite(picture_file, bordered_image)
            
        LOGGER.info("Send final picture to printer")
        app.printer.print_file(picture_file,
                               cfg.getint('PRINTER', 'pictures_per_page'))
        app.count.printed += 1
        app.count.remaining_duplicates -= 1

    @pibooth.hookimpl
    def pibooth_cleanup(self, app):
        app.printer.quit()

    @pibooth.hookimpl
    def state_failsafe_enter(self, cfg, app):
        """Reset variables set in this plugin.
        """
        app.count.remaining_duplicates = cfg.getint('PRINTER', 'max_duplicates')

    @pibooth.hookimpl
    def state_wait_do(self, cfg, app, events):
        if app.find_print_event(events) and app.previous_picture_file and app.printer.is_installed():

            if app.count.remaining_duplicates <= 0:
                LOGGER.warning("Too many duplicates sent to the printer (%s max)",
                               cfg.getint('PRINTER', 'max_duplicates'))
                return

            elif not app.printer.is_ready():
                LOGGER.warning("Maximum number of printed pages reached (%s/%s max)", app.count.printed,
                               cfg.getint('PRINTER', 'max_pages'))
                return

            self.print_picture(cfg, app)

    @pibooth.hookimpl
    def state_processing_enter(self, cfg, app):
        app.count.remaining_duplicates = cfg.getint('PRINTER', 'max_duplicates')

    @pibooth.hookimpl
    def state_processing_do(self, cfg, app):
        if app.previous_picture_file and app.printer.is_ready():
            number = cfg.gettyped('PRINTER', 'auto_print')
            if number == 'max':
                number = cfg.getint('PRINTER', 'max_duplicates')
            for i in range(number):
                if app.count.remaining_duplicates > 0:
                    self.print_picture(cfg, app)

    @pibooth.hookimpl
    def state_print_do(self, cfg, app, events):
        if app.find_print_event(events) and app.previous_picture_file:
            self.print_picture(cfg, app)
