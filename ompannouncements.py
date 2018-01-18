# -*- coding: utf-8 -*-
'''
Created on 11 Jan 2018

@author: wit
'''

from ompdal import OMPDAL


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

        name = 'Aktuelles' if self.locale == 'de_DE' else 'News'

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

        news = self.get_news().as_list()

        return list(map(lambda e: self.create_news(e['announcement_id']), news))

    def create_news(self, news_id):

        n = self.ompdal.getAnnouncementSettings(news_id).as_list()

        t= list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'title', n))
        title = t[0]['setting_value'] if t else ''

        ds = list(filter(lambda e: e['locale'] == self.locale and e['setting_name'] == 'descriptionShort', n))
        description_short = ds[0]['setting_value'] if ds else ''

        return (title, description_short)



if __name__ == '__main__':
    a = Announcements(myconf, db, locale)
    print(a.create_news_list())
