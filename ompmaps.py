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
        self.monographs_priority = 0.9
        self.series_priority = 0.9
        self.ignore_apps = ['heiup']


    def createFileEntry(self, file_row):
        """

        :param file_row:
        :return: stirng
        """
        type = file_row.original_file_name.split('.').pop().strip().lower()
        items = [file_row.submission_id, file_row.genre_id, file_row.file_id, file_row.revision, file_row.file_stage, file_row.date_uploaded.strftime('%Y%m%d'), ]
        file_name = '-'.join([str(i) for i in items]) + '.' + type
        op = 'index' if type == 'xml' or type == 'html' else 'download'

        file_path = (join('/reader', op, str(file_row.submission_id), file_name), file_row.date_modified, 0.4)
        return file_path


    def createMonographs(self):
        """
        creates URL list for monographs
        :return: array
        """
        result = []
        submissions = ompdal.getSubmissionsByPress(self.press_id).as_list()

        result += sorted(list(map(lambda x: ('/catalog/book/{}'.format(x['submission_id']), x['date_submitted'].date(), self.monographs_priority), submissions)))

        pdf = [(x['submission_id'], ompdal.getPublicationFormatByName(x['submission_id'], 'PDF').first()) for x in submissions if ompdal.getPublicationFormatByName(x['submission_id'], 'PDF')]
        result += [self.createFileEntry(ompdal.getLatestRevisionOfFullBookFileByPublicationFormat(x[0], x[1]['publication_format_id']), ) for x in pdf if x]

        html = [(x['submission_id'], ompdal.getPublicationFormatByName(x['submission_id'], 'HTML').first()) for x in submissions if ompdal.getPublicationFormatByName(x['submission_id'], 'HTML')]
        result += [self.createFileEntry(ompdal.getLatestRevisionOfFullBookFileByPublicationFormat(x[0], x[1]['publication_format_id']), ) for x in html if x]

        return result


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

        entries = self.templates.URLSet(list(map(lambda x: self.templates.url(x), l)))
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


if __name__ == '__main__':
    s = SiteMap()
    s.createSiteMap()
