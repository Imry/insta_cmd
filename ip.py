#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import csv
import datetime
import logging
import os
import pickle
import shutil
import sys
import time
import traceback
from multiprocessing.dummy import Pool

import requests
from instagram_private_api import ClientError

import excel_t
import parse_t
from api_t import connect
from data import User
from g import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(process)-16s %(filename)-16s %(funcName)-16s:%(lineno)-4s %(levelname)-8s: %(message)s',
                    handlers=[logging.FileHandler(os.path.join(os.path.dirname(__file__), __file__ + '.log'), 'a+', 'utf-8')])
logging.info('==================================================')


def my_excepthook(type, value, tback):
    # log the exception here
    logging.error("Uncaught exception", exc_info=(type, value, tback))
    # then call the default handler
    sys.__excepthook__(type, value, tback)


sys.excepthook = my_excepthook


def log_p(msg):
    logging.info(msg)
    print(msg)


def state_save(state_fn, data):
    logging.info('Save state: %s' % state_fn)
    print('Save state: %s' % state_fn)
    with open(state_fn, 'wb') as p_f:
        pickle.dump(data, p_f)


def state_load(state_fn):
    with open(state_fn, 'rb') as p_f:
        return pickle.load(p_f)


def load_csv(fn):
    with open(fn, newline='') as csv_fn:
        names_reader = csv.reader(csv_fn, delimiter=';')
        users = []
        opt = []
        login, pwd = None, None
        for col, row in enumerate(names_reader):
            if not row:
                continue
            name = row[0].strip().lower()
            if name != '':
                if name.startswith('@'):
                    name = name[1:]
                users.append(name)
            if col == 0:
                login = row[1].strip()
            if col == 1:
                pwd = row[1].strip()
            if len(row) > 2:
                o = row[2].strip().lower()
                if o != '':
                    opt.append(o)
        logging.info('login: %s' % login)
        logging.info('pwd: %s' % pwd)
        logging.info('users: %s' % '\n'.join([u for u in users]))
        logging.info('opt: %s' % '\n'.join(opt))
        return users, login, pwd, opt


def parse_opt(opt):
    r = dict()
    r['uipost'] = 1e6
    r['ipdate'] = datetime.datetime(1900, 1, 1)
    for o in opt:
        if o.startswith('uipost'):
            oo = o.split('=')
            if len(oo) == 2:
                r['uipost'] = int(oo[1])
        elif o.startswith('ipdate'):
            oo = o.split('=')
            if len(oo) == 2:
                oo = oo[1].split('-')
                if len(oo) == 3:
                    r['ipdate'] = datetime.datetime(int(oo[0]), int(oo[1]), int(oo[2]))
        else:
            r[o] = None
    return r


def get_info(api, username):
    try:
        result = api.username_info(username).get('user', {})
        if result != {}:
            log_p('Get info: %s. Done' % username)
            return True, parse_t.user(result)
        else:
            log_p('Get info: %s. Empty' % username)
            return False, None
    except ClientError:
        log_p('Get info: %s. Error' % username)
        return False, None


def get_list(message,
             api_f,
             args,
             lst,
             is_continue,
             items_key,
             parse):
    try:
        logging.info(message)
        time.sleep(REQUEST_WAIT)
        if not lst.data:
            results = api_f(**args)
            lst.data.extend([parse(r) for r in results.get(items_key, [])])
            lst.cursor = results.get('next_max_id')
            sys.stdout.write('%s %s/%s' % (message, len(lst.data), lst.count))
            sys.stdout.flush()
        while DEBUG_DOWNLOAD_ALL and lst.cursor and is_continue(lst.data):
            time.sleep(REQUEST_WAIT)
            args['max_id'] = lst.cursor
            result = api_f(**args)
            lst.cursor = result.get('next_max_id')
            lst.data.extend([parse(r) for r in result.get(items_key, [])])
            sys.stdout.write('\r%s %s/%s' % (message, len(lst.data), lst.count))
            sys.stdout.flush()
        sys.stdout.write('\r%s %s/%s Done\n' % (message, len(lst.data), lst.count))
        sys.stdout.flush()
        return True, lst.data, None
    except ClientError:
        logging.error((traceback.format_exc()))
        sys.stdout.write('\r%s %s/%s Error\n' % (message, len(lst.data), lst.count))
        sys.stdout.flush()
        return False, lst.data, lst.cursor
    except Exception:
        raise


def get_url(data, dn):
    img = {}
    for u in data:
        # avatar
        img[os.path.join(dn, u.username, 'avatar.jpg')] = u.img
        # feed
        for p in u.media.data:
            pp = p.media_str.split('\n')
            for j, ppp in enumerate(pp):
                ext = ppp.split('?')[0].rsplit('.', 1)[1]
                img[os.path.join(dn, u.username, 'media', p.code, str(j) + '.' + ext)] = ppp
        # followers & following
        for ff in ['followers', 'following']:
            for f in getattr(u, ff).data:
                img[os.path.join(dn, u.username, ff, f.username + '.jpg')] = f.img
    return img


def create_dirs(data, dn):
    for u in DATA:
        if os.path.exists(os.path.join(dn, u.username)):
            shutil.rmtree(os.path.join(dn, u.username))
        for p in u.media.data:
            if not os.path.exists(os.path.join(dn, u.username, 'media', p.code)):
                os.makedirs(os.path.join(dn, u.username, 'media', p.code))
        os.makedirs(os.path.join(dn, u.username, 'followers'))
        os.makedirs(os.path.join(dn, u.username, 'following'))


