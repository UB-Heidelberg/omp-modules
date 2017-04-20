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



    def __init__(self, submissions, current, locale, p, sort_by, filters):
        self.current = current
        self.filters = {'category':['Wissenschaft']}
        self.per_page = p
        self.locale = locale
        self.sort_by = sort_by

        def category(s):
            return s.associated_items.get('category').settings.getLocalizedValue('title', self.locale)  if s.associated_items.get('category') else False

        self.submission_sort = {
            'category': (category),
            'date': (lambda s: min(s.associated_items.get('publication_dates', [datetime(1, 1, 1)]))),
            'title': (lambda s: s.settings.getLocalizedValue('title', self.locale).lower()),
        }


        #self.filter_functions = {
        #    'category': (lambda s : cat_filter(s,v))
        #}
        #submissions = filter(lambda s:   datetime.strptime(str(y),'%Y') <  min(s.associated_items.get('publication_dates', [datetime(1, 1, 1)])) <  datetime.strptime(str(y+1),'%Y') , submissions)



        self.total = len(submissions) / p + 1 if len(submissions) % p > 0 else len(submissions) / p
        self.navigation_select = self.get_navigation_select()
        self.navigation_list = self.get_navigation_list()
        self.sort_select = self.get_sort_select()

        self.submissions = submissions

    def get_navigation_list(self):
        li = []
        al = {'_aria-label': "Page navigation"}
        for i in range(0, self.total):
            l = A(i + 1, _href=URL('index?page_nr=' + str(i + 1)))
            li.append(LI(l, _class="active")) if i == self.current else li.append(LI(l))

        return TAG.nav(UL(li, _class="pagination pull-left"), **al)

    def get_navigation_select(self):
        per_page = [2, 3, 4]
        li = [LI(A(i, _href=URL('index?per_page=' + str(i)))) for i in per_page]
        ul = UL(li, _class="dropdown-menu")
        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("Results per Page"), SPAN(_class='caret'), **button_cs)
        return DIV(button, ul, _class="btn-group pull-right")


    def filter_submissions(self, submissions):
        def category(s, v):
            return str(s.associated_items.get('category').settings.getLocalizedValue('title', self.locale)) == str(v) if s.associated_items.get('category') else False
        return filter(lambda s: category(s, 'Wissenschaft'), submissions)


    def process_submissions(self, submissions):
        submissions = sorted(submissions, key=self.submission_sort.get(self.sort_by), reverse=False)
        submissions = submissions[self.current * self.per_page:(self.current + 1) * self.per_page]
        return submissions


    def get_sort_select(self, ul_class="btn-group pull-right"):
        li = [LI(A(i.capitalize(), _href=URL('index?sort_by=' + str(i)))) for i in sorted(self.submission_sort.keys())]
        ul = UL(li, _class="dropdown-menu")
        button_cs = {"_type": "button", "_class": "btn btn-default dropdown-toggle", "_data-toggle": "dropdown",
                     "_aria-haspopup": "true", "_aria-expanded": "false"}
        button = TAG.button(current.T("sort by"), SPAN(_class='caret'), **button_cs)
        return DIV(button, ul, _class=ul_class)
