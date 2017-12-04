#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QThread, pyqtSignal

from queue import Queue
from threading import Thread


def page(fn, args, cursor=None, cursor_key='max_id', get_cursor=lambda r: r.get('next_max_id')):
    if cursor:
        args[cursor_key] = cursor
    results = fn(**args)
    cursor = get_cursor(results)
    return results, cursor

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            self.tasks.task_done()

class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        self.tasks.join()

if __name__ == '__main__':
    from random import randrange
    delays = [randrange(1, 10) for i in range(100)]
    from time import sleep
    def wait_delay(d):
        print('sleeping for (%d)sec' % d)
        sleep(d)
    # 1) Init a Thread pool with the desired number of threads
    pool = ThreadPool(20)
    for i, d in enumerate(delays):
        # print the percentage of tasks placed in the queue
        print('%.2f%c' % ((float(i) / float(len(delays))) * 100.0, '%'))
        # 2) Add the task to the queue
        pool.add_task(wait_delay, d)
    # 3) Wait for completion
    pool.wait_completion()



class Worker(QThread):
    send_data = pyqtSignal(bool, str, str, list, str)
    error = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.data = None
        self.is_running = False
        self.worker = None

    def __del__(self):
        self.wait()

    def run(self):
        if not self.data:
            return
        self.is_running = True
        w = self.worker
        d = self.data
        worker = w['worker']
        max_id = d.get(w['stage'] + '_cursor', None)
        if max_id == '':
            return
        for ok, result, cursor in worker(d['id'], max_id=max_id):
            if not ok:
                self.error.emit()
                break
            self.send_data.emit(ok, d['username'], w['stage'], result, str(cursor) if cursor != None else cursor)
            if not self.is_running:
                return

    def stop(self):
        self.is_running = False

    def set_data(self, data, worker):
        self.data = data
        self.worker = worker

class Work(QThread):
    task = pyqtSignal(str)
    stage = pyqtSignal(str)
    set_max = pyqtSignal(int)
    progress = pyqtSignal(int)
    send_data = pyqtSignal(bool, str, str, list, str)
    error = pyqtSignal()

    def __init__(self):
        QThread.__init__(self)
        self.data = []
        self.is_running = False
        self.workers = []
        self.max = {}
        self.prog = {}
        self.threads = []

    def __del__(self):
        self.wait()

    def run(self):
        if len(self.data) == 0:
            return
        self.is_running = True
        for idx, d in enumerate(self.data):
            if not self.is_running:
                return
            self.task.emit('%s / %s'%(idx + 1, len(self.data)))
            self.stage.emit(d['username'])
            self.progress.emit(0)
            for w in self.workers:
                mx = d[w['stage'] + '_count']
                self.max[w['stage']] = mx
                self.prog[w['stage']] = len(d.get(w['stage'], []))
                worker = w['worker']
                ttt = Worker()
                ttt.set_data(d, w)
                ttt.error.connect(self.send_error)
                ttt.send_data.connect(self.get_data)
                ttt.start()
                self.threads.append(ttt)

            self.set_max.emit(sum([v for v in self.max.values()]))
            self.progress.emit(sum([v for v in self.prog.values()]))

            for t in self.threads:
                t.wait()

    def send_error(self):
        self.error.emit()

    def stop(self):
        self.is_running = False
        for t in self.threads:
            t.stop()

    def set_data(self, data, workers):
        self.data = data
        self.workers = workers

    def get_data(self, ok, user, stage, result, cursor):
        self.prog[stage] += len(result)
        self.progress.emit(sum([v for v in self.prog.values()]))
        self.send_data.emit(ok, user, stage, result, str(cursor) if cursor != None else cursor)

    def set_progress(self, v, worker):
        self.prog[worker] += v
        self.progress.emit(sum([v for v in self.prog.values()]))




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
