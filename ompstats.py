# -*- coding: utf-8 -*-


'''
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
'''
import json
import re
import urllib
import urllib2
from ompdal import OMPDAL
from gluon.html import *
import os.path
from gluon import current

class OMPStats:

    def __init__(self, conf, db, locale):
        self.locale = locale
        self.ompdal = OMPDAL(db, conf)
        self.oas_server = conf.take('statistik.server')
        self.oas_id = conf.take('statistik.id')

    def checkOASService(self):
        '''
        check if oas server is available
        '''
        return urllib.urlopen(self.oas_server).getcode() == 200

    def createChapterDict(self, sid, fs):
        '''
        generate  table structure as  list of dicts
        '''
        trs, fids = [], []
        for i, ch in enumerate(self.ompdal.getChaptersBySubmission(sid)):
            cs = self.ompdal.getChapterSettings(ch['chapter_id'])
            stats = {}
            for f in fs:
                try:
                    pfid = self.ompdal.getPublicationFormatByName(
                        sid, f).first()['publication_format_id']
                    fid = self.ompdal.getLatestRevisionOfChapterFileByPublicationFormat(
                        ch['chapter_id'], pfid)['file_id']
                    fname = '-'.join([str(sid), str(fid), self.getNormalizedHTMLName(f)])
                    fids.append(fname)
                    stats[fname] = ''
                except:
                    pass
            trs.append({self.getFilteredTitle(cs): stats})
        return trs, fids

    def createChapterHTMLTable(self,sid, trs, st, fs, style):
        '''
        creates HTML Table
        '''

        table = TABLE(
            _class="table",
            _style=style)
        htr = TR()
        htr.append(TD())
        for f in fs:
          pfid = self.ompdal.getPublicationFormatByName(sid, f)
          htr.append(TD(f)) if pfid else ''         
        table.append(htr)
        table = self.setTotalsToTable(table, st, trs)
        return table

    def createFullDict(self, sid, fs):
        '''
        creates a dictionary for full files
        '''
        trs, fids = [], []
        for f in fs:
            fn = self.ompdal.getPublicationFormatByName(sid, f)
            stats = {}
            try:
                fid = self.ompdal.getLatestRevisionOfFullBookFileByPublicationFormat(
                    sid, fn.first()["publication_format_id"])
                fname = '-'.join([str(sid), str(fid['file_id']), self.getNormalizedHTMLName(f)])
                fids.append(fname)
                stats[fname] = ''
                trs.append({f: stats})
            except:
                pass

        return trs, fids

    def createFullHTMLTable(self, trs, st, fs ,style):
        '''
        creates html table for full files
        '''
        table = TABLE(
            _class="table",
            _style=style)
        table = self.setTotalsToTable(table, st, trs)
        return table

    def getChapterHTMLTable(self, sid, fs, style):
        '''
        creates  HTML chapter table
        '''
        trs, fids = self.createChapterDict(sid, fs)
        st = self.getOASResponse(fids)
        return self.createChapterHTMLTable(sid, trs, st, fs, style)

    def getFilteredTitle(self, cs):
        '''
        get the title row and extract row from the table Rows
        '''
        for row in cs:
            try:
                if row.locale == self.locale and row.setting_name == 'title':
                    return row['setting_value']
            except:
                return {}

    def getFullHTMLTable(self, sid, fs ,style):
        '''
        creates  chapter table
        '''
        trs, fids = self.createFullDict(sid, fs)
        st = self.getOASResponse(fids)
        return self.createFullHTMLTable(trs, st, fs, style)

    def getOASResponse(self, fids):
        '''
        get the oastatistik  json and convert into a python dictionary
        '''
        url = ''.join([self.oas_server, '?repo=', self.oas_id,
                       '&', 'type=json', '&', 'ids=', ','.join(fids)])
        req = urllib2.Request(url)
        r = urllib2.urlopen(req)
        return json.loads(r.read())

    
    def getNormalizedHTMLName(self, f):
      return 'xml' if f=='html' else f
    
    def getTotalForFileID(self, k, st):
        '''
        calculate some for a  file id
        '''
        sum = 0
        if k in st.keys():
          for k2 in st[k]['all_years']:
           sum += int(k2['volltext'])
        return sum

    def setTotalsToTable(self, table, st, trs):
        '''
        add rows to the table
        '''
        total = 0
        for i in range(len(trs)):
            for k, v in trs[i].iteritems():
                tr = TR(TD(k))
                for k2 in v.keys():
                    t = self.getTotalForFileID(k2, st)
                    tr.append(TD(t))
                    total += t
                    
                table.append(tr)
            table.append(TR(TD(current.T('Total'),TD(total))))
        return table
