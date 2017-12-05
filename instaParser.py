#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import os
import sys
import traceback

from PyQt5.QtWidgets import QApplication

from gui import Main


logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(filename)-16s %(funcName)-16s:%(lineno)s %(levelname)-8s: %(message)s',
                    handlers=[logging.FileHandler(os.path.join(os.path.dirname(__file__), __file__ + '.log'), 'a+', 'utf-8')])
logging.info('==================================================')


def my_excepthook(type, value, tback):
    # log the exception here
    logging.error("Uncaught exception", exc_info=(type, value, tback))
    # then call the default handler
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook


class App(QApplication):
    def __init__(self, argv):
        QApplication.__init__(self, argv)
        self.ui = Main()
        self.ui.show()


if __name__ == '__main__':
    try:
        app = App(sys.argv)
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(traceback.format_exc())
        # Logs the error appropriately.
