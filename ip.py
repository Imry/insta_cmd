#!/usr/bin/env python
# -*- coding: utf-8 -*-


import argparse
import csv
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

# import excel_t
import excel_t_xlsx
import parse_t
from api_t import connect
from data import User
from g import *

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(process)-16s %(filename)-16s %(funcName)-16s:%(lineno)-4s %(levelname)-8s: \
                    %(message)s',
                    handlers=[logging.FileHandler(os.path.join(os.path.dirname(__file__), __file__ + '.log'),
                                                  'a+',
                                                  'utf-8')])
logging.info('==================================================')


def my_excepthook(t, value, tback):
    # log the exception here
    logging.error("Uncaught exception", exc_info=(t, value, tback))
    # then call the default handler
    sys.__excepthook__(t, value, tback)


sys.excepthook = my_excepthook


def plog(log_f, msg):
    log_f(msg)
    print(msg)

def plog_i(msg):
    plog(logging.info, msg)


def state_save(state_fn, data):
    plog_i('Save state: %s' % state_fn)
    with open(state_fn, 'wb') as p_f:
        pickle.dump(data, p_f)
    plog_i('Save state: %s. Done' % state_fn)


def state_load(state_fn):
    plog_i('Load state: %s' % state_fn)
    with open(state_fn, 'rb') as p_f:
        data = pickle.load(p_f)
        plog_i('Load state: %s. Done' % state_fn)
        return data


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
    r[OPT_POST_COUNT] = OPT_POST_COUNT_DEFAULT
    r[OPT_POST_UNTIL_DATE] = OPT_POST_UNTIL_DATE_DEFAULT
    for o in opt:
        if o.startswith(OPT_POST_COUNT):
            oo = o.split('=')
            if len(oo) == 2:
                r[OPT_POST_COUNT] = int(oo[1])
        elif o.startswith(OPT_POST_UNTIL_DATE):
            oo = o.split('=')
            if len(oo) == 2:
                oo = oo[1].split('-')
                if len(oo) == 3:
                    r[OPT_POST_UNTIL_DATE] = datetime.datetime(int(oo[0]), int(oo[1]), int(oo[2]))
        else:
            r[o] = None
    return r


def api_call(api_f, kwargs):
    delay = REQUEST_WAIT
    while delay < REQUEST_WAIT_MAX:
        time.sleep(REQUEST_WAIT)
        try:
            result = api_f(**kwargs)
            return True, result
        except KeyboardInterrupt:
            raise
        except ClientError:
            delay = min(2.0 * delay, REQUEST_WAIT_MAX)
            logging.warning('Expected error. Delay = %s' % delay)
    return False, None


def get_info(api, username):
    ok, result = api_call(api.username_info, {'user_name': username})
    if ok:
        if result != {}:
            plog_i('Get info: %s. Done' % username)
            return True, parse_t.user(result.get('user', {}))
        else:
            plog_i('Get info: %s. Empty' % username)
            return False, None
    else:
        plog_i('Get info: %s. Error' % username)
        return False, None



def stdout_p(msg):
    sys.stdout.write(msg)
    sys.stdout.flush()


