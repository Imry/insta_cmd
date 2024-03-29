#!/usr/bin/env python
# -*- coding: utf-8 -*-


import codecs
import json
import logging
import os

from instagram_private_api import (
    Client, ClientError, ClientLoginError,
    ClientCookieExpiredError, ClientLoginRequiredError,
    __version__ as client_version)


def connect(username, password, cookie_file):
    def to_json(python_object):
        if isinstance(python_object, bytes):
            return {'__class__': 'bytes',
                    '__value__': codecs.encode(python_object, 'base64').decode()}
        raise TypeError(repr(python_object) + ' is not JSON serializable')

    def from_json(json_object):
        if '__class__' in json_object and json_object['__class__'] == 'bytes':
            return codecs.decode(json_object['__value__'].encode(), 'base64')
        return json_object

    def onlogin_callback(api, new_settings_file):
        cache_settings = api.settings
        with open(new_settings_file, 'w') as outfile:
            json.dump(cache_settings, outfile, default=to_json, indent=4)
            logging.info('SAVED: {0!s}'.format(new_settings_file))
            print('SAVED: {0!s}'.format(new_settings_file))

    device_id = None
    try:
        if not os.path.isfile(cookie_file):
            # settings file does not exist
            logging.info('Unable to find file: {0!s}'.format(cookie_file))
            print('Unable to find file: {0!s}'.format(cookie_file))
            # login new
            api = Client(username, password, on_login=lambda x: onlogin_callback(x, cookie_file))
            return api
        else:
            with open(cookie_file) as file_data:
                cached_settings = json.load(file_data, object_hook=from_json)
            logging.info('Reusing settings: {0!s}'.format(cookie_file))
            print('Reusing settings: {0!s}'.format(cookie_file))
            device_id = cached_settings.get('device_id')
            # reuse auth settings
            api = Client(username, password, settings=cached_settings)
            return api
    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        logging.error('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))
        print('ClientCookieExpiredError/ClientLoginRequiredError: {0!s}'.format(e))
        # Login expired
        # Do relogin but use default ua, keys and such
        try:
            api = Client(username, password, device_id=device_id, on_login=lambda x: onlogin_callback(x, cookie_file))
            return api
        except Exception as e:
            logging.error('Unexpected Exception: {0!s}'.format(e))
            print('Unexpected Exception: {0!s}'.format(e))
            return None
    except ClientLoginError as e:
        logging.error('ClientLoginError {0!s}'.format(e))
        print('ClientLoginError {0!s}'.format(e))
        return None
    except ClientError as e:
        logging.error('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        print('ClientError {0!s} (Code: {1:d}, Response: {2!s})'.format(e.msg, e.code, e.error_response))
        return None
    except Exception as e:
        logging.error('Unexpected Exception: {0!s}'.format(e))
        print('Unexpected Exception: {0!s}'.format(e))
        return None
