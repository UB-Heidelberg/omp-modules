# -*- coding: utf-8 -*-
"""
Copyright (c) 2016 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
"""

import datetime


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
        'id': str(submission.attributes.submission_id),
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
        # Add subtitle to title, because CSL-JSON does not define a separate field for subtitle
        csl_data['title'] += ': ' + subtitle
    if series:
        csl_data['collection-title'] = " ".join([series.settings.getLocalizedValue('prefix', locale), series.settings.getLocalizedValue('title', locale)])
        if series.settings.getLocalizedValue('subtitle', locale):
            csl_data['collection-title'] += " – " + series.settings.getLocalizedValue('subtitle', locale)
    if submission.attributes.series_position:
        csl_data['collection-number'] = submission.attributes.series_position
    if doi:
        csl_data['DOI'] = doi
    return csl_data