def get_list(message,
             api_f,
             args,
             lst,
             is_continue,
             items_key,
             parse):
    try:
        if not lst.data:
            logging.info(message)
            ok, results = api_call(api_f, args)
            if ok:
                lst.data.extend([parse(r) for r in results.get(items_key, [])])
                lst.cursor = results.get('next_max_id')
                sys.stdout.write('%s %s/%s' % (message, len(lst.data), lst.count))
                sys.stdout.flush()

            else:
                sys.stdout.write('%s %s/%s Error\n' % (message, len(lst.data), lst.count))
                sys.stdout.flush()
                return False, lst
        while DEBUG_DOWNLOAD_ALL and lst.cursor:
            if not is_continue(lst.data):
                lst.cursor = None
                break
            time.sleep(REQUEST_WAIT)
            args['max_id'] = lst.cursor
            ok, results = api_call(api_f, args)
            if ok:
                lst.data.extend([parse(r) for r in results.get(items_key, [])])
                lst.cursor = results.get('next_max_id')
                sys.stdout.write('\r%s %s/%s' % (message, len(lst.data), lst.count))
                sys.stdout.flush()
            else:
                sys.stdout.write('\r%s %s/%s Error\n' % (message, len(lst.data), lst.count))
                sys.stdout.flush()
                return False, lst
        sys.stdout.write('\r%s %s/%s Done\n' % (message, len(lst.data), lst.count))
        sys.stdout.flush()
        return True, lst

    except Exception:
        logging.error('Unexpected error')
        logging.error(traceback.format_exc())
        return False, lst


def get_url(u, dn):
    # avatar
    img = {os.path.join(dn, u.username, u.img.split('/')[-1]): u.img}
    # feed
    for p in u.media.data:
        if not os.path.exists(os.path.join(dn, u.username, p.code)):
            pp = p.media_str.split('\n')
            for j, ppp in enumerate(pp):
                ext = ppp.split('?')[0].rsplit('.', 1)[1]
                img[os.path.join(dn, u.username, p.code, str(j) + '.' + ext)] = ppp
    return img


def create_dirs(u, dn):
    for p in u.media.data:
        if not os.path.exists(os.path.join(dn, u.username, p.code)):
            os.makedirs(os.path.join(dn, u.username, p.code))


class NeedRepeatException(Exception):
    pass


