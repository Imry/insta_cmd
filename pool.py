#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import queue

from PyQt5.QtCore import QThread, pyqtSignal


def getter(result, kwargs, cursor_key='max_id', get_cursor=lambda r: r.get('next_max_id')):
    cursor = get_cursor(result)
    if cursor:
        kwargs[cursor_key] = cursor
        return True, kwargs
    else:
        return False, None

def setter(data, result):
    None

class Worker(QThread):
    data = pyqtSignal(object)
    error = pyqtSignal()

    def __init__(self, tasks):
        QThread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.need_stop = False

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            try:
                fn, args, kwargs, setter, getter = self.tasks.get(block=False)
                result = fn(*args, **kwargs)
                self.data.emit({'result': result, 'setter': setter, 'fn': fn, 'args': args, 'kwargs': kwargs})
                ok, kwargs = getter(result, kwargs)
                if ok:
                    self.tasks.put({'result': result, 'setter': setter, 'fn': fn, 'args': args, 'kwargs': kwargs})
                if self.need_stop:
                    return
            except queue.Empty as e:
                return
            except Exception as e:
                logging.error(e)
                self.error.emit()

    def stop(self):
        self.need_stop = True

class Work(QThread):
    stop = pyqtSignal()

    def __init__(self, parent, tasks, threads_num):
        QThread.__init__(self)
        self.q = queue.Queue()
        for t in tasks:
            self.q.put(t)
        self.parent = parent
        self.threads_num = threads_num

    def __del__(self):
        self.wait()

    def run(self):
        threads = []
        for t in range(self.threads_num):
            t = Worker(self.q)
            t.data.connect(self.parent.get_work_data)
            t.error.connect(self.parent.increase_errors)
            self.parent.btn_stop.clicked.connect(t.stop)
            t.start()
            threads.append(t)
        for t in threads:
            t.wait()

# class Worker(QThread):
#     send_data = pyqtSignal(bool, str, str, list, str)
#     error = pyqtSignal()
#
#     def __init__(self):
#         QThread.__init__(self)
#         self.data = None
#         self.is_running = False
#         self.worker = None
#
#     def __del__(self):
#         self.wait()
#
#     def run(self):
#         if not self.data:
#             return
#         self.is_running = True
#         w = self.worker
#         d = self.data
#         worker = w['worker']
#         max_id = d.get(w['stage'] + '_cursor', None)
#         if max_id == '':
#             return
#         for ok, result, cursor in worker(d['id'], max_id=max_id):
#             if not ok:
#                 self.error.emit()
#                 break
#             self.send_data.emit(ok, d['username'], w['stage'], result, str(cursor) if cursor != None else cursor)
#             if not self.is_running:
#                 return
#
#     def stop(self):
#         self.is_running = False
#
#     def set_data(self, data, worker):
#         self.data = data
#         self.worker = worker
#
# class Work(QThread):
#     task = pyqtSignal(str)
#     stage = pyqtSignal(str)
#     set_max = pyqtSignal(int)
#     progress = pyqtSignal(int)
#     send_data = pyqtSignal(bool, str, str, list, str)
#     error = pyqtSignal()
#
#     def __init__(self):
#         QThread.__init__(self)
#         self.data = []
#         self.is_running = False
#         self.workers = []
#         self.max = {}
#         self.prog = {}
#         self.threads = []
#
#     def __del__(self):
#         self.wait()
#
#     def run(self):
#         if len(self.data) == 0:
#             return
#         self.is_running = True
#         for idx, d in enumerate(self.data):
#             if not self.is_running:
#                 return
#             self.task.emit('%s / %s'%(idx + 1, len(self.data)))
#             self.stage.emit(d['username'])
#             self.progress.emit(0)
#             for w in self.workers:
#                 mx = d[w['stage'] + '_count']
#                 self.max[w['stage']] = mx
#                 self.prog[w['stage']] = len(d.get(w['stage'], []))
#                 worker = w['worker']
#                 ttt = Worker()
#                 ttt.set_data(d, w)
#                 ttt.error.connect(self.send_error)
#                 ttt.send_data.connect(self.get_data)
#                 ttt.start()
#                 self.threads.append(ttt)
#
#             self.set_max.emit(sum([v for v in self.max.values()]))
#             self.progress.emit(sum([v for v in self.prog.values()]))
#
#             for t in self.threads:
#                 t.wait()
#
#     def send_error(self):
#         self.error.emit()
#
#     def stop(self):
#         self.is_running = False
#         for t in self.threads:
#             t.stop()
#
#     def set_data(self, data, workers):
#         self.data = data
#         self.workers = workers
#
#     def get_data(self, ok, user, stage, result, cursor):
#         self.prog[stage] += len(result)
#         self.progress.emit(sum([v for v in self.prog.values()]))
#         self.send_data.emit(ok, user, stage, result, str(cursor) if cursor != None else cursor)
#
#     def set_progress(self, v, worker):
#         self.prog[worker] += v
#         self.progress.emit(sum([v for v in self.prog.values()]))


class Parser(QThread):
    progress = pyqtSignal(int)

    def __init__(self, worker):
        QThread.__init__(self)
        self.worker = worker
        self.data = []

    def __del__(self):
        self.wait()

    def run(self):
        self.is_running = True
        for i, d in enumerate(self.data):
            if not self.is_running:
                return
            self.worker(d)
            self.progress.emit(i + 1)

    def stop(self):
        self.is_running = False

    def set_data(self, data):
        self.data = data

    def set_worker(self, worker):
        self.worker = worker


class CommentsLoader(QThread):
    task = pyqtSignal(str)
    set_max = pyqtSignal(int)
    progress = pyqtSignal(int)
    send_data = pyqtSignal(bool, str, str, list, str)
    error = pyqtSignal()

    def __init__(self, worker):
        QThread.__init__(self)
        self.data = []
        self.is_running = False
        self.worker = worker
        self.username = None

    def __del__(self):
        self.wait()

    def run(self):
        if self.username is None:
            return
        if len(self.data) == 0:
            return
        self.is_running = True
        for idx, d in enumerate(self.data):
            self.task.emit('%s / %s'%(idx + 1, len(self.data)))
            self.set_max.emit(d['comment_count'])
            self.progress.emit(0)

            for ok, result, cursor in self.worker(d['pk']):
                if not self.is_running:
                    return
                self.progress.emit(len(result))
                self.send_data.emit(ok, self.username, str(d['pk']), result, str(cursor) if cursor != None else cursor)
                if not ok:
                    self.error.emit()
                    break

    def stop(self):
        self.is_running = False

    def set_data(self, username, data):
        self.username = username
        self.data = data
