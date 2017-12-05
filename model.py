#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from PyQt5.Qt import Qt
from PyQt5.QtWidgets import QHeaderView


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

    def find_id(self, id):
        for d in self.data:
            if d['id'] == id:
                return d['username']

    def _get(self, username):
        for d in self.data:
            if d['username'] == username:
                return d
        return None

    def _set(self, username, key, value):
        # if username[0] != '@': username = '@' + username
        for d in self.data:
            if d['username'] == username:
                d[key] = value
                break

    def _set2(self, username, key_value):
        # if username[0] != '@': username = '@' + username
        for d in self.data:
            if d['username'] == username:
                for k, v in key_value.items():
                    d[k] = v
                return

    def _append(self, username, key, value):
        # if username[0] != '@': username = '@' + username
        for d in self.data:
            if d['username'] == username:
                if key not in d:
                    d[key] = value
                else:
                    d[key].extend(value)
                break

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
