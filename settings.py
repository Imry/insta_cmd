#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import base64

from PyQt5 import QtWidgets

import ui_settings

# password save in base64, better than nothing

default_config = {
    "user": {
        "username": "",
        "password": ""
    },
    "load": {
        "load_new_users": True,
        "max_threads": 5,
        "thread_delay": 0.1
    }
}


class Settings(QtWidgets.QDialog, ui_settings.Ui_Dialog):
    def __init__(self, fn):
        super(self.__class__, self).__init__()
        self.setupUi(self)
        self.fn = fn
        self.config = default_config
        self.load()

    def load(self):
        if not os.path.isfile(self.fn):
            with open(self.fn, 'w', encoding='utf-8') as c_f:
                json.dump(self.config, c_f, indent=4)
        else:
            with open(self.fn, 'r', encoding='utf-8') as c_f:
                self.config = json.load(c_f)
        self.from_config()

    def save(self):
        self.to_config()
        with open(self.fn, 'w', encoding='utf-8') as c_f:
            json.dump(self.config, c_f, indent=4)

    def from_config(self):
        user = self.config.get('user', {})
        self.username.setText(user.get('username', ''))
        self.password.setText(base64.b64decode(user.get('password', '').encode('utf-8')).decode('utf-8'))
        load = self.config.get('load', {})
        self.cb_load_new.setChecked(load.get('load_new_users', True))
        self.sb_max_threads.setValue(load.get('max_threads', True))

    def to_config(self):
        self.config['user']['username'] = self.username.text()
        self.config['user']['password'] = base64.b64encode(self.password.text().encode('utf-8')).decode('utf-8')
        self.config['load']['load_new_users'] = self.cb_load_new.isChecked()
        self.config['load']['max_threads'] = self.sb_max_threads.value()
