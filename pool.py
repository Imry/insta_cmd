#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import queue

from PyQt5.QtCore import QThread, pyqtSignal


def getter(result, args, kwargs, cursor_key='max_id', get_cursor=lambda r: r.get('next_max_id')):
    cursor = get_cursor(result)
    if cursor:
        kwargs[cursor_key] = cursor
        return True, args, kwargs
    else:
        return False, args, kwargs

class Worker(QThread):
    data = pyqtSignal(object)
    error = pyqtSignal()

    def __init__(self, tasks):
        QThread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.need_stop = False

    # def __del__(self):
    #     self.wait()

    def run(self):
        while True:
            try:
                fn, args, kwargs, setter, getter = self.tasks.get(block=False)
                if self.need_stop:
                    return
                result = fn(*args, **kwargs)
                self.data.emit({'result': result, 'setter': setter, 'args': args, 'kwargs': kwargs})
                ok, args, kwargs = getter(result, args.copy(), kwargs.copy())
                if ok:
                    self.tasks.put((fn, args, kwargs, setter, getter))
            except queue.Empty as e:
                return
            except Exception as e:
                logging.error(e)
                self.error.emit()
                # return

    def stop(self):
        self.need_stop = True

class Work(QThread):
    def __init__(self, parent, tasks, threads_num):
        QThread.__init__(self)
        self.q = queue.Queue()
        for t in tasks:
            self.q.put(t)
        self.parent = parent
        self.threads_num = threads_num

    # def __del__(self):
    #     self.wait()

    def run(self):
        self.threads = []
        for t in range(self.threads_num):
            t = Worker(self.q)
            t.data.connect(self.parent.get_work_data)
            t.error.connect(self.parent.increase_errors)
            t.start()
            self.threads.append(t)
        for t in self.threads:
            t.wait()

    def stop(self):
        for t in self.threads:
            t.stop()

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
