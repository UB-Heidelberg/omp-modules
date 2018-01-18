# -*- coding: utf-8 -*-
'''
Created on 11 Jan 2018

@author: wit
'''

from ompdal import OMPDAL
from gluon.html import DIV,H5,IMG,P,URL,XML


class Announcements:

    def __init__(self, conf, db, locale):
        self.locale = locale
        self.ompdal = OMPDAL(db, conf)
        self.press_settings = self.ompdal.getPressSettings(conf.take('omp.press_id'))

    def get_status(self):

        ae = list(filter(lambda e: e['setting_name'] == 'enableAnnouncements', self.press_settings.as_list()))

        if ae:
            return ae[0]['setting_value']
        else:
            return []

    def get_number(self):

        nah = list(filter(lambda e: e['setting_name'] == 'numAnnouncementsHomepage', self.press_settings.as_list()))

        if nah:
            return nah[0]['setting_value']
        else:
            return 10

    def get_news(self):


        if self.locale == 'de_DE':
            name = 'Aktuelles'
        elif self.locale == 'en_US':
            name ='news'
        else:
            name = ''

        return self.get_announcements_by_type_name(name)

    def get_announcements_by_type_name(self, name):

        ats = self.ompdal.getAnnouncementTypeSettings().as_list()
        ats_list = list(filter(lambda e: (e['setting_name'] == 'name') and (e['setting_value'] == name), ats))

        if ats_list:
            announcement_type = self.ompdal.getAnnouncementType(ats_list[0]['type_id'])
            if announcement_type:
                return self.ompdal.getAnnouncementsByType(announcement_type)

        else:
            return []

    def create_news_list(self):

        news = self.get_news()
        if news :
            return list(map(lambda e: self.create_news(e), news.as_list()))
        else:
            return []

    def create_news(self, news):

        n = self.ompdal.getAnnouncementSettings(news['announcement_id']).as_list()

        t= list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'title', n))
        title = t[0]['setting_value'] if t else ''

        ds = list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'descriptionShort', n))
        description_short = ds[0]['setting_value'] if ds else ''

        div = self.news_block(description_short, news, title)
        return div

    def news_block(self, description_short, news, title):

        img_url = URL('static', 'images/press/home/heiup_aktuelles.png')
        div_img = DIV(IMG(_src=img_url, _style="width: 50px;"),
                      _class="media-left pull-left")
        posted__date = news['date_posted'].date()
        div_date = P(posted__date.strftime("%d.%m.%Y "), _class="media-heading")
        div_heading = H5(XML(title))
        div_short_descrpition = P(XML(description_short), _class="boxText")
        div_body = DIV(div_date, div_heading, div_short_descrpition, _class="media-body")
        div = DIV(div_img, div_body, _class = "media")

        return div


if __name__ == '__main__':
    a = Announcements(myconf, db, locale)
    print(a.create_news_list())
