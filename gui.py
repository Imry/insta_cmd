#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import logging
import os
import pickle
import webbrowser

from PyQt5 import QtWidgets, QtCore
from PyQt5.Qt import QIntValidator
from PyQt5.QtWidgets import QHeaderView

import api
import excel
import model
import pagination
import parse
import pool
import settings
import ui_filter
import ui_main


COOKIE_FILE = 'cookie.json'
CONFIG = 'config.json'


class Filter(QtWidgets.QDialog, ui_filter.Ui_Dialog):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.e_post.setValidator(QIntValidator(0, 99999, self))

class Main(QtWidgets.QMainWindow, ui_main.Ui_MainWindow):
    def __init__(self):
        super(self.__class__, self).__init__()
        self.setupUi(self)

        self.api = None
        self.connector = api.Connector(COOKIE_FILE)
        self.settings_dialog = settings.Settings(CONFIG)

        self.filter_dialog = Filter()

        self.model = model.DataModel(self.user_list)
        self.user_list.setModel(self.model)
        for i, h in enumerate(self.model.headers):
            if h[2] is not None:
                self.user_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.user_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.posts = model.PostModel()
        self.post_list.setModel(self.posts)
        for i, h in enumerate(self.posts.headers):
            if h[2] is not None:
                self.post_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.post_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # self.post_list.horizontalHeader().setMaximumSectionSize(2000)
        # self.post_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)

        self.follower = model.UsersModel()
        self.follower_list.setModel(self.follower)
        for i, h in enumerate(self.follower.headers):
            if h[2] is not None:
                self.follower_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.follower_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.following = model.UsersModel()
        self.following_list.setModel(self.following)
        for i, h in enumerate(self.following.headers):
            if h[2] is not None:
                self.following_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.following_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.comments = model.CommentsModel()
        self.comments_list.setModel(self.comments)
        for i, h in enumerate(self.comments.headers):
            if h[2] is not None:
                self.comments_list.horizontalHeader().setSectionResizeMode(i, h[2])
        self.comments_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        self.last_select = ''

        self.work = None
        self.comments_loader = pool.CommentsLoader(worker=self.get_media_comments)

        self.errors = 0
        self.prepare_status_bar()
        self.end_work()
        self._connect_all()

        self.login(self.settings_dialog.username.text(), self.settings_dialog.password.text())

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

        self.action_import.triggered.connect(self.import_users)
        self.action_export.triggered.connect(self.export_users)
        self.action_save.triggered.connect(self.save_project)
        self.action_load.triggered.connect(self.load_project)
        self.action_exit.triggered.connect(self.exit)

        self.action_settngs.triggered.connect(self.settings)

        self.connector.status.connect(self.sb_connection.setText)
        self.settings_dialog.login.clicked.connect(self.settings_login)

        self.btn_prepare.clicked.connect(self.load_users)
        self.btn_comments.clicked.connect(self.load_comments)
        self.user_list.clicked.connect(self.show_posts)
        self.user_list.doubleClicked.connect(self.open_user)
        self.post_list.clicked.connect(self.show_comments)
        self.post_list.doubleClicked.connect(self.open_post)

        self.btn_filter.toggled.connect(self.filter)
        self.btn_filter_settings.clicked.connect(self.filter_settings)

    def save_project(self):
        file = QtWidgets.QFileDialog.getSaveFileName(self, caption='Выберите файл проекта или введите название нового', filter='Project file (*.project)')
        if file:
            if file[0] != '':
                p_name = file[0]
                with open(p_name, 'wb') as p_f:
                    pickle.dump(self.model.data, p_f)

    def load_project(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, caption='Выберите файл проекта', filter='Project file (*.project)')
        if file:
            if file[0] != '':
                p_name = file[0]
                with open(p_name, 'rb') as p_f:
                    self.model.beginResetModel()
                    self.model.data = pickle.load(p_f)
                    self.model.endResetModel()

    def import_users(self):
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
                    data = []
                    for row in names_reader:
                        name = row[0]
                        if name.startswith('@'): name = name[1:]
                        if not is_in_data(name):
                            data.append(name)
                            self.model.beginResetModel()
                            self.model.data.append({'username': name})
                            self.model.endResetModel()

                    if self.settings_dialog.config.get('load', {}).get('load_new_users', False):
                        if not self.api:
                            return

                        self.start_work()
                        tasks = []
                        for d in data:
                            tasks.append((self.api.username_info, [d], {}, self.user_setter, lambda result, args, kwargs: (False, {}, {})))
                        self.work = pool.Work(self, tasks, self.settings_dialog.config.get('load', {}).get('max_threads', 1))
                        self.work.finished.connect(self.end_work)
                        self.btn_stop.clicked.connect(self.work.stop)
                        self.sb_progress.setMaximum(len(data))
                        self.sb_stage.setText('Предзагрузка пользователей')
                        self.work.start()

    def export_users(self):
        data = [self.model.data[s] for s in [i.row() for i in self.user_list.selectionModel().selectedRows()] if self.model.data[s].get('id', None) != None]
        if len(data) == 0:
            return
        file = str(QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory"))
        for d in data:
            try:
                excel.save_user(d, os.path.join(file, d['username'] + '.xls'))
            except Exception as e:
                logging.error(e)

    def open_user(self, index):
        if not index:
            return
        row = index.row()
        user = self.model.data[row]['username']
        webbrowser.open('www.instagram.com/%s/'%user)

    def open_post(self, index):
        if not index:
            return
        row = index.row()
        user = self.model.data[row]['username']
        webbrowser.open('www.instagram.com/%s/'%user)

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

    def increase_progress(self, value):
        self.sb_progress.setValue(self.sb_progress.value() + value)

    def get_work_data(self, data):
        data.get('setter')(data.get('result'), data.get('args'), data.get('kwargs'))

    def user_setter(self, result, args, kwargs):
        if result.get('ok', False):
            self.increase_errors()
        else:
            user = result.get('user', {})
            if user != {}:
                # selection = [i.row() for i in self.user_list.selectionModel().selectedRows()]
                self.model.beginResetModel()
                self.model._set2(args[0], parse.user(user))
                self.model.endResetModel()
                self.increase_progress(1)
                # for s in selection:
                #     self.user_list.selectRow(s)

    def update_list_data(self, stage, id, data, result):
        self.model.beginResetModel()
        self.model._set(self.model.find_id(id), stage + '_cursor', result.get('next_max_id', ''))
        self.model._append(self.model.find_id(id), stage, data)
        self.model.endResetModel()
        self.increase_progress(len(data))

    def following_setter(self, result, args, kwargs):
        data = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in
                {v['pk']: v for v in result.get('users', [])}.values()]
        if data:
            self.update_list_data('following', args[0], data, result)

    def follower_setter(self, result, args, kwargs):
        data = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in
                {v['pk']: v for v in result.get('users', [])}.values()]
        if data:
            self.update_list_data('follower', args[0], data, result)

    def media_setter(self, result, args, kwargs):
        data = [parse.post(p) for p in result.get('items', [])]
        if data:
            self.update_list_data('media', args[0], data, result)


    def load_users(self):
        if not self.api:
            return
        data = [self.model.data[s] for s in
                [i.row() for i in self.user_list.selectionModel().selectedRows()]
                if self.model.data[s].get('id', None) is not None]
        if len(data) == 0:
            return

        self.start_work()

        tasks = []
        stage_fn = {
            'media': self.api.user_feed,
            'following': self.api.user_following,
            'follower': self.api.user_followers
        }
        max = 0
        for d in data:
            # fn, args, kwargs, setter, getter = self.tasks.get()
            for stage in ['media', 'following', 'follower']:
                if d.get(stage + '_count', 0) > 0 and d.get(stage + '_cursor', None) != '':
                    tasks.append((stage_fn[stage], [d['id']], {'max_id': d.get(stage + '_cursor', '')}, getattr(self, stage + '_setter'), pool.getter))
                    max += d.get(stage + '_count', 0)

        self.work = pool.Work(self, tasks, self.settings_dialog.config.get('load', {}).get('max_threads', 1))
        self.work.finished.connect(self.end_work)
        self.btn_stop.clicked.connect(self.work.stop)
        self.sb_progress.setMaximum(max)
        self.sb_stage.setText('Парсинг пользователей')
        self.work.start()

    def comment_setter(self, result, args, kwargs):
        def prepare_comment(comment):
            comment['username'] = comment['user']['username']
            return comment
        data = [prepare_comment(c) for c in result.get('comments', [])]
        ttt = [v for v in {v['pk']: v for v in data}.values()]
        cursor = result.get('next_max_id', '')
        if data:
            self.comments.beginResetModel()
            # for d in self.model.data:
            #     if d['username'] == username:
            #         for p in d['media']:
            #             if str(p['pk']) == media_id:
            #                 p['comment_simple'] = result
            #                 p['comment_cursor'] = cursor
            #                 break
            self.comments.endResetModel()

    def load_comments(self):
        if not self.api:
            return
        data = [self.posts.data[s] for s in [i.row() for i in self.post_list.selectionModel().selectedRows()]]
        if len(data) == 0:
            return
        self.start_work()

        tasks = []
        max = 0
        for d in data:
            # fn, args, kwargs, setter, getter = self.tasks.get()
            if d.get('comments_count', 0) > 0 and d.get(stage + 'comments_cursor', None) != '':
                tasks.append((stage_fn[stage], [d['id']], {'max_id': d.get(stage + '_cursor', '')}, getattr(self, stage + '_setter'), pool.getter))
                max += d.get(stage + '_count', 0)

        self.work = pool.Work(self, tasks, self.settings_dialog.config.get('load', {}).get('max_threads', 1))
        self.work.finished.connect(self.end_work)
        self.btn_stop.clicked.connect(self.work.stop)
        self.sb_progress.setMaximum(max)
        self.sb_stage.setText('Загруза коментариев')
        self.work.start()


    # def get_media_comments(self, media_id):
    #     if not self.api:
    #         return False, [], None
    #     def prepare_comment(comment):
    #         comment['username'] = comment['user']['username']
    #         return comment
    #     try:
    #         items = []
    #         items_u = set()
    #         for results, cursor in pagination.page(self.api.media_comments, args={'media_id': media_id}, wait=0):
    #             if results.get('comments'):
    #                 items.extend([prepare_comment(c) for c in results['comments']])
    #             items_u = sorted([v for v in {v['pk']: v for v in items}.values()], key=lambda x: x['created_at_utc'], reverse=False)
    #             yield True, items_u, cursor
    #     except Exception as e:
    #         logging.error(e)
    #         return False, [], None


    def start_work(self):
        self.errors = 0
        self.show_errors()
        self.sb_progress.setValue(0)
        self.btn_stop.setEnabled(True)

        self.btn_prepare.setEnabled(False)
        self.btn_comments.setEnabled(False)
        self.btn_filter.setEnabled(False)
        self.btn_filter_settings.setEnabled(False)

    def end_work(self):
        self.sb_progress.setValue(self.sb_progress.maximum())
        self.btn_stop.setEnabled(False)

        self.btn_prepare.setEnabled(True)
        self.btn_comments.setEnabled(True)
        self.btn_filter.setEnabled(True)
        self.btn_filter_settings.setEnabled(True)

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

        old_config = self.settings_dialog.config.copy()
        res = self.settings_dialog.exec_()
        if res == 1:
            self.settings_login()
            self.settings_dialog.save()
        else:
            self.settings_dialog.config = old_config.copy()
            self.settings_dialog.from_config()

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
