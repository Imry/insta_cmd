#!/usr/bin/env python
# -*- coding: utf-8 -*-


import sys

from PyQt5.QtWidgets import QApplication

from gui import Main


class App(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.ui = Main()
        self.ui.show()

if __name__ == '__main__':
    # app = QApplication(sys.argv)
    # form = Punctuator()
    # app.exec_()

    app = App(sys.argv)
    sys.exit(app.exec_())
