#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import datetime

def get_user_info(name):
    if name.startswith('@'): name = name[1:]
    try:
        r = requests.get('https://www.instagram.com/%s/?__a=1'%name)
        if r.status_code == 200:
            data = json.loads(r.text)
            user = data.get('user', {})
            id = user.get('id', '')
            full_name = user.get('full_name', '')
            if full_name is None:
                full_name = ''
            else:
                full_name = full_name.strip()
            return {'username': user.get('username', ''),
                    'img': user.get('profile_pic_url_hd', ''),
                    'name': full_name,
                    'following': user.get('follows', {}).get('count', 0),
                    'followers': user.get('followed_by', {}).get('count', 0),
                    'url': user.get('external_url', ''),
                    'desc': user.get('biography', ''),
                    'media_count': user.get('media', {}).get('count', 0),
                    'id': user.get('id', ''),
                    'media': []
                    }
        # 'media': {'nodes': [], 'has_next_page': user.get('media', {}).get('page_info', {}).get('has_next_page', False),'end_cursor': user.get('media', {}).get('page_info', {}).get('end_cursor', '')}
    except:
        return {}

def get_user_media(name, max_id = ''):
    def get_post(data):
        location = data.get('location', {})
        if location is not None:
            location = location.get('name', '')
        else:
            location = ''

        caption = data.get('caption', {})
        if caption is not None:
            caption = caption.get('text', '')
        else:
            caption = ''

        return {'caption': caption,
                'link': data.get('link', ''),
                'likes': data.get('likes', {}).get('count', 0),
                'time': datetime.datetime.fromtimestamp(float(data.get('created_time', 0))).isoformat(),
                'location': location,
                'comments': '\n'.join(['%s: %s'%(d.get('from',{}).get('full_name',''), d.get('text', '')) for d in data.get('comments', {}).get('data', [])]),
                'media':  data.get('images', {}).get('standard_resolution', {}).get('url', ''),
                'id': data.get('id', '')
                }
    r = requests.get('https://www.instagram.com/%s/media'%name)
    items = []
    if r.status_code == 200:
        data = json.loads(r.text)
        items.extend([get_post(d) for d in data.get('items', [])])
        yield items
        while data.get('more_available', False):
            max_id = items[-1].get('id', '')
            print(max_id)
            r = requests.get('https://www.instagram.com/%s/media?max_id=%s'%(name, max_id))
            if r.status_code == 200:
                data = json.loads(r.text)
                items.extend([get_post(d) for d in data.get('items', [])])
                # items.extend(data.get('items', []))
                yield items
            else:
                break

    return items

if __name__ == '__main__':

    data = get_user_info('shota_rigvava')
    print(data)


    # for i in get_user_media('yana__berezka'):
    #     print(len(i))

    # data = get_user_media('mashatert')
    # print(len(data))
    # print(len(set(data)))

    None