def main(fn):
    try:
        users, login, pwd, opt = load_csv(fn)
        opt = parse_opt(opt)
        api = connect(login, pwd, '%s.cookie' % login)
        if api is None:
            logging.error('Login error')
            print('Login error')
            return
    except Exception:
        logging.error('Unexpeted error')
        logging.error(traceback.format_exc())
        return

    global DATA
    if 'load' in opt and os.path.exists(fn + '.' + STATE_EXT):
        DATA = state_load(fn + '.' + STATE_EXT)
    else:
        for name in users:
            DATA.append(User(username=name))

    repeat = 0
    is_repeat = True
    while is_repeat and repeat < REPEAT_COUNT:
        is_repeat = False
        repeat += 1

        # get users info
        for i, u in enumerate(DATA):
            if not u.id:
                ok, data = get_info(api, u.username)
                if ok:
                    DATA[i] = data
                else:
                    is_repeat = True

        # per user
        for i, u in enumerate(DATA):
            print('User: %s' % u.username)
            if u.id and not u.private:
                try:
                    # feed
                    if opt['uipost'] > 0:
                        if not u.media.data or u.media.cursor:
                            ok, data, cursor = get_list('Get media',
                                                        api.user_feed,
                                                        {'user_id': u.id},
                                                        u.media,
                                                        lambda d: len(d) < opt['uipost'] and d[-1].time > opt['ipdate'],
                                                        'items',
                                                        parse_t.post)
                            DATA[i].media.data = data
                            if ok:
                                DATA[i].media.data.sort(key=lambda x: x.time, reverse=True)
                            else:
                                DATA[i].media.cursor = cursor
                                is_repeat = True
                except Exception as e:
                    logging.error('Unexpeted error')
                    logging.error(traceback.format_exc())
                    is_repeat = True

                # comments ?

                try:
                    # followers
                    if 'iuloginin' not in opt:
                        if not u.followers.data or u.followers.cursor:
                            ok, data, cursor = get_list('Get followers',
                                                        api.user_followers,
                                                        {'user_id': u.id},
                                                        u.followers,
                                                        lambda _: True,
                                                        'users',
                                                        parse_t.user_small)
                            DATA[i].followers.data = data
                            if ok:
                                DATA[i].followers.data.sort(key=lambda x: x.id)
                            else:
                                DATA[i].followers.cursor = cursor
                                is_repeat = True
                except Exception as e:
                    logging.error('Unexpeted error')
                    logging.error(traceback.format_exc())
                    is_repeat = True

                # following
                try:
                    if 'iuloginout' not in opt:
                        if not u.following.data or u.following.cursor:
                            ok, data, cursor = get_list('Get following',
                                                        api.user_following,
                                                        {'user_id': u.id},
                                                        u.following,
                                                        lambda _: True,
                                                        'users',
                                                        parse_t.user_small)
                            DATA[i].following.data = data
                            if ok:
                                DATA[i].following.data.sort(key=lambda x: x.id)
                            else:
                                DATA[i].following.cursor = cursor
                                is_repeat = True
                except Exception as e:
                    logging.error('Unexpeted error')
                    logging.error(traceback.format_exc())
                    is_repeat = True

        # check errors
        if is_repeat:
            state_save(fn + '.' + STATE_EXT, DATA)
            wait_time = REPEAT_WAIT * repeat
            log_p('There have been errors, an attempt to download the missed things, waiting %s sec.' % wait_time)
            time.sleep(wait_time)

    state_save(fn + '.' + STATE_EXT, DATA)

    # load images
    print('\nLoading photos')
    if 'foto' not in opt:
        try:
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

            def save_img(data):
                global idx, total
                idx += 1
                p, url = data[0], data[1]
                print('Load %s/%s %s' % (idx, total, p))
                # sys.stdout.write('\rLoaded %s/%s' % (idx, total))
                # sys.stdout.flush()
                repeat = 0
                is_repeat = True
                while is_repeat and repeat < REPEAT_COUNT:
                    is_repeat = False
                    repeat += 1
                    try:
                        r = requests.get(url)
                        with open(p, "wb") as i_f:
                            i_f.write(r.content)
                    except Exception as e:
                        logging.error(traceback.format_exc())
                        is_repeat = True

            work = [(k, v) for k, v in img.items()]
            global total
            total = len(work)
            pool = Pool(CONCURENT_DOWNLOADS)
            r = pool.map(save_img, work)
            pool.close()
            pool.join()
            print('Loaded')

        except Exception as e:
            logging.error('Unexpeted error')
            logging.error(traceback.format_exc())

    # Save xls
    try:
        print('Create report')
        excel_t.save(DATA, fn.rsplit('.', 1)[0] + '.xls')

        print('Delete CSV')
        os.remove(fn)

    except Exception as e:
        logging.error('Unexpeted error')
        logging.error(traceback.format_exc())

    print('Ok!')


idx = 0
total = 0


if __name__ == '__main__':
    logging.info('Arguments: %s' % sys.argv)
    parser = argparse.ArgumentParser(description='Instagram parser')
    parser.add_argument('csv', help='Input file with data')
    csv = parser.parse_args().csv
    logging.info('CSV: %s' % csv)
    if os.path.exists(csv):
        try:
            main(csv)
        except Exception:
            logging.error(traceback.format_exc())
            # Logs the error appropriately.
    else:
        log_p('File %s not found.' % csv)
