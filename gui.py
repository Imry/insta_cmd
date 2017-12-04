#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv, json, os, codecs, datetime, traceback
import threading
from multiprocessing.dummy import Pool
import logging

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QHeaderView, QMenu
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QThreadPool, QObject
from PyQt5.Qt import Qt, QIntValidator

import ui_main
import ui_settings
import ui_filter

# import instagram_private_api
from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError,
    __version__ as client_version)

# import url_parser

import pagination
import excel
import api
import pool

AUTH_FILE_NAME = 'auth.json'
COOKIE_FILE = 'cookie.json'


class Headers():
    def __init__(self):
        self.headers = []

    def find_header(self, idx):
        return self.headers[idx][0]

class DataModel(QtCore.QAbstractTableModel, Headers):
    def __init__(self, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.data = []
        self.headers = [('username', 'Ник', QHeaderView.ResizeToContents),
                        ('full_name', 'Имя', QHeaderView.ResizeToContents),
                        ('media_count', 'Постов', QHeaderView.ResizeToContents),
                        ('following_count', 'Подписок', QHeaderView.ResizeToContents),
                        ('follower_count', 'Подпичиков', QHeaderView.ResizeToContents),
                        ('status', 'Обработан', QHeaderView.ResizeToContents),
                        ('img', 'Фото', QHeaderView.Stretch),
                        ('external_url', 'Ссылка', QHeaderView.Stretch),
                        ('biography', 'Инфо', QHeaderView.Stretch)
                        ]

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.headers[section][1]
        return None

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        col = self.find_header(index.column())
        row = self.data[index.row()]

        if col == 'status':
            media = len(row.get('media', []))
            following = len(row.get('following', []))
            follower = len(row.get('follower', []))

            if media + following + follower == 0:
                return 'Не обработан'
            else:
                if row.get('media_cursor', None) != '':
                    media = str(media) + '+'
                if row.get('following_cursor', None) != '':
                    following = str(following) + '+'
                if row.get('follower_cursor', None) != '':
                    follower = str(follower) + '+'
                return 'Постов: %s\nПодписок: %s\nПодписчиков: %s'%(media, following, follower)
        else:
            return row.get(col, None)

    def sort(self, col, order):
        # self.layoutAboutToBeChanged.emit()
        self.beginResetModel()
        hdr = self.headers[col][0]
        self.data = sorted(self.data, key=lambda x: x.get(hdr, 0), reverse=order==Qt.DescendingOrder)
        self.endResetModel()
        # self.layoutChanged.emit()

    def _set(self, username, key, value):
        # if username[0] != '@': username = '@' + username
        for d in self.data:
            if d['username'] == username:
                d[key] = value
                break

    def _append(self, username, key, value):
        # if username[0] != '@': username = '@' + username
        for d in self.data:
            if d['username'] == username:
                if key not in d:
                    d[key] = value
                else:
                    d[key].extend(value)
                break

    def _set2(self, username, key_value):
        # if username[0] != '@': username = '@' + username
        for d in self.data:
            if d['username'] == username:
                for k, v in key_value.items():
                    d[k] = v
                return

    def _get(self, username):
        for d in self.data:
            if d['username'] == username:
                return d

    def find_id(self, id):
        for d in self.data:
            if d['id'] == id:
                return d['username']

class PostModel(QtCore.QAbstractTableModel, Headers):
    def __init__(self, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.data = []
        self.headers = [
            # ('caption_simple', 'Заголовок', QHeaderView.ResizeToContents),
            ('like_count', 'Лайки', QHeaderView.ResizeToContents),
            ('taken_at_simple', 'Дата/Время', QHeaderView.ResizeToContents),
            ('comment_count', 'Комментариев', QHeaderView.ResizeToContents),
            ('comment_status', 'Статус', QHeaderView.ResizeToContents),
            ('caption_simple', 'Заголовок', QHeaderView.Stretch),
            ('location_simple', 'Место', QHeaderView.Stretch),
            ('url', 'Ссылка', QHeaderView.Stretch),
            ('media_simple', 'Медиа', QHeaderView.Stretch),
            # ('comment_simple', 'Комментарии', QHeaderView.Stretch)
        ]

        self.parent = parent

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.headers[section][1]
        return None

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        col = self.find_header(index.column())
        row = index.row()
        if col == 'comment_status':
            if len(self.data[row]['comment_simple']) == self.data[row]['comment_count']:
                return 'Комментариев: %s'%(len(self.data[row]['comment_simple']))
            else:
                return 'Не обработан'
        else:
            return self.data[row].get(col, None)

    def sort(self, col, order):
        # self.layoutAboutToBeChanged.emit()
        self.beginResetModel()
        hdr = self.headers[col][0]
        self.data = sorted(self.data, key=lambda x: x.get(hdr, 0), reverse=order==Qt.DescendingOrder)
        self.endResetModel()
        # self.layoutChanged.emit()

    def _set_data(self, data):
        self.beginResetModel()
        self.data = data
        self.endResetModel()

class UsersModel(QtCore.QAbstractTableModel, Headers):
    def __init__(self, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.data = []
        self.headers = [
            ('username', 'Ник', QHeaderView.ResizeToContents),
            ('full_name', 'Имя', QHeaderView.ResizeToContents),
            ('profile_pic_url', 'Фото', QHeaderView.Stretch)
        ]
        self.parent = parent

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.headers[section][1]
        return None

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        col = self.find_header(index.column())
        row = index.row()
        return self.data[row].get(col, None)

    def _set_data(self, data):
        self.beginResetModel()
        self.data = data
        self.endResetModel()

class CommentsModel(QtCore.QAbstractTableModel, Headers):
    def __init__(self, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.data = []
        self.headers = [
            ('username', 'Имя', QHeaderView.ResizeToContents),
            ('text', 'Текст', QHeaderView.Stretch)
        ]
        self.parent = parent

    def rowCount(self, parent):
        return len(self.data)

    def columnCount(self, parent):
        return len(self.headers)

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self.headers[section][1]
        return None

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        col = self.find_header(index.column())
        row = index.row()
        return self.data[row].get(col, None)

    def _set_data(self, data):
        self.beginResetModel()
        self.data = data
        self.endResetModel()

class Settings(QtWidgets.QDialog, ui_settings.Ui_Dialog):
    def __init__(self, username, password):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.username.setText(username)
        self.password.setText(password)

    #     self.buttonBox.accepted.connect(self.submitclose)
    #
    # def submitclose(self):
    #     self.accept()

class Filter(QtWidgets.QDialog, ui_filter.Ui_Dialog):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.e_post.setValidator(QIntValidator(0, 99999, self))

class Main(QtWidgets.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        auth = {'username': '', 'password': ''}
        if not os.path.isfile(AUTH_FILE_NAME):
            with open(AUTH_FILE_NAME, 'w', encoding='utf-8') as auth_fn:
                json.dump(auth, auth_fn, indent=4)
        else:
            with open(AUTH_FILE_NAME, 'r', encoding='utf-8') as auth_fn:
                auth = json.load(auth_fn)
        self.api = None
        self.connector = api.Connector(self.api, COOKIE_FILE)

        self.settings_dialog = Settings(auth['username'], auth['password'])
        self.filter_dialog = Filter()

        self.model = DataModel(self.user_list)
        self.user_list.setModel(self.model)
        for i, h in enumerate(self.model.headers):
            if h[2] is not None:
                self.user_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.user_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.posts = PostModel()
        self.post_list.setModel(self.posts)
        for i, h in enumerate(self.posts.headers):
            if h[2] is not None:
                self.post_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.post_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.post_list.horizontalHeader().setMaximumSectionSize(2000)
        # self.post_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

        self.follower = UsersModel()
        self.follower_list.setModel(self.follower)
        for i, h in enumerate(self.follower.headers):
            if h[2] is not None:
                self.follower_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.follower_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.following = UsersModel()
        self.following_list.setModel(self.following)
        for i, h in enumerate(self.following.headers):
            if h[2] is not None:
                self.following_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.following_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.comments = CommentsModel()
        self.comments_list.setModel(self.comments)
        for i, h in enumerate(self.comments.headers):
            if h[2] is not None:
                self.comments_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.comments_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.last_select = ''

        self.preparser = pool.Parser(worker=self.load_user_info)
        # self.work = pool.Work()
        self.comments_loader = pool.CommentsLoader(worker=self.get_media_comments)

        self.errors = 0
        self.prepare_status_bar()
        self.set_progress_ready()
        self._connect_all()

        self.login(auth['username'], auth['password'])

    def prepare_status_bar(self):
        self.sb_connection = QtWidgets.QLabel('')
        self.statusbar.addWidget(self.sb_connection)

        self.sb_items = QtWidgets.QLabel('')
        self.statusbar.addWidget(self.sb_items)

        self.sb_stage = QtWidgets.QLabel('Загрузите базу')
        self.statusbar.addWidget(self.sb_stage)

        self.sb_progress = QtWidgets.QProgressBar()
        self.statusbar.addWidget(self.sb_progress)

        self.sb_error = QtWidgets.QLabel('Ошибок: 0')
        self.statusbar.addWidget(self.sb_error)

    def _connect_all(self):
        self.connector.finished.connect(self.set_api)

        self.action_load.triggered.connect(self.csv_load)
        self.action_save.triggered.connect(self.save_data)
        self.action_exit.triggered.connect(self.exit)

        self.action_settngs.triggered.connect(self.settings)
        # self.action_login.triggered.connect(self.login)
        # self.action_logout.triggered.connect(self.logout)

        self.connector.status.connect(self.sb_connection.setText)
        self.settings_dialog.login.clicked.connect(self.settings_login)

        self.btn_start.clicked.connect(self.preload)
        self.btn_prepare.clicked.connect(self.load_user_media)
        self.btn_comments.clicked.connect(self.load_comments)
        # self.btn_stop.clicked.connect(self.stop)
        self.user_list.clicked.connect(self.show_posts)
        self.post_list.clicked.connect(self.show_comments)
        # self.user_list.doubleClicked.connect(self.open_url)

        self.btn_filter.toggled.connect(self.filter)
        self.btn_filter_settings.clicked.connect(self.filter_settings)

    def csv_load(self):
        def is_in_data(name):
            for d in self.model.data:
                if d.get('username', '') == name:
                    return True
            return False
        file = QtWidgets.QFileDialog.getOpenFileName(self, caption='Выберете csv файл', filter='text (*.csv)')
        if file:
            if file[0] != '':
                csv_name = file[0]
                with open(csv_name, newline='') as csv_fn:
                    names_reader = csv.reader(csv_fn, delimiter=';')
                    l = 0
                    for row in names_reader:
                        name = row[0]
                        if name.startswith('@'): name = name[1:]
                        if not is_in_data(name):
                            l += 1
                            self.model.beginResetModel()
                            self.model.data.append({'username': name})
                            self.model.endResetModel()
                    self.sb_progress.setMaximum(1)
                    self.sb_progress.setValue(1)
                    self.sb_items.setText('%s / %s'%(l, l))
                    self.sb_stage.setText('Загружены пользователи')

    def save_data(self):
        data = [self.model.data[s] for s in [i.row() for i in self.user_list.selectionModel().selectedRows()] if self.model.data[s].get('id', None) != None]
        if len(data) == 0:
            return
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        for d in data:
            try:
                excel.save_user(d, os.path.join(file, d['username'] + '.xls'))
            except Exception as e:
                logging.error(e)

    def get_user_info(self,username):
        if not self.api:
            return {}
        try:
            r = self.api.username_info(username)
            if r['status'] == 'ok':
                return r['user']
        except Exception as e:
            logging.error(e)
            return {}

    def load_user_info(self, username):
        # ui = url_parser.get_user_info(username)
        ui = self.get_user_info(username)
        if ui != {}:
            selection = [i.row() for i in self.user_list.selectionModel().selectedRows()]
            self.model.beginResetModel()
            self.model._set2(username, {'id': ui.get('pk', 0),
                                        'img': ui.get('hd_profile_pic_url_info', {}).get('url', ''),
                                        'full_name': ui.get('full_name', ''),
                                        'following_count': ui.get('following_count', ''),
                                        'follower_count': ui.get('follower_count', ''),
                                        'external_url': ui.get('external_url', ''),
                                        'biography': ui.get('biography', ''),
                                        'media_count': ui.get('media_count', '')
                                        })
            self.model.endResetModel()
            for s in selection:
                self.user_list.selectRow(s)
        else:
            self.increase_errors()

    # def set_user_status(self, name, status):
    #     self.model._set(name, 'status', status)

    def show_posts(self, index):
        if not index:
            return
        row = index.row()
        user = self.model.data[row]
        self.last_select = user['username']
        self.posts._set_data(user.get('media', []))
        self.following._set_data(user.get('following', []))
        self.follower._set_data(user.get('follower', []))

    def show_comments(self, index):
        if not index:
            return
        row = index.row()
        post = self.posts.data[row]
        self.comments._set_data(post.get('comment_simple', []))

    def show_errors(self):
        self.sb_error.setText('Ошибок: %s'%(self.errors))

    def increase_errors(self):
        self.errors += 1
        self.show_errors()

    def preparser_progress(self, v):
        self.sb_progress.setValue(v)
        m = self.sb_progress.maximum()
        self.sb_items.setText('%s / %s'%(v, m))

    def preload(self):
        self.set_progress_work()
        data = [d['username'] for d in self.model.data if d.get('id', 0) == 0]
        self.errors = 0
        self.show_errors()
        self.sb_progress.setValue(0)
        self.sb_progress.setMaximum(len(data))
        self.sb_stage.setText('Предзагрузка')
        self.sb_items.setText(' 0 / %s'%len(data))

        self.btn_stop.clicked.connect(self.preparser.stop)
        self.preparser.progress.connect(self.preparser_progress)
        self.preparser.finished.connect(self.set_progress_ready)

        self.preparser.set_data(data)
        self.preparser.set_worker(self.load_user_info)

        self.preparser.start()

    def get_user_following(self, user_id, max_id=None):
        if not self.api:
            return False, [], max_id
        try:
            items = []
            items_u = set()
            for results, cursor in pagination.page(self.api.user_following, args={'user_id': user_id}, wait=0, max_id=max_id):
                if results.get('users'):
                    items = results['users']
                items_u = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in {v['pk']:v for v in items}.values()]
                yield True, items_u, cursor
        except Exception as e:
            logging.error(e)
            return False, [], max_id

    def get_user_followers(self, user_id, max_id=None):
        if not self.api:
            return False, [], max_id
        try:
            items = []
            items_u = set()
            for results, cursor in pagination.page(self.api.user_followers, args={'user_id': user_id}, wait=0, max_id=max_id):
                if results.get('users'):
                    items = results['users']
                items_u = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in {v['pk']:v for v in items}.values()]
                # yield True, items_u, cursor
                yield True, items, cursor
        except Exception as e:
            logging.error(e)
            return False, [], max_id

    def prepare_post(self, post):
        if 'location' in post and post['location'] != None:
            loc = []
            location = post['location']
            for l in ['name', 'address', 'sity']:
                ll = location.get(l, '')
                if ll != '':
                    loc.append(ll)
            post['location_simple'] = '%s\n%s'%(
                ', '.join(loc),
                'https://www.instagram.com/explore/locations/%s/'%location['pk']
            )
        else:
            post['location_simple'] = ''

        post['taken_at_simple'] = datetime.datetime.fromtimestamp(post['taken_at']).strftime('%Y-%m-%dT%H:%M:%SZ')

        def get_best_media(images):
            return sorted(images, key=lambda  x: x['width'], reverse=True)[0]['url']

        if post['media_type'] == 1:
            post['media_simple'] = get_best_media(post['image_versions2']['candidates'])
        elif post['media_type'] == 2:
            post['media_simple'] = get_best_media(post['video_versions'])
        elif post['media_type'] == 8:
            media = []
            for pm in post['carousel_media']:
                if pm['media_type'] == 1:
                    media.append(get_best_media(pm['image_versions2']['candidates']))
                elif pm['media_type'] == 2:
                    media.append(get_best_media(pm['video_versions']))
                else:
                    None
            post['media_simple'] = '\n'.join(media)
        else:
            post['media_simple'] = ''

        if 'caption' in post and post['caption'] != None:
            post['caption_simple'] = post['caption']['text']
        else:
            post['caption_simple'] = ''

        post['url'] = 'https://www.instagram.com/p/%s/'%post['code']

        post['comment_simple'] = []
        post['comment_status'] = 0
        post['comment_count'] = post.get('comment_count', 0)
        # if 'caption_simple' in post:
        #     post['comment_simple'].append({'username':post['user']['username'], 'text': post['caption_simple']})
        # post['comment_simple'].extend(get_media_comments(post['pk']))

        return post

    def get_user_media(self, user_id, max_id = None):
        if not self.api:
            return False, [], max_id
        try:
            items = []
            items_u = set()
            for results, cursor in pagination.page(self.api.user_feed, args={'user_id': user_id}, wait=0, max_id=max_id):
                if results.get('items'):
                    items = [self.prepare_post(p) for p in results['items']]
                items_u = sorted([v for v in {v['pk']:v for v in items}.values()], key=lambda x: x['taken_at'], reverse=True)
                yield True, items_u, cursor
        except Exception as e:
            print(e)
            logging.error(e)
            return False, [], max_id

    def work_progress(self, ok, username, stage, data, cursor):
        if ok:
            self.model.beginResetModel()
            self.model._set(username, stage + '_cursor', cursor)
            self.model._append(username, stage, data)
            self.model.endResetModel()
            # if self.last_select == username:
            #     d = self.model._get(username)
            #     self.posts._set_data(d.get('media', []))
            #     self.following._set_data(d.get('following', []))
            #     self.follower._set_data(d.get('follower', []))
        else:
            self.increase_errors()




    def get_work_data(self, data):
        data.get('setter')(data.get('result'), data.get('args'), data.get('kwargs'))

    def update_list_data(self, id, data, result, get_cursor=lambda r: r.get('next_max_id')):
        self.model.beginResetModel()
        self.model._set(self.model.find_id(id), 'following_cursor', get_cursor(result))
        self.model._append(self.model.find_id(id), 'following', data)
        self.model.endResetModel()

    def following_setter(self, result, args, kwargs):
        data = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in
                   {v['pk']: v for v in result.get('users', [])}.values()]
        if data:
            self.update_list_data(args[0], data, result)

    def follower_setter(self, result, args, kwargs):
        data = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in
                   {v['pk']: v for v in result.get('users', [])}.values()]
        if data:
            self.update_list_data(args[0], data, result)

    def media_setter(self, result, args, kwargs):
        data = [self.prepare_post(p) for p in result.get('items', [])]
        if data:
            self.update_list_data(args[0], data, result)

    def load_user_media(self):
        data = [self.model.data[s] for s in
            [i.row() for i in self.user_list.selectionModel().selectedRows()]
            if self.model.data[s].get('id', None) != None]
        if len(data) == 0:
            return

        self.set_progress_work()
        self.errors = 0
        self.show_errors()
        self.sb_progress.setValue(0)

        tasks = []
        stage_fn = {
            'media': self.api.user_feed,
            'following': self.api.user_following,
            'follower': self.api.user_followers
        }
        for d in data:
            # fn, args, kwargs, setter, getter = self.tasks.get()
            for stage in ['media', 'following', 'follower']:
                if d.get(stage + '_count', 0) > 0 and d.get(stage + '_cursor', None) != '':
                    tasks.append((stage_fn[stage], [d['id']], {'next_max_id': d.get(stage + '_cursor', None)}, getattr(self, stage + '_setter'), pool.getter))

        self.work = pool.Work(self, tasks, 10)
        self.work.finished.connect(self.set_progress_ready)
        self.work.start()


        # self.work = pool.Work()
        # self.btn_stop.clicked.connect(self.work.stop)
        # self.work.task.connect(self.sb_items.setText)
        # self.work.stage.connect(self.sb_stage.setText)
        # self.work.set_max.connect(self.sb_progress.setMaximum)
        # self.work.progress.connect(self.sb_progress.setValue)
        # self.work.error.connect(self.increase_errors)
        # self.work.send_data.connect(self.work_progress)
        # self.work.finished.connect(self.set_progress_ready)
        #
        # self.work.set_data(data, [
        #     {'stage_name': 'Загрузка постов', 'stage': 'media', 'worker': self.get_user_media},
        #     {'stage_name': 'Загрузка подписок', 'stage': 'following', 'worker': self.get_user_following},
        #     {'stage_name': 'Загрузка подписчиков', 'stage': 'follower', 'worker': self.get_user_followers},
        # ])
        #
        # self.work.start()

    def get_media_comments(self, media_id):
        if not self.api:
            return False, [], None
        def prepare_comment(comment):
            comment['username'] = comment['user']['username']
            return comment
        try:
            items = []
            items_u = set()
            for results, cursor in pagination.page(self.api.media_comments, args={'media_id': media_id}, wait=0):
                if results.get('comments'):
                    items.extend([prepare_comment(c) for c in results['comments']])
                items_u = sorted([v for v in {v['pk']: v for v in items}.values()], key=lambda x: x['created_at_utc'], reverse=False)
                yield True, items_u, cursor
        except Exception as e:
            logging.error(e)
            return False, [], None

    def comments_progress(self, ok, username, media_id, result, cursor):
        if ok:
            self.sb_progress.setValue(len(result))
            self.comments.beginResetModel()
            for d in self.model.data:
                if d['username'] == username:
                    for p in d['media']:
                        if str(p['pk']) == media_id:
                            p['comment_simple'] = result
                            p['comment_cursor'] = cursor
                            break
            self.comments.endResetModel()
        else:
            self.increase_errors()

    def load_comments(self):
        data = [self.posts.data[s] for s in [i.row() for i in self.post_list.selectionModel().selectedRows()]]
        if len(data) == 0:
            return

        self.set_progress_work()

        self.errors = 0
        self.show_errors()
        self.sb_progress.setValue(0)

        self.sb_stage.setText('Загрука комментариев')
        self.btn_stop.clicked.connect(self.comments_loader.stop)
        self.comments_loader.task.connect(self.sb_items.setText)
        self.comments_loader.set_max.connect(self.sb_progress.setMaximum)
        self.comments_loader.progress.connect(self.sb_progress.setValue)
        self.comments_loader.error.connect(self.increase_errors)
        self.comments_loader.send_data.connect(self.comments_progress)
        self.comments_loader.finished.connect(self.set_progress_ready)

        self.comments_loader.set_data(self.last_select, data)

        self.comments_loader.start()

    def set_progress_ready(self):
        self.btn_start.setEnabled(True)
        self.btn_prepare.setEnabled(True)
        self.btn_comments.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_filter.setEnabled(True)
        self.btn_filter_settings.setEnabled(True)
        self.sb_progress.setValue(self.sb_progress.maximum())

    def set_progress_work(self):
        self.btn_start.setEnabled(False)
        self.btn_prepare.setEnabled(False)
        self.btn_comments.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_filter.setEnabled(False)
        self.btn_filter_settings.setEnabled(False)

    def set_status(self, status):
        self.sb_connection.setText(status)

    def filter_settings(self):
        info_gm = self.filter_dialog.frameGeometry()
        center = self.frameGeometry().center()
        info_gm.moveCenter(center)
        self.filter_dialog.move(info_gm.topLeft())
        res = self.filter_dialog.exec_()
        if res == 1:
            self.filter(self.btn_filter.isChecked())

    def filter(self, checked):
        for i, d in enumerate(self.model.data):
            self.user_list.setRowHidden(i, False)
        if checked:
            for i, d in enumerate(self.model.data):

                posts_f = True
                posts = self.filter_dialog.e_post.text()
                if posts != '':
                    if 'media_count' in d:
                        posts_f = d['media_count'] > int(posts)
                        if self.filter_dialog.cb_post.currentText() == '<':
                            posts_f = not posts_f

                following_f = True
                following = self.filter_dialog.e_following.text()
                if following != '':
                    if 'following_count' in d:
                        following_f = d['following_count'] > int(following)
                        if self.filter_dialog.cb_following.currentText() == '<':
                            following_f = not following_f

                follower_f = True
                follower = self.filter_dialog.e_follower.text()
                if follower != '':
                    if 'follower_count' in d:
                        follower_f = d['follower_count'] > int(follower)
                        if self.filter_dialog.cb_follower.currentText() == '<':
                            follower_f = not posts_f

                biography_f = True
                biography = self.filter_dialog.e_info.text().lower()
                if biography != '':
                    if 'biography' in d:
                        biography_f = biography in d['biography'].lower()

                if not (posts_f and following_f and follower_f and biography_f):
                    self.user_list.setRowHidden(i, True)
                    continue

    def settings(self):
        info_gm = self.settings_dialog.frameGeometry()
        center = self.frameGeometry().center()
        info_gm.moveCenter(center)
        self.settings_dialog.move(info_gm.topLeft())
        old_username = self.settings_dialog.username.text()
        old_password = self.settings_dialog.password.text()
        res = self.settings_dialog.exec_()
        if res == 1:
            self.settings_login()
            with open(AUTH_FILE_NAME, 'w') as outfile:
                json.dump({'username': self.settings_dialog.username.text(), 'password': self.settings_dialog.password.text()}, outfile, indent=4)
        else:
            self.settings_dialog.username.setText(old_username)
            self.settings_dialog.password.setText(old_password)

    def check_credentials(self, username, password):
        if self.api:
            return self.api.username == username and self.api.password == password
        else:
            return False

    def settings_login(self):
        if not self.connector.isRunning():
            if not self.check_credentials(self.settings_dialog.username.text(), self.settings_dialog.password.text()):
                if os.path.isfile(COOKIE_FILE):
                    os.remove(COOKIE_FILE)
                self.login(self.settings_dialog.username.text(), self.settings_dialog.password.text())

    def login(self, username, password):
        if not self.connector.isRunning():
            if not self.check_credentials(username, password):
                self.connector.username = username
                self.connector.password = password
                self.connector.start()

    def set_api(self):
        self.api = self.connector.api

    def exit(self):
        QtCore.QCoreApplication.instance().quit()

