# -*- coding: utf-8 -*-
'''
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
'''
from gluon import HTTP,BR

#TODO reactivate for solr
'''
try:
    import sunburnts
except ImportError as err:
    raise HTTP(400, '{} <br/> {}'.format(err, "Install using sudo pip install sunburnt"))
'''
class OMPSOLR:
    def __init__(self,db,conf, **other_kwargs):
        self.db = db
        self.conf = conf
        self.other_kwargs = other_kwargs

        try:
            try:
                solr_url = conf.take('plugin_solr.url')
            except BaseException as err:
                raise HTTP(400, 'plugin_solr.url not in private/appconfig.ini {} {}'.format(BR(),err))
            try:
                self.si = sunburnt.SolrInterface(solr_url)

            except (RuntimeError,OverflowError, sunburnt.SolrError)  as err:
                raise HTTP(400, '{}'.format(err))
        except RuntimeError as err:
            raise HTTP(400, err)

    def __repr__(self):
        return 'Book("%s", "%s")' % (title, author)



# document = {"submission_id":43, "press_id":6,"en_title_s":u"öüßä","de_title_s":"Test EN","locale_s":"de","authors":["Dulip Withanage","Max Musterman"]}
# si.add(document)
# si.delete(queries=si.Q("*"))
# si.commit()

# for i in si.query(press_id="6").execute():
#    solr_results.append(i)

# curl "http://localhost:8983/solr/presss_portal/update?commit=true" -H "Content-Type: text/xml" --data-binary '<delete><query>*:*</query></delete>'



