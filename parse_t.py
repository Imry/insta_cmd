#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime


import data


def user(user):
    u = data.User()
    u.username = user.get('username', None)
    u.id = user.get('pk', None)
    u.private = user.get('is_private', False)
    u.name = user.get('full_name', '')
    u.bio = user.get('biography', '')
    u.url = user.get('external_url', '')
    u.img = user.get('hd_profile_pic_url_info', {}).get('url', '')
    u.media = data.List()
    u.media.count = user.get('media_count', None)
    u.followers = data.List()
    u.followers.count = user.get('follower_count', None)
    u.following = data.List()
    u.following.count = user.get('following_count', None)
    return u


def user_small(user):
    u = data.User()
    u.username = user.get('username', 0)
    u.id = user.get('pk', 0)
    u.name = user.get('full_name', '')
    u.img = user.get('profile_pic_url', '')
    return u


def post(post):
    p = data.Post()

    if post.get('location', None) is not None:
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
    p.location_str = post['location_simple']

    post['taken_at_simple'] = datetime.datetime.fromtimestamp(post['taken_at']).strftime('%Y-%m-%dT%H:%M:%SZ')
    p.time = datetime.datetime.fromtimestamp(post['taken_at'])
    p.time_str = post['taken_at_simple']

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
    p.media = post['media_simple']
    p.media_str = post['media_simple']

    if 'caption' in post and post['caption'] is not None:
        post['caption_simple'] = post['caption']['text']
    else:
        post['caption_simple'] = ''
    p.text = post['caption_simple']

    post['url'] = 'https://www.instagram.com/p/%s/' % post['code']
    p.id = post['id']
    p.code = post['code']
    p.url = post['url']

    post['comment_simple'] = []
    post['comment_status'] = 0
    post['comment_count'] = post.get('comment_count', 0)
    if 'caption_simple' in post:
        post['comment_simple'].append({'username': post['user']['username'], 'text': post['caption_simple']})
        p.comment_str = post['caption_simple']
    # post['comment_simple'].extend(get_media_comments(post['pk']))
    p.comment.count = post['comment_count']

    p.likes = post['like_count']

    return p, post
