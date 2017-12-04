#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xlwt

def save_user(data, fname):
    book = xlwt.Workbook(encoding="utf-8")
    sheet1 = book.add_sheet("user_info")
    sheet2 = book.add_sheet("posts")
    style = xlwt.easyxf('font: underline single')

    sheet1.write(0, 0, 'IULogin')
    sheet1.write(1, 0, data['username'])
    sheet1.write(2, 0, xlwt.Formula('HYPERLINK("%s";"%s")' % (
        'http://www.instagram.com/%s/' % data['username'], 'instagram.com/%s/' % data['username'])), style)
    # sheet1.col(0).width = 256 * 50

    sheet1.write(0, 1, 'IUFoto')
    sheet1.write(1, 1, xlwt.Formula('HYPERLINK("file:%s";"%s")' % (data['img'], data['img'])), style)
    # sheet1.col(1).width = 256 * 50

    sheet1.write(0, 2, 'IUName')
    sheet1.write(1, 2, data['full_name'])

    sheet1.write(0, 3, 'IUSite')
    sheet1.write(1, 3, data['external_url'])
    # sheet1.col(3).width = 256 * 50

    sheet1.write(0, 4, 'IUNote')
    sheet1.write(1, 4, data['biography'])
    # sheet1.col(4).width = 256 * 50

    sheet1.write(0, 5, 'IULoginOut')
    sheet1.write(1, 5, data['follower_count'])
    sheet1.write(2, 5, 'IULogin')
    sheet1.write(2, 6, 'IUName')
    sheet1.write(2, 7, 'IUFoto')
    for idx, f in enumerate(data.get('follower', [])):
        sheet1.write(3 + idx, 5, f['username'])
        sheet1.write(3 + idx, 6, f['full_name'])
        sheet1.write(3 + idx, 7,
                     xlwt.Formula('HYPERLINK("%s";"%s")' % (f['profile_pic_url'], f['profile_pic_url'])), style)

    sheet1.write(0, 9, 'IULoginIn')
    sheet1.write(1, 9, data['following_count'])
    sheet1.write(2, 9, 'IULogin')
    sheet1.write(2, 10, 'IUName')
    sheet1.write(2, 11, 'IUFoto')
    for idx, f in enumerate(data.get('following', [])):
        sheet1.write(3 + idx, 9, f['username'])
        sheet1.write(3 + idx, 10, f['full_name'])
        sheet1.write(3 + idx, 11,
                     xlwt.Formula('HYPERLINK("%s";"%s")' % (f['profile_pic_url'], f['profile_pic_url'])), style)

    sheet2.write(0, 0, data['media_count'])
    sheet2.write(1, 0, 'IPUrl')
    sheet2.write(1, 1, 'IPLocation')
    sheet2.write(1, 2, 'IPDate')
    sheet2.write(1, 3, 'IPLike')
    sheet2.write(1, 4, 'IPFoto')
    sheet2.write(1, 5, 'IPComments')

    shift = 2
    for p in data.get('media', []):
        sheet2.write(shift, 0, p['url'])
        l = []
        if 'location_simple' in p:
            l = p['location_simple'].split('\n')
            sheet2.write(shift, 1, l[0])
            sheet2.write(shift + 1, 1, xlwt.Formula('HYPERLINK("%s";"%s")' % (l[1], l[1])), style)
        sheet2.write(shift, 2, p['taken_at_simple'])
        sheet2.write(shift, 3, p['like_count'])
        m = p['media_simple'].split('\n')
        for idx, mm in enumerate(m):
            sheet2.write(shift + idx, 4, xlwt.Formula('HYPERLINK("%s";"%s")' % (mm, mm)), style)
        c = p['comment_simple']
        for idx, cc in enumerate(c):
            sheet2.write(shift + idx, 5, cc['username'])
            sheet2.write(shift + idx, 6, cc['text'])

        shift += max([1, len(l), len(m), len(c)])

    book.save(fname)
