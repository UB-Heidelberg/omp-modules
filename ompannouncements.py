# -*- coding: utf-8 -*-
'''
Created on 11 Jan 2018

@author: wit
'''

import datetime

from gluon import current
from gluon.html import A, DIV, H5, IMG, P, URL, XML
from ompdal import OMPDAL


class Announcements:

    def __init__(self, conf, db, locale):
        self.locale = locale
        self.conf = conf
        self.ompdal = OMPDAL(db, conf)
        self.press_id = int(conf.take('omp.press_id'))
        self.press_settings = self.ompdal.getPressSettings(self.press_id)


    def get_status(self):

        ae = list(filter(lambda e: e['setting_name'] == 'enableAnnouncements', self.press_settings.as_list()))

        if ae:
            return ae[0]['setting_value']
        else:
            return []


    def get_number(self):

        nah = list(filter(lambda e: e['setting_name'] == 'numAnnouncementsHomepage', self.press_settings.as_list()))

        if nah:
            return int(nah[0]['setting_value'])
        else:
            return 6


    def create_announcement_list(self):
        now = datetime.datetime.now()


        def expires(e):
            if e['date_expire']:
                if e['date_expire'] > now:
                    return True
                else:
                    return False
            else:
                return True


        news = self.ompdal.getAnnouncementsByPress(self.press_id).as_list()

        news = list(filter(lambda e: expires(e), news))

        if news:
            nl = list(map(lambda e: self.create_announcement(e), news))

            del nl[self.get_number():]
            return nl
        else:
            return []


    def create_announcement(self, a):

        n = self.ompdal.getAnnouncementSettings(a['announcement_id']).as_list()

        t = list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'title', n))
        title = t[0]['setting_value'] if t else ''

        ds = list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'descriptionShort', n))
        description_short = ds[0]['setting_value'] if ds else ''

        dl = list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'description', n))
        extLink = True if len(dl[0]['setting_value']) > 0 else False

        div = self.announcement_block(description_short, a, title, extLink)
        return div


    def announcement_block(self, description_short, a, title, extLink):

        ann = self.ompdal.getAnnouncementTypeSettings(a['type_id']).as_list()
        t = list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'name', ann))
        ann_type = t[0]['setting_value'] if t else self.conf.take('web.application')
        ann_type = ann_type.replace(' ', '_').lower()
        img_url = URL('static', '{}{}{}'.format('images/press/home/announcements/', ann_type, '.png'))

        div_img = DIV(IMG(_src=img_url, _style="width: 50px;"),
                      _class="media-left pull-left")
        posted__date = a['date_posted'].date()
        div_date = P(posted__date.strftime("%d.%m.%Y "), _class="media-heading")
        div_heading = H5(XML(title))
        link = DIV(A(current.T('more'), _href=URL('aktuelles', 'eintrag', args=[a['announcement_id']]))) if extLink else ''

        div_short_description = DIV(XML(description_short), link, _class="boxText")
        div_body = DIV(div_date, div_heading, div_short_description, _class="media-body")
        div = DIV(div_img, div_body, _class="media")

        return div


if __name__ == '__main__':
    a = Announcements(myconf, db, locale)
    print(a.create_announcement_list())
