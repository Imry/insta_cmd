#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging


def get_user_info(self, username):
    if not self.api:
        return {}
    try:
        r = self.api.username_info(username)
        if r['status'] == 'ok':
            return r['user']
    except Exception as e:
        logging.error(e)
        return {}


def load_user_info(self, username):
    # ui = url_parser.get_user_info(username)
    ui = self.get_user_info(username)
    if ui != {}:
        selection = [i.row() for i in self.user_list.selectionModel().selectedRows()]
        self.model.beginResetModel()
        self.model._set2(username, {'id': ui.get('pk', 0),
                                    'img': ui.get('hd_profile_pic_url_info', {}).get('url', ''),
                                    'full_name': ui.get('full_name', ''),
                                    'following_count': ui.get('following_count', ''),
                                    'follower_count': ui.get('follower_count', ''),
                                    'external_url': ui.get('external_url', ''),
                                    'biography': ui.get('biography', ''),
                                    'media_count': ui.get('media_count', '')
                                    })
        self.model.endResetModel()
        for s in selection:
            self.user_list.selectRow(s)
    else:
        self.increase_errors()


def get_user_following(self, user_id, max_id=None):
    if not self.api:
        return False, [], max_id
    try:
        items = []
        items_u = set()
        for results, cursor in pagination.page(self.api.user_following, args={'user_id': user_id}, wait=0,
                                               max_id=max_id):
            if results.get('users'):
                items = results['users']
            items_u = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in
                       {v['pk']: v for v in items}.values()]
            yield True, items_u, cursor
    except Exception as e:
        logging.error(e)
        return False, [], max_id


def get_user_followers(self, user_id, max_id=None):
    if not self.api:
        return False, [], max_id
    try:
        items = []
        items_u = set()
        for results, cursor in pagination.page(self.api.user_followers, args={'user_id': user_id}, wait=0,
                                               max_id=max_id):
            if results.get('users'):
                items = results['users']
            items_u = [{k: v[k] for k in ['full_name', 'username', 'profile_pic_url']} for v in
                       {v['pk']: v for v in items}.values()]
            # yield True, items_u, cursor
            yield True, items, cursor
    except Exception as e:
        logging.error(e)
        return False, [], max_id


def get_user_media(self, user_id, max_id=None):
    def prepare_post(post):
        if 'location' in post and post['location'] != None:
            loc = []
            location = post['location']
            for l in ['name', 'address', 'sity']:
                ll = location.get(l, '')
                if ll != '':
                    loc.append(ll)
            post['location_simple'] = '%s\n%s' % (
                ', '.join(loc),
                'https://www.instagram.com/explore/locations/%s/' % location['pk']
            )
        else:
            post['location_simple'] = ''

        post['taken_at_simple'] = datetime.datetime.fromtimestamp(post['taken_at']).strftime('%Y-%m-%dT%H:%M:%SZ')

        def get_best_media(images):
            return sorted(images, key=lambda x: x['width'], reverse=True)[0]['url']

        if post['media_type'] == 1:
            post['media_simple'] = get_best_media(post['image_versions2']['candidates'])
        elif post['media_type'] == 2:
            post['media_simple'] = get_best_media(post['video_versions'])
        elif post['media_type'] == 8:
            media = []
            for pm in post['carousel_media']:
                if pm['media_type'] == 1:
                    media.append(get_best_media(pm['image_versions2']['candidates']))
                elif pm['media_type'] == 2:
                    media.append(get_best_media(pm['video_versions']))
                else:
                    None
            post['media_simple'] = '\n'.join(media)
        else:
            post['media_simple'] = ''

        if 'caption' in post and post['caption'] != None:
            post['caption_simple'] = post['caption']['text']
        else:
            post['caption_simple'] = ''

        post['url'] = 'https://www.instagram.com/p/%s/' % post['code']

        post['comment_simple'] = []
        post['comment_status'] = 0
        post['comment_count'] = post.get('comment_count', 0)
        # if 'caption_simple' in post:
        #     post['comment_simple'].append({'username':post['user']['username'], 'text': post['caption_simple']})
        # post['comment_simple'].extend(get_media_comments(post['pk']))

        return post

    if not self.api:
        return False, [], max_id
    try:
        items = []
        items_u = set()
        for results, cursor in pagination.page(self.api.user_feed, args={'user_id': user_id}, wait=0, max_id=max_id):
            if results.get('items'):
                items = [prepare_post(p) for p in results['items']]
            items_u = sorted([v for v in {v['pk']: v for v in items}.values()], key=lambda x: x['taken_at'],
                             reverse=True)
            yield True, items_u, cursor
    except Exception as e:
        print(e)
        logging.error(e)
        return False, [], max_id
