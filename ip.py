#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import csv
import datetime
import logging
import os
import pickle
import sys
import traceback
from multiprocessing.dummy import Pool
import shutil


import requests

import data
import excel_t
import parse_t
from api_t import connect

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(filename)-16s %(funcName)-16s:%(lineno)-4s %(levelname)-8s: %(message)s',
                    handlers=[logging.FileHandler(os.path.join(os.path.dirname(__file__), __file__ + '.log'), 'a+', 'utf-8')])
logging.info('==================================================')


def my_excepthook(type, value, tback):
    # log the exception here
    logging.error("Uncaught exception", exc_info=(type, value, tback))
    # then call the default handler
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook


DATA = []
STATE = 'state'


def state_save():
    with open(STATE, 'wb') as p_f:
        pickle.dump(DATA, p_f)


def state_load():
    global DATA
    with open(STATE, 'rb') as p_f:
        DATA = pickle.load(p_f)


def users_import(fn):
    with open(fn, newline='') as csv_fn:
        names_reader = csv.reader(csv_fn, delimiter=';')
        opt = []
        login, pwd = None, None
        for idx, row in enumerate(names_reader):
            if not row:
                continue
            name = row[0].strip()
            if name != '':
                if name.startswith('@'):
                    name = name[1:]
                DATA.append(data.User(username=name))

            if idx == 0:
                login = row[1].strip()
                logging.info('login: %s' % login)

            if idx == 1:
                pwd = row[1].strip()
                logging.info('pwd: %s' % pwd)

            o = row[2].strip()
            if o != '':
                opt.append(o)

        logging.info('users: %s' % '\n'.join([u.username for u in DATA]))
        logging.info('opt: %s' % '\n'.join(opt))
        return login, pwd, opt


def users_export():
    None


