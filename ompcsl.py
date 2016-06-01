# -*- coding: utf-8 -*-
"""
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
"""

import datetime
from gluon.html import *
from gluon.serializers import json
from gluon import current


def csl_date(date):
    """
    Utility functino to build a date dict according to CSL JSON specification.

    Args:
        date: Instance of datetime.date or ISO-8601 date string

    Returns:
        Dict with "date-parts" array
    """
    if isinstance(date, datetime.date):
        return {'date-parts': [[date.year, date.month, date.day]]}
    elif isinstance(date, str):
        return {'raw': date}
    else:
        raise TypeError('date_published must be a string or an instance of datetime.date')


def csl_name(a):
    """
    Utility function to build name dict according to CSL JSON specification.

    Args:
        a: OMPItem of an author row

    Returns:
        Dict with "family", "given" and "suffix" name parts.
    """
    return {'family': a.attributes.last_name,
            'given': ' '.join([a.attributes.first_name, a.attributes.middle_name]),
            'suffix': a.attributes.suffix}


def build_csl_data(submission, authors, date_published, doi, press_settings, locale, series=None, editors = list):
    """
    Map from OMP entries for a submission to the CSL JSON data format.

    See Also: https://github.com/citation-style-language/schema#csl-json-schema

    Args:
        submission: OMPItem of a submission row with settings
        authors: List of OMPItems of author rows with settings
        date_published: Instance of datetime.date or string in ISO-8601 format
        doi: string
        press_settings: OMPSettings of press settings
        locale: locale string
        series: OMPItem of a series row with settings
        editors: List of OMPItems of editor rows with settings

    Returns:
        A dict with fields according to CSL JSON

    """
    csl_data = {
        'id': submission.attributes.submission_id,
        'type': 'book',
        'title': ' '.join([submission.settings.getLocalizedValue('prefix', locale), submission.settings.getLocalizedValue('title', locale)]),
        'publisher-place': press_settings.getLocalizedValue('location', ''),
        'publisher': press_settings.getLocalizedValue('publisher', ''),
        'issued': csl_date(date_published),
        'author': [csl_name(a) for a in authors]
    }
    if editors:
        csl_data['editor'] = [csl_name(e) for e in editors]
    subtitle = submission.settings.getLocalizedValue('subtitle', locale)
    if subtitle:
        csl_data['title'] += ': ' + subtitle
    if series:
        csl_data['collection-title'] = " ".join([series.settings.getLocalizedValue('prefix', locale), series.settings.getLocalizedValue('title', locale)])
        if series.settings.getLocalizedValue('subtitle', locale):
            csl_data['collection-title'] += " – " + series.settings.getLocalizedValue('subtitle', locale)
    if submission.attributes.series_position:
        csl_data['collection-number'] = submission.attributes.series_position
    if doi:
        csl_data['DOI'] = doi
    # Add subtitle to title, because CSL-JSON does not define a separate field for subtitle
    return csl_data


def render_citeproc_javascript(book_data, style, lang, target_element):
    return XML('<script type="application/json" id="book-csl-json">' + json(book_data) + '</script>' +
               """<script>
    function initCiteproc(styleID, lang, processorReady) {
        // Get the CSL style as a serialized string of XML
        var citeprocSys = {
            retrieveLocale: function (lang){ return this.localeXml },
            retrieveItem: function(id){ return $.parseJSON($('#book-csl-json').html()) }
            };
        if(lang == 'de') {
            lang = 'de-DE';
        }
        else if (lang == 'en') {
            lang = 'en-US';
        }
        else {
            console.log('Unsupported locale: ' + lang);
        }
        $.when(
          // Get the CSL style
          $.get('""" + URL('static', 'files/csl/') + """' + styleID + '.csl', function( data ) {
              citeprocSys.style = data;
          }),
          // Get the locale file
          $.get('""" + URL('static', 'files/csl/locales-') + """' + lang + '.xml', function(localeText) {
              citeprocSys.localeXml = localeText;
          }, 'text')
        ).then(function() {
            processorReady(new CSL.Engine(citeprocSys, citeprocSys.style, lang, true));
        });
    }

    function renderCitation(citeproc) {
        citeproc.updateItems([""" + str(book_data['id']) + """]);
        // Function returns an array, the first
        var bibHtml = citeproc.makeBibliography()[1][0];
        $('""" + target_element + """').html(bibHtml);
    }
    $(function() {
        initCiteproc('""" + style + "', '" + lang + """', renderCitation);
    });
</script>""")