#!/usr/bin/env python
# -*- coding: utf-8 -*-


import logging
import queue
import time
import traceback

from PyQt5.QtCore import QThread, pyqtSignal


def list_getter(result, fn, args, kwargs, setter, getter):
    cursor = result.get('next_max_id')
    if cursor:
        kwargs['max_id'] = cursor
        return [(fn, args, kwargs, setter, getter)]
    else:
        return []


class Worker(QThread):
    data = pyqtSignal(object)
    error = pyqtSignal()

    def __init__(self, tasks):
        QThread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.need_stop = False
        self.dalay = 0
    # def __del__(self):
    #     self.wait()

    def run(self):
        while True:
            try:
                if self.dalay:
                    time.sleep(self.dalay)
                fn, args, kwargs, setter, getter = self.tasks.get(block=False)
                if self.need_stop:
                    return
                result = fn(*args, **kwargs)
                self.data.emit({'result': result, 'setter': setter, 'args': args, 'kwargs': kwargs})
                task = getter(result, fn, args.copy(), kwargs.copy(), setter, getter)
                if task:
                    for t in task:
                        fn, args, kwargs, setter, getter = t
                        self.tasks.put((fn, args, kwargs, setter, getter))
            except queue.Empty as e:
                return
            except Exception as e:
                logging.error(e)
                logging.error(traceback.format_exc())
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
        self.threads = []

    # def __del__(self):
    #     self.wait()

    def run(self):
        for _ in range(self.threads_num):
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