def main(fn):
    login, pwd, opt = users_import(fn)
    api = connect(login, pwd, '%s.cookie' % login)
    if api is None:
        return

    # get users info
    for i, u in enumerate(DATA):
        print('Get info: %s' % u.username)
        logging.info('Get info: %s' % u.username)
        result = api.username_info(u.username)
        user = result.get('user', {})
        if user != {}:
            DATA[i] = parse_t.user(user)


    DEBUG_DOWNLOAD_ALL = True


    # get media
    posts_count = 1e6
    posts_date = datetime.datetime(1900, 1, 1)
    for o in opt:
        if o.startswith('UIPost'):
            oo = o.split('=')
            if len(oo) == 2:
                posts_count = int(oo[1])
        if o.startswith('IPDate'):
            oo = o.split('=')
            if len(oo) == 2:
                oo = oo[1].split('-')
                if len(oo) == 3:
                    posts_date = datetime.datetime(int(oo[0]), int(oo[1]), int(oo[2]))

    if posts_count > 0:
        for i, u in enumerate(DATA):
            print('Get media: %s' % u.username)
            logging.info('Get media: %s' % u.username)

            result = api.user_feed(u.id)
            DATA[i].media.data.extend([parse_t.post(r)[0] for r in result.get('items', [])])
            DATA[i].media.cursor = result.get('next_max_id')
            sys.stdout.write('Loaded %s/%s' % (len(DATA[i].media.data), DATA[i].media.count))
            sys.stdout.flush()

            while DEBUG_DOWNLOAD_ALL and DATA[i].media.cursor and len(DATA[i].media.data) < posts_count and DATA[i].media.data[-1].time > posts_date:
                result = api.user_feed(u.id, max_id=DATA[i].media.cursor)
                DATA[i].media.cursor = result.get('next_max_id')
                DATA[i].media.data.extend([parse_t.post(r)[0] for r in result.get('items', [])])
                sys.stdout.write('\rLoaded %s/%s' % (len(DATA[i].media.data), DATA[i].media.count))
                sys.stdout.flush()

            DATA[i].media.data.sort(key=lambda x: x.time, reverse=True)

            # get comments
            # if False: #'IPComments' not in opt:
            #     print('\nGet comments: %s' % u.username)
            #     logging.info('Get comments: %s' % u.username)
            #     for j, p in enumerate(DATA[i].media.data):
            #         result = api.media_comments(p.id)
            #         DATA[i].media.data[j].comments.data.extend([parse_t.post(r)[0] for r in result.get('comments', [])])
            #         DATA[i].media.data[j].comments.cursor = result.get('next_max_id')
            #
            #         while DATA[i].media.cursor and len(DATA[i].media.data) < posts_count and DATA[i].media.data[-1].time > posts_date:
            #             result = api.user_feed(u.id, max_id=DATA[i].media.cursor)
            #             DATA[i].media.cursor = result.get('next_max_id')
            #             DATA[i].media.data.extend([parse_t.post(r)[0] for r in result.get('items', [])])
            #
            #         DATA[i].media.data.sort(key=lambda x: x.time, reverse=True)
            #         sys.stdout.write('\rLoaded %s/%s' % (j, len(DATA[i].media.data)))
            #         sys.stdout.flush()


    def get_users():
        if 'IULoginIn' not in opt:
            for i, u in enumerate(DATA):
                print('\nGet followers: %s' % u.username)
                logging.info('Get followers: %s' % u.username)

                result = api.user_followers(u.id)
                DATA[i].followers.data.extend([parse_t.user_small(r) for r in result.get('users', [])])
                DATA[i].followers.cursor = result.get('next_max_id')
                sys.stdout.write('Loaded %s/%s' % (len(DATA[i].followers.data), DATA[i].followers.count))
                sys.stdout.flush()

                while DEBUG_DOWNLOAD_ALL and DATA[i].followers.cursor:
                    result = api.user_feed(u.id, max_id=DATA[i].followers.cursor)
                    DATA[i].followers.cursor = result.get('next_max_id')
                    DATA[i].followers.data.extend([parse_t.user_small(r) for r in result.get('items', [])])
                    sys.stdout.write('\rLoaded %s/%s' % (len(DATA[i].followers.data), DATA[i].followers.count))
                    sys.stdout.flush()
                    if len(DATA[i].followers.data) >= 1e6:
                        break

                DATA[i].followers.data.sort(key=lambda x: x.id)

    # get followers
    if 'IULoginIn' not in opt:
        for i, u in enumerate(DATA):
            print('\nGet followers: %s' % u.username)
            logging.info('Get followers: %s' % u.username)

            result = api.user_followers(u.id)
            DATA[i].followers.data.extend([parse_t.user_small(r) for r in result.get('users', [])])
            DATA[i].followers.cursor = result.get('next_max_id')
            sys.stdout.write('Loaded %s/%s' % (len(DATA[i].followers.data), DATA[i].followers.count))
            sys.stdout.flush()

            while DEBUG_DOWNLOAD_ALL and DATA[i].followers.cursor:
                result = api.user_followers(u.id, max_id=DATA[i].followers.cursor)
                DATA[i].followers.cursor = result.get('next_max_id')
                DATA[i].followers.data.extend([parse_t.user_small(r) for r in result.get('users', [])])
                sys.stdout.write('\rLoaded %s/%s' % (len(DATA[i].followers.data), DATA[i].followers.count))
                sys.stdout.flush()

            DATA[i].followers.data.sort(key=lambda x: x.id)

    # get following
    if 'IULoginOut' not in opt:
        for i, u in enumerate(DATA):
            print('\nGet following: %s' % u.username)
            logging.info('Get following: %s' % u.username)

            result = api.user_following(u.id)
            DATA[i].following.data.extend([parse_t.user_small(r) for r in result.get('users', [])])
            DATA[i].following.cursor = result.get('next_max_id')
            sys.stdout.write('Loaded %s/%s' % (len(DATA[i].following.data), DATA[i].following.count))
            sys.stdout.flush()

            while DEBUG_DOWNLOAD_ALL and  DATA[i].following.cursor:
                result = api.user_following(u.id, max_id=DATA[i].following.cursor)
                DATA[i].following.cursor = result.get('next_max_id')
                DATA[i].following.data.extend([parse_t.user_small(r) for r in result.get('users', [])])
                sys.stdout.write('\rLoaded %s/%s' % (len(DATA[i].following.data), DATA[i].following.count))
                sys.stdout.flush()

            DATA[i].following.data.sort(key=lambda x: x.id)



    # load images
    if 'Foto' not in opt:
        img = {}
        d = os.path.dirname(fn)
        for u in DATA:
            if os.path.exists(os.path.join(d, u.username)):
                shutil.rmtree(os.path.join(d, u.username))
                # .wait(5)

            img[os.path.join(d, u.username, 'avatar.jpg')] = u.img

            for p in u.media.data:
                pp = p.media_str.split('\n')
                for j, ppp in enumerate(pp):
                    if not os.path.exists(os.path.join(d, u.username, 'media', p.code)):
                        os.makedirs(os.path.join(d, u.username, 'media', p.code))
                    ext = ppp.split('?')[0].rsplit('.', 1)[1]
                    img[os.path.join(d, u.username, 'media', p.code, str(j) + '.' + ext)] = ppp

            os.makedirs(os.path.join(d, u.username, 'followers'))
            for f in u.followers.data:
                img[os.path.join(d, u.username, 'followers', f.username + '.jpg')] = f.img

            os.makedirs(os.path.join(d, u.username, 'following'))
            for f in u.following.data:
                img[os.path.join(d, u.username, 'following', f.username + '.jpg')] = f.img

    print('\nLoading photos')

    def save_img(data):
        global idx, total
        idx += 1
        p, url = data[0], data[1]
        print('Loaded %s/%s %s' % (idx, total, p))
        # sys.stdout.write('\rLoaded %s/%s' % (idx, total))
        # sys.stdout.flush()
        r = requests.get(url)
        with open(p, "wb") as i_f:
            i_f.write(r.content)

    work = [(k, v) for k, v in img.items()]
    global total
    total = len(work)
    pool = Pool(25)
    r = pool.map(save_img, work)
    pool.close()
    pool.join()

    # Save xls
    os.remove(fn)
    excel_t.save(DATA, fn.rsplit('.', 1)[0] + '.xls')

idx = 0
total = 0


if __name__ == '__main__':
    logging.info('Arguments: %s' % sys.argv)
    parser = argparse.ArgumentParser(description='Instagram parser')
    parser.add_argument('csv', help='Input file with data')
    # parser.add_argument('--config', help='Config file')
    args = parser.parse_args()
    logging.info('CSV: %s' % args.csv)
    try:
        main(args.csv)
    except Exception as e:
        logging.error(traceback.format_exc())
        # Logs the error appropriately.
