# -*- coding: utf-8 -*-
'''
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
'''
from gluon.html import *
from gluon import current
from datetime import datetime

class Pagination:

    def __init__(self, current, total):
        self.current = current
        self.total = total

    def get_navigation_result(self):
        li = []
        al = {'_aria-label': "Page navigation"}
        for i in range(0, self.total):
            l = A(i + 1, _href=URL('index?page_nr=' + str(i + 1)))
            li.append(LI(l, _class="active")) if i == self.current else li.append(LI(l))

        return TAG.nav(UL(li, _class="pagination pull-left"), **al)

    def get_navigation_select(self):
        per_page = [2, 3, 4]
        li = [LI(A(i, _href=URL('index?per_page=' + str(i)))) for i in per_page]
        ul = UL(li, _class="dropdown-menu ")
        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("Results per Page"), SPAN(_class='caret'), **button_cs)
        return DIV(button, ul, _class="btn-group pull-right")


class Sort:

    def __init__(self, locale):
        self.locale = locale
        self.submission_sort = {'category': (lambda s: s.associated_items.get('category')),
                                'date': (lambda s: min(s.associated_items.get('publication_dates', [datetime(1, 1, 1)]))),
                                'title': (lambda s: s.settings.getLocalizedValue('title', self.locale).lower()),
                                }

    def sort_submissions(self, submissions, sort_by):
        return sorted(submissions, key=self.submission_sort.get(sort_by), reverse=False)

    def get_sort_select(self):
        li = [LI(A(i.capitalize(), _href=URL('index?sort_by=' + str(i)))) for i in sorted(self.submission_sort.keys())]
        ul = UL(li, _class="dropdown-menu")
        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("sort by"), SPAN(_class='caret'), **button_cs)
        return DIV(button, ul, _class="btn-group pull-right")
