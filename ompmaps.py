#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 11 Jan 2018

@author: wit
'''

import datetime
import json
import os
from os.path import join
from string import Template
from urllib.request import urlopen

from ompdal import OMPDAL
from ompformat import downloadLink

ompdal = OMPDAL(db, myconf)


class Templates:

    def url(self, entry):
        """
        Creates template url
        :param entry:  Set
        :return: Template
        """
        loc = entry[0]
        lastmod = entry[1]
        change_frequency = 'weekly'
        priority = entry[2] if len(entry) == 3 else 0.5

        t = Template(
            '<url>'
            '<loc>${loc}</loc>'
            '<lastmod>$lastmod</lastmod>'
            '<changefreq>$changefreq</changefreq>'
            '<priority>$priority</priority>'
            '</url>')

        return t.substitute(loc=loc, lastmod=lastmod, changefreq=change_frequency, priority=priority)


    def URLSet(self, urls):
        """
        Creates the URL map
        :param urls: list
        :return: string
        """
        urls_str = '\n'.join(urls)

        return '{}\n{}\n{}'.format(
            '<urlset xmlns = "http://www.sitemaps.org/schemas/sitemap/0.9" >',
            urls_str,
            '</urlset>')


class SiteMap:
    """
    Site map class
    """
    def __init__(self):

        self.path = '{}/{}'.format(request.env.web2py_path, request.folder)
        self.press_id = myconf.take('omp.press_id')
        self.stop_words = ['snippets', 'series', 'catalog/snippets', 'partner', 'reader', 'default']
        self.site_map_priority = '{}/{}'.format(self.path, 'sitemap.json')
        self.templates = Templates()
        self.static_path = '{}/{}'.format(self.path, 'static')
        self.views_path = '{}/{}'.format(self.path, 'views')
        self.chapters_priority = 0.8
        self.monographs_priority = 0.9
        self.series_priority = 0.9
        self.ignore_apps = ['heiup']
        self.db = db
        self.sc = self.db.submission_chapters


    def createFileEntry(self, file_row):
        """

        :param file_row:
        :return: stirng
        """
        file_path = (downloadLink(file_row), file_row.date_modified.date(), 0.4)
        return file_path


    def createMonographs(self):
        """
        creates URL list for monographs
        :return: array
        """
        result = []
        submissions = ompdal.getSubmissionsByPress(self.press_id).as_list()

        result += list(map(lambda x: ('/catalog/book/{}'.format(x['submission_id']), x['date_submitted'].date(), self.monographs_priority), submissions))


        for s in submissions:
            formats = ompdal.getDigitalPublicationFormats(s['submission_id'], available=True, approved=True)
            for f in formats:
                file_row = ompdal.getLatestRevisionOfFullBookFileByPublicationFormat(s['submission_id'], f.publication_format_id)
                if file_row:
                    result.append(self.createFileEntry(file_row))

            result += self.createChapters(s)

        return sorted(result)


    def createSeries(self):
        """
         creates URL list for series
        :return: array
        """
        series = ompdal.getSeriesByPress(self.press_id).as_list()
        series_map = list(map(lambda x: ('/catalog/series/{}'.format(x['path']), datetime.datetime.now().date(), self.series_priority), series))
        series_info_map = list(map(lambda x: ('/series/info/{}'.format(x['path']), datetime.datetime.now().date(), self.series_priority), series))

        return series_map + series_info_map


    def createApplicationPath(self, path):
        """

        :param path:
        :return: string
        """
        if myconf['web']['application'] not in self.ignore_apps:
            loc = '{}/{}{}'.format(myconf['web']['url'], myconf['web']['application'], path)
        else:
            loc = '{}{}'.format(myconf['web']['url'], path)
        return loc


    def IsValidURL(self, url,check=False):
        """
        Checks if URL is valid, default no.
        :param url:
        :param check:
        :return: boolean
        """
        if  not check:
            return True

        try:
            a = urlopen(url)
            result = True if a.getcode() == 200 else False
            return result

        except:
            return False


    def createSitemapEntries(self):
        """
        Create all  Sitemap entries
        :return: string
        """
        l = self.createStaticFilesList() + self.createMonographs() + self.createSeries()
        l = list(map(lambda x: (self.createApplicationPath(x[0]), x[1]), l))
        for s in l:
            if not self.IsValidURL(s[0]):
                l.remove(s)

        entries = self.templates.URLSet(list(map(lambda x: self.templates.url(x), l))) if l else []
        return entries


    def getStaticFiles(self):
        """
        get static files list
        :return: array
        """
        files = []

        for root, directories, filenames in os.walk(self.views_path):
            for f in filenames:

                date_modified = (datetime.datetime.fromtimestamp(os.path.getmtime(root)).date())
                controller = root.replace(self.views_path, '')
                if controller[1:] not in self.stop_words:
                    if (os.path.getsize(os.path.join(root, f))):
                        files.append((os.path.join(controller, f), date_modified.isoformat()))
        return files


    def removeEntries(self, file_list):
        """
        Remove specified files
        :param file_list:
        :return: array
        """
        file_list = list(filter(lambda x: x[0].endswith('.html'), file_list))
        file_list = list(filter(lambda x: x[0].startswith('/'), file_list))
        file_list = list(filter(lambda x: x[0] not in self.stop_words, file_list))

        return file_list


    def getPriorityConfiguration(self):
        """
        get priority file
        :return: JSON
        """
        if os.path.exists(self.site_map_priority):
            with open(self.site_map_priority) as f:
                return json.load(f)
        else:
            print('{} {}'.format('File not found:\t', self.site_map_priority))
            return []


    def createStaticFilesList(self):
        """
        Creates list of static files
        :return: array
        """
        dirs = self.getPriorityConfiguration().get(
            'directories') if self.getPriorityConfiguration() else []
        paths = list(map(lambda x: x["path"], dirs))
        files = self.removeEntries(self.getStaticFiles())

        for item in range(len(files)):
            d = files[item][0].split('/')[1]
            if d in paths:
                j = list(filter(lambda x: x['path'] == d, dirs) if dirs else d)
                priority = j[0]['priority'] if j else 0.5
                files[item] = files[item] + (priority,)

        return files


    def createSiteMap(self):
        """
        Create full sitemap
        """
        f = open(join(s.static_path, 'sitemap.xml'), 'w')
        f.write(s.createSitemapEntries())
        f.close()


    def createChapters(self, s):
        """
        Creates chapter entries
        :param s:
        :return: array
        """
        result = []
        chapter_rows = self.db(self.sc.submission_id == s['submission_id']).select(self.sc.chapter_id).as_list()
        formats = ompdal.getDigitalPublicationFormats(s['submission_id'], available=True, approved=True)
        for c in chapter_rows:
            chapter_settings_rows = ompdal.getChapterSettings(c['chapter_id']).as_list()
            if self.getTableSetting(chapter_settings_rows, 'pub-id::doi'):
                result.append(('/catalog/book/{}/c{}'.format(s['submission_id'], c['chapter_id']), s['date_submitted'].date(), self.chapters_priority))

                chapter_file_entries = []
                for pf in formats:
                    chapter_file_row = ompdal.getLatestRevisionOfChapterFileByPublicationFormat(c['chapter_id'], pf.publication_format_id)
                    if chapter_file_row:
                        chapter_file_entries.append(self.createFileEntry(chapter_file_row))
                result += chapter_file_entries

        return result


    def getTableSetting(self, settings_list, name):
        """
        get table setting from OMP
        :param settings_list: array
        :param name:
        :return:
        """
        result = ''.join(set([settings['setting_value'] for settings in settings_list if settings['setting_name'] == name]))
        return result

if __name__ == '__main__':
    s = SiteMap()
    s.createSiteMap()

