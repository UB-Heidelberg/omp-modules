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

	def __init__ (self):
		pass

	def url (self, x):
		loc = x[0]
		lastmod = x[1]
		change_frequency = 'weekly'
		priority = x[2] if len(x) == 3 else 0.5

		t = Template(
			'<url>'
			'<loc>${loc}</loc>'
			'<lastmod>$lastmod</lastmod>'
			'<changefreq>$changefreq</changefreq>'
			'<priority>$priority</priority>'
			'</url>')

		return t.substitute(loc=loc, lastmod=lastmod,
		                    changefreq=change_frequency, priority=priority)

	def url_set (self, urls):
		urls_str = '\n'.join(urls)

		return '{}\n{}\n{}'.format(
			'<urlset xmlns = "http://www.sitemaps.org/schemas/sitemap/0.9" >',
			urls_str,
			'</urlset>')


class SiteMap:

	def __init__ (self):

		self.path = '{}/{}'.format(request.env.web2py_path, request.folder)
		self.press_id = myconf.take('omp.press_id')
		self.stop_words = ['snippets', 'series', 'catalog/snippets', 'partner',
		                   'reader', 'default']
		self.site_map_priority = '{}/{}'.format(self.path, 'sitemap.json')
		self.templates = Templates()
		self.static_path = '{}/{}'.format(self.path, 'static')
		self.views_path = '{}/{}'.format(self.path, 'views')
		self.monographs_priority = 0.9
		self.series_priority = 0.9
		self.ignore_apps = ['heiup']

	def createMonographs (self):

		submissions = ompdal.getSubmissionsByPress(self.press_id).as_list()

		return list(map(lambda x: ('/catalog/book/{}'.format(x['submission_id']), x['date_submitted'].date(), self.monographs_priority), submissions))

	def createSeries (self):

		series = ompdal.getSeriesByPress(self.press_id).as_list()
		series_map = list(
			map(lambda x: ('/catalog/series/{}'.format(x['path']),
			               datetime.datetime.now().date(),
			               self.series_priority),
			    series))
		series_info_map = list(
			map(lambda x: ('/series/info/{}'.format(x['path']),
			               datetime.datetime.now().date(),
			               self.series_priority),
			    series))

		return series_map + series_info_map

	def createURL (self, x):
		if myconf['web']['application'] not in self.ignore_apps:
			loc = '{}/{}{}'.format(myconf['web']['url'],
			                       myconf['web']['application'], x)
		else:
			loc = '{}{}'.format(myconf['web']['url'], x)
		return loc

	def IsValidURL (self, u):
		try:
			a = urlopen(u)
			if a.getcode() == 200:
				return True
			else:
				return False
		except:
			return False

	def createEntryList (self):
		file_list = self.createLinkList() + self.createMonographs() + \
                    self.createSeries()
		file_list = list(map(lambda x: (self.createURL(x[0]), x[1]), file_list))
		for s in file_list:
			if not self.IsValidURL(s[0]):
				file_list.remove(s)

		return self.templates.url_set(
			list(map(lambda x: self.templates.url(x), file_list)))

	def getStaticFiles (self):

		files = []

		for root, directories, filenames in os.walk(self.views_path):
			for f in filenames:

				date_modified = (
					datetime.datetime.fromtimestamp(
						os.path.getmtime(root)).date())
				controller_path = root.replace(self.views_path, '')
				if controller_path[1:] not in self.stop_words:
					if (os.path.getsize(os.path.join(root, f))):
						files.append(
							(os.path.join(controller_path, f),
							 date_modified.isoformat()))
		return files

	def removeEntries (self, l):

		l = list(filter(lambda x: x[0].endswith('.html'), l))
		l = list(filter(lambda x: x[0].startswith('/'), l))
		l = list(
			filter(lambda x: x[0] not in self.stop_words, l))

		return l

	def getConfig (self):

		if os.path.exists(self.site_map_priority):
			with open(self.site_map_priority) as f:
				return json.load(f)
		else:
			print('{} {}'.format('File not found:\t', self.site_map_priority))

	def createLinkList (self):

		dirs = self.getConfig().get(
			'directories') if self.getConfig() else []
		paths = list(map(lambda x: x["path"], dirs))
		l = self.removeEntries(self.getStaticFiles())

		for item in xrange(len(l)):
			d = l[item][0].split('/')[1]
			if d in paths:
				j = list(filter(lambda x: x['path'] == d, dirs) if dirs else d)
				priority = j[0]['priority'] if j else 0.5
				l[item] = l[item] + (priority,)

		return l

	def createSiteMap (self):

		f = open(join(s.static_path, 'sitemap.xml'), 'w')
		f.write(s.createEntryList())
		f.close()


if __name__ == '__main__':
	s = SiteMap()
	s.createSiteMap()
