#!/usr/bin/env python

from webkit2png import WebkitRenderer
from PyQt4.QtGui import QApplication
from PyQt4.QtCore import QTimer, Qt
import sys, signal


class ScreenShooter(object):
    def __init__(self):
        self.app = QApplication([])
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.shots = []
        self.renderers = {}

    def _get_renderer(self, width, height):
        try:
            return self.renderers[(width, height)]
        except:
            renderer = WebkitRenderer(scaleRatio='crop', scaleTransform='smooth', scaleToWidth=width, scaleToHeight=height)
            self.renderers[(width, height)] = renderer
            return renderer
        
    def __take_screenshots(self):
        for shot in self.shots:
            image = self._get_renderer(shot['size'][0], shot['size'][1]).render(shot['url'])
            image.save(shot['filename'], 'png')
        sys.exit(0)

    def add_shot(self, url, filename, size):
        self.shots.append({'url': url, 'filename': filename, 'size': size})
        
    def run(self):
        QTimer().singleShot(0, self.__take_screenshots)
        self.app.exec_()

if __name__ == '__main__':
    s = ScreenShooter()
    s.add_shot('http://google.com', 'google.png')
    s.add_shot('http://amazon.com', 'amazon.png')
    s.run()