def main(fn):
    fnd = os.path.dirname(fn)
    try:
        users, login, pwd, opt = load_csv(fn)
        opt = parse_opt(opt)
        logging.info('Parsed options: %s' % opt)
        api = connect(login, pwd, '%s.cookie' % login)
        if api is None:
            logging.error('Login error')
            print('Login error')
            return
    except Exception:
        logging.error('Unexpected error')
        logging.error(traceback.format_exc())
        return

    ok = True
    for i, u in enumerate(users, 1):
        plog_i('%s / %s %s' % (i, len(users), u))

        repeat = 0
        is_repeat = True
        DATA = User()
        while is_repeat and repeat < REPEAT_COUNT:
            is_repeat = False
            repeat += 1

            try:
                # get users info
                state_fn = os.path.join(fnd, u + '.' + STATE_EXT)
                if OPT_LOAD_STATE in opt and os.path.exists(state_fn):
                    plog_i('Load from state')
                    DATA = state_load(state_fn)
                    plog_i('Done')
                else:
                    ok, data = get_info(api, u)
                    if ok:
                        DATA = data
                    else:
                        is_repeat = True
                        raise NeedRepeatException()

                # feed
                if opt[OPT_POST_COUNT] > 0:
                    if not DATA.media.data or DATA.media.cursor: # Empty or need to redownload
                        ok, data = get_list('Get media',
                                            api.user_feed,
                                            {'user_id': DATA.id},
                                            DATA.media,
                                            lambda d: len(d) < opt[OPT_POST_COUNT] and d[-1].time > opt[OPT_POST_UNTIL_DATE],
                                            'items',
                                            parse_t.post)

                        DATA.media = data

                        if ok:
                            DATA.media.data.sort(key=lambda x: x.time, reverse=True)

                            break_i = None
                            for i, d in enumerate(DATA.media.data):
                                if d.time <= opt[OPT_POST_UNTIL_DATE]:
                                    break_i = i
                                    break
                            if break_i is not None:
                                DATA.media.data = DATA.media.data[:break_i]

                            if len(DATA.media.data) > opt[OPT_POST_COUNT]:
                                DATA.media.data = DATA.media.data[:opt[OPT_POST_COUNT]]
                        else:
                            is_repeat = True

                # followers
                if 'iuloginin' not in opt:
                    if not DATA.followers.data or DATA.followers.cursor:
                        ok, data = get_list('Get followers',
                                            api.user_followers,
                                            {'user_id': DATA.id},
                                            DATA.followers,
                                            lambda _: True,
                                            'users',
                                            parse_t.user_small)
                        DATA.followers = data
                        if ok:
                            DATA.followers.data.sort(key=lambda x: x.id)
                        else:
                            is_repeat = True

                # following
                if 'iuloginout' not in opt:
                    if not DATA.following.data or DATA.following.cursor:
                        ok, data = get_list('Get following',
                                            api.user_following,
                                            {'user_id': DATA.id},
                                            DATA.following,
                                            lambda _: True,
                                            'users',
                                            parse_t.user_small)
                        DATA.following = data
                        if ok:
                            DATA.following.data.sort(key=lambda x: x.id)
                        else:
                            is_repeat = True

                if OPT_SAVE_STATE in opt:
                    state_save(os.path.join(fnd, u + '.' + STATE_EXT), DATA)

                # load images
                if 'foto' not in opt:
                    print('\nLoading photos')
                    try:
                        img = get_url(DATA, fnd)
                        create_dirs(DATA, fnd)

                        def save_img(data):
                            global idx, total
                            p, url = data
                            repeat = 0
                            is_repeat = True
                            while is_repeat and repeat < REPEAT_COUNT:
                                is_repeat = False
                                repeat += 1
                                try:
                                    r = requests.get(url, timeout=60)
                                    with open(p, "wb") as i_f:
                                        i_f.write(r.content)
                                        idx += 1
                                        print('Loaded %s/%s %s' % (idx, total, p))
                                except requests.exceptions.Timeout:
                                    logging.warning('Timeout error. repeat = %s' % repeat)
                                    is_repeat = True
                                except Exception:
                                    logging.error(traceback.format_exc())
                                    is_repeat = True

                        work = [(k, v) for k, v in img.items()]
                        global total
                        total = len(work)
                        pool = Pool(CONCURRENT_DOWNLOADS)
                        _ = pool.map(save_img, work)
                        pool.close()
                        pool.join()
                        print('Loaded')

                    except Exception:
                        logging.error('Unexpected error')
                        logging.error(traceback.format_exc())

                # Save xls
                print('Create report')
                excel_t_xlsx.save(DATA, os.path.join(fnd, u + '.xlsx'))

            except KeyboardInterrupt:
                logging.info('KeyboardInterrupt')
                sys.exit(0)
            except NeedRepeatException:
                logging.info('Need repeat')
                is_repeat = True
            except Exception:
                logging.error('Unexpected error')
                logging.error(traceback.format_exc())
                is_repeat = True

            # check errors
            if is_repeat:
                if OPT_SAVE_STATE in opt:
                    state_save(os.path.join(fnd, u + '.' + STATE_EXT), DATA)
                wait_time = REPEAT_WAIT * repeat
                plog_i('There have been errors, an attempt to download the missed things.')
                plog_i('Attempt: %s / %s. Waiting %s sec.' % (repeat, REPEAT_COUNT, wait_time))
                time.sleep(wait_time)

        if is_repeat:
            ok = False

    if ok and OPT_KEEP_CSV not in opt:
        plog_i('Delete CSV')
        os.remove(fn)
        plog_i('Ok!')
    else:
        plog_i('Keep CSV')

idx = 0
total = 0


if __name__ == '__main__':
    logging.info('Arguments: %s' % sys.argv)
    parser = argparse.ArgumentParser(description='Instagram parser')
    parser.add_argument('csv', help='Input file with data')
    csv_fn = parser.parse_args().csv
    logging.info('CSV: %s' % csv_fn)
    if os.path.isfile(csv_fn):
        try:
            main(csv_fn)
        except Exception:
            logging.error('Unexpected error')
            logging.error(traceback.format_exc())
    else:
        plog_i('File %s not found.' % csv_fn)
