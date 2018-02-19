#!/usr/bin/env python
# -*- coding: utf-8 -*-

import openpyxl
from openpyxl.styles import NamedStyle, Font, Alignment, colors
from openpyxl.utils.cell import get_column_letter


STYLE_BOLD = NamedStyle(name="bold")
STYLE_BOLD.font = Font(bold=True)
STYLE_WRAP = NamedStyle(name="wrap")
STYLE_WRAP.alignment = Alignment(wrapText=True)
STYLE_LINK = NamedStyle(name="Hyperlink")
STYLE_LINK.font = Font(color=colors.BLUE)
STYLE_LINK.alignment = Alignment(wrapText=True)


def link(url):
    return ['=HYPERLINK("%s", "%s")' % (url, url), STYLE_LINK]


def create_write(sheet, col, row):
    def writer(c, r, data, style=None):
        c = sheet.cell(column=1+row + r, row=1+col + c, value=data)
        if style:
            c.style = style
    return writer


def write_info(sheet, data, col, row):
    writer = create_write(sheet, col, row)

    writer(0, 0, 'IULogin', STYLE_BOLD)
    writer(0, 1, 'IUFoto', STYLE_BOLD)
    writer(0, 2, 'IUName', STYLE_BOLD)
    writer(0, 3, 'IUSite', STYLE_BOLD)
    writer(0, 4, 'IUNote', STYLE_BOLD)

    writer(1, 0, data.username)
    writer(2, 0, *link(data.username))

    writer(1, 1, *link(data.img))

    writer(1, 2, data.name, STYLE_WRAP)

    writer(1, 3, *link(data.url))

    writer(1, 4, data.bio)


def write_user_list(sheet, data, col, row, title, key):
    writer = create_write(sheet, col, row)

    writer(0, 0, title, STYLE_BOLD)
    writer(2, 0, 'IULogin', STYLE_BOLD)
    writer(2, 1, 'IUName', STYLE_BOLD)
    writer(2, 2, 'IUFoto', STYLE_BOLD)

    l = getattr(data, key, None)
    if not l:
        return
    writer(1, 0, l.count)
    for idx, f in enumerate(l.data):
        writer(3 + idx, 0, f.username)
        writer(3 + idx, 1, f.name, STYLE_WRAP)
        writer(3 + idx, 2, *link(f.img))


def write_media(sheet, data, col, row):
    writer = create_write(sheet, col, row)

    writer(0, 0, 'UIPost', STYLE_BOLD)
    writer(0, 1, data.media.count)
    writer(1, 0, 'IPUrl', STYLE_BOLD)
    writer(1, 1, 'IPLocation', STYLE_BOLD)
    writer(1, 2, 'IPDate', STYLE_BOLD)
    writer(1, 3, 'IPLike', STYLE_BOLD)
    writer(1, 4, 'IPFoto', STYLE_BOLD)
    writer(1, 5, 'IPComments', STYLE_BOLD)

    shift = 2
    for p in data.media.data:
        writer(shift, 0, *link(p.url))
        location = p.location_str
        if location != '':
            location = location.split('\n')
            writer(shift, 1, location[0], STYLE_WRAP)
            writer(shift + 1, 1, *link(location[1]))
        writer(shift, 2, p.time_str)
        writer(shift, 3, p.likes)
        m = p.media_str.split('\n')
        for idx, mm in enumerate(m):
            writer(shift + idx, 4, *link(mm))
        writer(shift + idx, 5, p.comment_str, STYLE_WRAP)

        shift += max([1, len(location), len(m)])


def save(data, fname):
    book = openpyxl.Workbook()
    for sheet_idx, d in enumerate(data):
        sheet = book.create_sheet(d.username, sheet_idx)

        for i in range(19):
            i += 1
            if i not in [9, 13, 17]:
                sheet.column_dimensions[get_column_letter(i)].width = 50
        sheet.column_dimensions[get_column_letter(20)].width = 200

        write_info(sheet, d, 0, 0)
        write_user_list(sheet, d, 0, 5, 'IULoginIn',  'following')
        write_user_list(sheet, d, 0, 9, 'IULoginOut', 'followers')
        write_media(sheet, d, 0, 13)

    book.save(fname)
