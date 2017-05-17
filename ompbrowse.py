# -*- coding: utf-8 -*-
'''
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
'''
from gluon.html import *
from gluon import current
from datetime import datetime


class Browser:

    def __init__(self, s, current, locale, p, sort_by, f):
        self.current = current

        self.filters = dict(x.split('=') for x in f.split(',')) if len(f) > 0 else {}

        self.per_page = p
        self.locale = locale
        self.sort_by = sort_by
        self.submission_sort = {
            'category': (lambda s: s.associated_items.get('category').settings.getLocalizedValue('title', self.locale) if s.associated_items.get('category') else False),
            'oldest_to_newest': (lambda s: min(s.associated_items.get('publication_dates', [datetime(1, 1, 1)]))),
            'newest_to_oldest': (lambda s: min(s.associated_items.get('publication_dates', [datetime(1, 1, 1)]))),
            'title': (lambda s: s.settings.getLocalizedValue('title', self.locale).lower()),
        }

        self.categories = set(x.associated_items.get('category').settings.getLocalizedValue(
            'title', self.locale) for x in s if x.associated_items.get('category'))
        self.submissions = self.filter_submissions(s) if self.filters else s

        self.t = len(self.submissions)
        self.total = self.t / p + 1 if self.t % p > 0 else self.t / p
        self.navigation_select = self.get_navigation_select() if self.total> 20 else DIV()
        self.navigation_list = self.get_navigation_list() if self.total> 20 else DIV()
        self.sort_select = self.get_sort_select()
        self.filter_select = self.get_filter_select()

    def filter_submissions(self, s):
        def category(s, v):
            return str(s.associated_items.get('category').settings.getLocalizedValue('title', self.locale)) == str(
                v) if s.associated_items.get('category') else False

        s = filter(lambda s: category(s, self.filters.get('category')), s)

        # submissions = filter(lambda s:   datetime.strptime(str(y),'%Y') <  min(s.associated_items.get('publication_dates',
        # [datetime(1, 1, 1)])) <  datetime.strptime(str(y+1),'%Y') , submissions)
        return s

    def get_navigation_list(self):
        li = []
        al = {'_aria-label': "Page navigation"}
        for i in range(0, self.total):
            l = A(i + 1, _href=URL('index?page_nr=' + str(i + 1)))
            li.append(LI(l, _class="active")) if i == self.current else li.append(LI(l))

        return TAG.nav(UL(li, _class="pagination pull-left"), **al)

    def get_navigation_select(self):
        per_page = [10, 20, 30]
        li = [LI(A(i, _href=URL('index?per_page=' + str(i)))) for i in per_page]
        ul = UL(li, _class="dropdown-menu")
        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("Results per Page"), SPAN(_class='caret'), **button_cs)
        return DIV(button, ul, _class="btn-group pull-left")

    def get_sort_select(self, ul_class="btn-group pull-right"):
        li = [LI(A(current.T(i).capitalize(), _href=URL('index?sort_by=' + str(i)))) for i in sorted(self.submission_sort.keys())]
        ul = UL(li, _class="dropdown-menu")
        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("sort by"), SPAN(_class='caret'), **button_cs)
        return DIV(button, ul, _class=ul_class)

    def process_submissions(self, s):
        reverse = True if 'newest_to_oldest' in self.sort_by else False
        s = sorted(s, key=self.submission_sort.get(self.sort_by), reverse=reverse)
        s = s[self.current * self.per_page:(self.current + 1) * self.per_page]
        return s

    def get_filter_select(self, ul_class="btn-group pull-right"):

        o = [LI(A(current.T('All'), _href=URL('index?filter_by=[]')))]
        opt = [LI(A(s, _href=URL('index?filter_by=[category=' + str(s) + ']'))) for s in self.categories]
        o = o + opt

        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("Categories"), SPAN(_class='caret'), **button_cs)
        u = UL(o,  _class="dropdown-menu")
        return DIV(button, u,  _class=ul_class)
