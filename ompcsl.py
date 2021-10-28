# -*- coding: utf-8 -*-
"""
Copyright (c) 2016 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
"""

import datetime
from ompdal import OMPDAL, OMPSettings, OMPItem
from ompformat import dateFromRow

class OMPCSL():
    def __init__(self, dal, config, locale=''):
        self.locale = locale
        self.db = dal
        self.config = config

    def load_csl_data(self, submission_id):
        """
        Map from OMP entries for a submission to the CSL JSON data format.

        See Also: https://github.com/citation-style-language/schema#csl-json-schema

        Args:
            submission: OMPItem of a submission row with settings
            authors: List of OMPItems of author rows with settings
            date_published: Instance of datetime.date or string in ISO-8601 format
            doi: string
            press_settings: OMPSettings of press settings
            self.locale: self.locale string
            series: OMPItem of a series row with settings
            editors: List of OMPItems of editor rows with settings

        Returns:
            A dict with fields according to CSL JSON

        """

        press_id = self.config.take('omp.press_id')
        press_settings = OMPSettings(self.db.getPressSettings(press_id))

        # Get basic submission info (check, if submission is associated with the actual press and if the submission has been published)
        submission = self.db.getPublishedSubmission(submission_id, press_id=press_id)
        if not submission:
            raise ValueError("Unknown submission_id: " + submission_id)
        submission = OMPItem(submission, OMPSettings(self.db.getSubmissionSettings(submission_id)))

        editors = [OMPItem(e, OMPSettings(self.db.getAuthorSettings(e.author_id))) for e in
                   self.db.getEditorsBySubmission(submission_id)]

        authors = [OMPItem(a, OMPSettings(self.db.getAuthorSettings(a.author_id))) for a in
                                      self.db.getActualAuthorsBySubmission(submission_id, filter_browse=True)]

        date_published = None
        date_first_published = None
        pdf = self.db.getPublicationFormatByName(submission_id, self.config.take('omp.doi_format_name')).first()
        # Get DOI from the format marked as DOI carrier
        doi = OMPSettings(self.db.getPublicationFormatSettings(pdf.publication_format_id)).getLocalizedValue(
                "pub-id::doi", "") if pdf else None # DOI always has empty self.locale

        # Get the OMP publication date (column publication_date contains latest catalog entry edit date.) Try:
        # 1. Custom publication date entered for a publication format calles "PDF"
        if pdf:
            date_first_published = self.db.getPublicationDatesByPublicationFormat(pdf.publication_format_id, role='11')\
                .first()
            date_published = dateFromRow(
                self.db.getPublicationDatesByPublicationFormat(pdf.publication_format_id, role='01').first())
        # 2. Date on which the catalog entry was first published
        if not date_published:
            date_row = self.db.getMetaDataPublishedDates(submission_id).first()
            date_published = date_row.date_logged if date_row else None
        # 3. Date on which the submission status was last modified (always set)
        if not date_published:
            date_published = submission.attributes.date_status_modified

        series = self.db.getSeriesBySubmissionId(submission_id)
        if series:
            series = OMPItem(series, OMPSettings(self.db.getSeriesSettings(series.series_id)))

        csl_data = {
            'id': str(submission.attributes.submission_id),
            'type': 'book',
            'title': ' '.join([submission.settings.getLocalizedValue('prefix', self.locale),
                               submission.settings.getLocalizedValue('title', self.locale)]),
            'publisher-place': press_settings.getLocalizedValue('location', ''),
            'publisher': press_settings.getLocalizedValue('publisher', ''),
            'issued': csl_date(date_published),
            'author': [csl_name(a, self.locale) for a in authors]
        }
        if date_first_published:
            csl_data['original-date'] = csl_date(date_first_published.date)
        if editors:
            csl_data['editor'] = [csl_name(e, self.locale) for e in editors]
        subtitle = submission.settings.getLocalizedValue('subtitle', self.locale)
        if subtitle:
            # Add subtitle to title, because CSL-JSON does not define a separate field for subtitle
            csl_data['title'] += ': ' + subtitle
        if series:
            csl_data['collection-title'] = " ".join([series.settings.getLocalizedValue('prefix', self.locale),
                                                     series.settings.getLocalizedValue('title', self.locale)])
            series_subtitle = series.settings.getLocalizedValue('subtitle', self.locale)
            if series_subtitle:
                csl_data['collection-title'] += " – " + series_subtitle
        if submission.attributes.series_position:
            csl_data['collection-number'] = submission.attributes.series_position
        if doi:
            csl_data['DOI'] = doi
        return csl_data


def csl_date(date):
    """
    Utility function to build a date dict according to CSL JSON specification.

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


def csl_name(author, locale='en_US'):
    """
    Utility function to build name dict according to CSL JSON specification.

    Args:
        author: OMPItem of an author row

    Returns:
        Dict with "family", "given" and "suffix" name parts.
    """
    if not isinstance(author, OMPItem):
        raise TypeError('author must be an OMPItem')
    return {'family': author.settings.getLocalizedValue('familyName', locale),
            'given': author.settings.getLocalizedValue('givenName', locale),
            'suffix': ''}
