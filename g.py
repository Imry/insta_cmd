#!/usr/bin/env python
# -*- coding: utf-8 -*-


import datetime


STATE_EXT = 'state'
DEBUG_DOWNLOAD_ALL = True

REQUEST_WAIT = 0.5
REQUEST_WAIT_MAX = 40
REPEAT_WAIT = 30
REPEAT_COUNT = 5

CONCURRENT_DOWNLOADS = 25

OPT_POST_COUNT = 'UIPost'.lower()
OPT_POST_COUNT_DEFAULT = 1e6
OPT_POST_UNTIL_DATE = 'IPDate'.lower()
OPT_POST_UNTIL_DATE_DEFAULT = datetime.datetime(1900, 1, 1)
OPT_SKIP_PHOTO = 'Foto'.lower()
OPT_SKIP_FOLLOWERS = 'UILoginIn'.lower()
OPT_SKIP_FOLLOWINGS = 'UILoginOut'.lower()
OPT_LOAD_STATE = 'Load'.lower()
OPT_SAVE_STATE = 'Save'.lower()
