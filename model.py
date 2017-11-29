#!/usr/bin/env python
# -*- coding: utf-8 -*-


class List:
    def __init__(self, count=None):
        self.count = count
        self.data = []
        self.cursor = None

class User:
    def __init__(self, id=None, username=None):
        self.id = id
        self.username = username
        self.name = None
        self.bio = None
        self.url = None
        self.img = None
        self.media = List()
        self.follower = List()
        self.following = List()

class Location:
    def __init__(self):
        self.short_name = None
        self.name = None
        self.address = None
        self.city = None
        self.id = None
        self.url = None

class Media:
    def __init__(self):
        self.id = None
        self.height = None
        self.width = None
        self.url = None
        self.data = []

class Post:
    def __init__(self):
        self.id = None
        self.url = None
        self.time = None
        self.time_str = None
        self.likes = None
        self.comment = List()
        self.text = None
        self.media = []
        self.location = Location()
