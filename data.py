#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple


# List = namedtuple('List', ['size', 'data', 'cursor'])

class List:
    def __init__(self, count=None):
        self.count = count
        self.data = []
        self.cursor = None

class User:
    def __init__(self, username=None, id=None):
        self.username = username
        self.id = id
        self.private = None
        self.name = None
        self.bio = None
        self.url = None
        self.img = None
        self.media = List()
        self.followers = List()
        self.following = List()

# class Location:
#     def __init__(self):
#         self.id = None
#         self.url = None
#         self.short_name = None
#         self.name = None
#         self.address = None
#         self.city = None

# class Media:
#     def __init__(self):
#         self.id = None
#         self.height = None
#         self.width = None
#         self.url = None

class Post:
    def __init__(self):
        self.id = None
        self.code = None
        self.url = None
        self.time = None
        self.time_str = None
        self.likes = None
        self.comment = List()
        self.comment_str = None
        self.text = None
        self.media = []
        self.media_str = None
        # self.location = Location()
        self.location_str = None
