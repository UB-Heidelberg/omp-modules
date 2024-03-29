# -*- coding: utf-8 -*-
'''
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
'''
import re
from operator import itemgetter
import logging
from collections import OrderedDict

DOI_SETTING_NAME = 'pub-id::doi'


class OMPSettings:
    def __init__(self, rows=[]):
        self._settings = dict()
        for row in rows:
            self._settings.setdefault(row.setting_name, {})[row.locale] = row.setting_value

    def getLocalizedValue(self, setting_name, locale, fallback="en_US"):
        if setting_name in self._settings:
            value = self._settings[setting_name].get(locale, "")
            if not value:
                value = self._settings[setting_name].get(fallback, "")
            return value
        else:
            return ""

    def getValues(self, setting_name):
        return self._settings.get(setting_name, {})


class OMPItem:
    def __init__(self, row, settings=OMPSettings(), associated_items={}):
        self.attributes = row
        self.settings = settings
        self.associated_items = associated_items


class OMPDAL:
    """
    A rudimentary database abstraction layer for the OMP database.
    """

    def __init__(self, db, conf):
        self.db = db
        self.conf = conf
        self.logger = logging.getLogger(conf.take('web.application'))

    def getAnnouncementWithSettings(self, announcement_id):
        """
        Get announcement by id, including setting values and return as dictionary.
        """
        a = self.db.announcements(announcement_id).as_dict()
        q = (self.db.announcement_settings.announcement_id == announcement_id)

        for row in self.db(q).select(self.db.announcement_settings.ALL):
            a.setdefault(row.setting_name, {})[row.locale] = row.setting_value
        return a

    def getAnnouncementsByPress(self, press_id):
        """
        Get announcement by press
        """
        a = self.db.announcements
        q = (a.assoc_id == press_id)

        return self.db(q).select(a.ALL, orderby=~a.date_posted)

    def getAnnouncementsByPressGroupedByYearAndMonth(self, press_id, locale):
        """
        Get announcement by press and year, month
        """
        sql = ' '.join([
            'Select a.date_posted date, a.announcement_id id, an_s.setting_value as title',
            'from announcements a, announcement_settings an_s',
            'where assoc_id = {}'.format(press_id),
            'and an_s.announcement_id = a.announcement_id',
            'and an_s.locale = "{}"'.format(locale),
            'and an_s.setting_name = "title"',
            'order by date_posted desc'
        ])
        by_years_and_months = OrderedDict()
        for row in self.db.executesql(sql, as_dict=True):
            date = row['date']
            by_years_and_months.setdefault(date.year, OrderedDict()).setdefault(date.month, []).append(row)
        return by_years_and_months

    def getAnnouncementsByType(self, t):
        """
        Get Announcements by type
        """
        a = self.db.announcements

        q = ((a.type_id == t.type_id)
             & (a.assoc_id == t.assoc_id)
             & (a.assoc_type == t.assoc_type)
             )

        return self.db(q).select(a.ALL, orderby=~a.date_posted)

    def getAnnouncementSettings(self, announcement_id):
        """
        Get Announcement settings
        """
        a = self.db.announcement_settings
        q = (a.announcement_id == announcement_id)

        return self.db(q).select(a.ALL)

    def getAnnouncementType(self, type_id):
        """
         get Announcement type
        """

        return self.db.announcement_types[type_id]

    def getAnnouncementTypeSettings(self, type_id):
        """
        Get Announcement type settings
        """
        ats = self.db.announcement_type_settings

        return self.db(ats.type_id == type_id).select(ats.ALL)

    def getPresses(self):
        """
        Get all  enabled presses
        """
        ps = self.db.presses
        q = (ps.enabled == 1)

        return self.db(q).select(ps.ALL)

    def getPress(self, press_id):
        """
        Get row for a given press id.
        """
        return self.db.presses[press_id]

    def getPressSettings(self, press_id):
        """
        Get settings for a given press.
        """
        ps = self.db.press_settings
        q = (ps.press_id == press_id)

        return self.db(q).select(ps.ALL)

    def getSubmission(self, submission_id):
        """
        Get row for a given submission id.
        """
        return self.db.submissions[submission_id]

    def getSubmissionsByPress(self, press_id, ignored_submission_id=-1, status=3):
        """
        Get all submissions in press with the given status (default: 3=published).
        """
        s = self.db.submissions
        q = ((s.context_id == press_id)
             & (s.submission_id != ignored_submission_id)
             & (s.status == status)
             )

        return self.db(q).select(s.submission_id, s.series_id, s.date_submitted, s.series_position, orderby=~s.date_submitted)

    def getSubmissionsRangeByPress(self, press_id, from_id, to_id, ignored_submission_id=-1, status=3):
        """
        Get submissions range in press with the given status (default: 3=published).
        """
        s = self.db.submissions
        q = ((s.context_id == press_id)
             & (s.submission_id != ignored_submission_id)
             & (s.status == status)
             )

        return self.db(q).select(s.submission_id, s.series_id, s.date_submitted, s.series_position,
                                 orderby=~s.date_submitted, limitby=(from_id, to_id), cacheable=True)


    def getPublishedSubmissionsRangeByPressSorted(self, press_id, from_id, to_id,
                                                  ignored_submission_id=-1, status=3,
                                                  order_by='date_published', order_by_ascending=True):
        """
        Get submissions range in press with the given status (default: 3=published).
        """
        ps = self.db.published_submissions
        s = self.db.submissions
        q = ((s.context_id == press_id)
             & (s.submission_id != ignored_submission_id)
             & (s.status == status)
             & (s.submission_id == ps.submission_id)
             )
        order_by = getattr(ps, order_by)
        if not order_by_ascending:
            order_by = ~order_by
        return self.db(q).select(s.submission_id, s.series_id, s.date_submitted, s.series_position,
                                 ps.date_published, orderby=order_by,
                                 limitby=(from_id, to_id), cacheable=True)



    def getSubmissionsByCategory(self, category_id, ignored_submission_id=-1, status=3):
        """
        Get all submissions in a category with the given status (default: 3=published).
        """
        s = self.db.submissions
        sc = self.db.submission_categories

        q = ((sc.category_id == category_id)
             & (sc.submission_id == s.submission_id)
             & (s.submission_id != ignored_submission_id)
             & (s.status == status)
             )

        return self.db(q).select(s.ALL)

    def getSubmissionsBySeries(self, series_id, ignored_submission_id=-1, status=3, respect_sort_option=True):
        """
        Get all submissions in a series with the given status (default: 3=published).

        """
        series_settings = OMPSettings(self.getSeriesSettings(series_id))
        sort_option = series_settings.getValues('sortOption')['']

        def extract_series_position(row):
            # Special case for submissions in a series called 'Beiheft'
            if row.series_position.startswith('Beiheft'):
                prefix = 1,
            else:
                prefix = 0,
            return prefix + tuple(int(s) for s in re.findall(r'\d+', row.series_position))

        sort_parameters = {
            'seriesPosition-2': dict(key=extract_series_position, reverse=True),
            'seriesPosition-1': dict(key=extract_series_position, reverse=False),
            'title-1': dict(key=lambda row: row.submission_settings.setting_value, reverse=False),
            'title-2': dict(key=lambda row: row.submission_settings.setting_value, reverse=True),
            'datePublished-2': dict(key=lambda row: row.published_submissions.date_published, reverse=True),
            'datePublished-1': dict(key=lambda row: row.published_submissions.date_published, reverse=False),
        }

        s = self.db.submissions
        ss = self.db.submission_settings
        q = ((s.series_id == series_id)
             & (s.submission_id != ignored_submission_id)
             & (s.status == status)
             )
        if sort_option.startswith('title'):
            joins = ss.on((s.submission_id == ss.submission_id) & (ss.setting_name == 'title') & (ss.locale == 'de_DE'))
        elif sort_option.startswith('datePublished'):
            ps = self.db.published_submissions
            joins = ps.on(s.submission_id == ps.submission_id)
        else:
            joins = None
        rows_iterator = self.db(q).select(join=joins)
        if respect_sort_option:
            # use the dict stored in the sort_parameters dict as arguments for the sort method
            if joins:
                return [rows.submissions for rows in sorted(rows_iterator, **sort_parameters[sort_option])]
            else:
                return sorted(rows_iterator, **sort_parameters[sort_option])
        else:
            return list(rows_iterator)

    def getPublishedSubmission(self, submission_id, press_id=None):
        """
        Get submission info for a given submission id, but only return, if the
        submission has been published and is associated with a certain press.
        """
        s = self.db.submissions

        if press_id:
            q = ((s.submission_id == submission_id)
                 & (s.status == "3")
                 & (s.context_id == press_id)
                 )
        else:
            q = ((s.submission_id == submission_id)
                 & (s.status == "3")
                 )

        return self.db(q).select(s.ALL).first()

    def getSubmissionSettings(self, submission_id):
        """
        Get settings for a given submission.
        """
        q = (self.db.submission_settings.submission_id == submission_id)

        return self.db(q).select(self.db.submission_settings.ALL)

    def getAuthorsBySubmission(self, submission_id, filter_browse=False):
        """
        Get all authors associated with the specified submission regardless of their role.
        """
        a = self.db.authors
        q = (a.submission_id == submission_id)
        if filter_browse:
            q &= (a.include_in_browse == True)
        return self.db(q).select(
                a.ALL,
                orderby=a.seq
                )

    def getAuthorsByPress(self, press_id, filter_browse=True, status=3):
        """
        Get all authors associated with the specified press regardless of their role.
        """
        # TODO This functionality could be covered by the search service
        select_sql = 'SELECT TRIM(au_given_names.setting_value) as first_name, TRIM(au_family_names.setting_value) as last_name, a.submission_id'
        from_sql = 'FROM author_settings au_given_names, author_settings au_family_names, authors a, submissions s'
        conditions = [
            's.context_id = {}'.format(press_id),
            's.status = {}'.format(status),
            'au_given_names.locale = s.locale',
            'au_family_names.locale = s.locale',
            'a.submission_id = s.submission_id',
            'a.author_id = au_given_names.author_id',
            'a.author_id = au_family_names.author_id',
            'au_given_names.setting_name = "givenName"',
            'au_family_names.setting_name = "familyName"']
        if filter_browse:
            conditions.append('a.include_in_browse = 1')

        where_sql = 'WHERE ' + '\n AND '.join(conditions)
        order_sql = 'ORDER BY last_name, first_name'
        sql = '\n'.join([
            select_sql,
            from_sql,
            where_sql,
            order_sql
            ])
        return self.db.executesql(sql, as_dict=True)

    def getActualAuthorsBySubmission(self, submission_id, filter_browse=True):
        """
        Get all authors associated with the specified submission with chapter author role.
        """
        try:
            # Try to extract a list
            author_group_ids = self.conf.take('omp.author_ids', cast=lambda s: map(int, s.split(',')))
        except:
            return []

        a = self.db.authors
        q = (a.submission_id == submission_id) & a.user_group_id.belongs(author_group_ids)
        if filter_browse:
            q &= a.include_in_browse == 1
        return self.db(q).select(self.db.authors.ALL, orderby=self.db.authors.seq)

    def getEditorsBySubmission(self, submission_id, filter_browse=True):
        """
        Get all authors associated with the specified submission with editor role.
        """
        try:
            editor_group_id = self.conf.take('omp.editor_id')
        except:
            return []

        a = self.db.authors
        q = (a.submission_id == submission_id) & (a.user_group_id == editor_group_id)
        if filter_browse:
            q &= a.include_in_browse == 1

        return self.db(q).select(self.db.authors.ALL, orderby=self.db.authors.seq)

    def getAuthorsByChapter(self, chapter_id):
        """
        Get authors associated with a given chapter.
        """
        sca = self.db.submission_chapter_authors
        a = self.db.authors
        q = ((sca.chapter_id == chapter_id)
             & (a.author_id == sca.author_id)
             )

        return self.db(q).select(a.ALL, orderby=sca.seq)

    def getAuthor(self, author_id):
        """
        Get row for a given author id.
        """
        return self.db.authors[author_id]

    def getAuthorSettings(self, author_id):
        """
        Get settings for a given author.
        """
        aus = self.db.author_settings
        q = (aus.author_id == author_id)

        return self.db(q).select(aus.ALL)

    def getUserSettings(self, user_id):
        us = self.db.user_settings
        q = (us.user_id == user_id)

        return self.db(q).select(us.ALL)

    def getSeriesByPress(self, press_id):
        """
        Get all series published in the given press.
        """
        s = self.db.series
        q = (s.press_id == press_id)

        return self.db(q).select(
                s.ALL, orderby=s.seq
                )

    def getSeriesByPathAndPress(self, series_path, press_id):
        """
        Get the series with the given pass in the given press (unique).
        """
        s = self.db.series
        q = ((s.path == series_path) & (s.press_id == press_id))

        res = self.db(q).select(s.ALL)
        if res:
            return res.first()

    def getSeriesBySubmissionId(self, submission_id):
        """
        Get the series the given submission is assigned to.
        """
        sub = self.db.submissions
        ser = self.db.series

        q = ((sub.submission_id == submission_id) & (ser.series_id == sub.series_id))

        res = self.db(q).select(ser.ALL)
        if res:
            return res.first()

    def getCategoryByPathAndPress(self, category_path, context_id):
        """
        Get the category by path in the given press (unique).
        """
        c = self.db.categories
        q = ((c.path == category_path) & (c.context_id == context_id))

        res = self.db(q).select(c.ALL)
        if res:
            return res.first()

    def getCategoriesByPress(self, context_id):
        """
        Get all categories in  press.
        """
        c = self.db.categories
        q = (c.context_id == context_id)

        return self.db(q).select(c.ALL)

    def getCategoriesBySeries(self, series_id):
        """
        Get the assigned Category of series
        """
        cat = self.db.series_categories

        q = (cat.series_id == series_id)

        return self.db(q).select(cat.ALL)

    def getCategoryBySubmissionId(self, submission_id):
        """
        Get the assigned Category of submission
        """
        cat = self.db.submission_categories

        q = (cat.submission_id == submission_id)

        res = self.db(q).select(cat.ALL)
        if res:
            return res.first()

    def getCategorySettings(self, category_id):
        """
        Get settings for a given category
        """
        cs = self.db.category_settings
        q = (cs.category_id == category_id)

        return self.db(q).select(cs.ALL)

    def getCategory(self, category_id):
        """
        Get row for a given series id.
        """
        return self.db.categories[category_id]

    def getSeries(self, series_id):
        """
        Get row for a given series id.
        """
        return self.db.series[series_id]

    def getSeriesEditors(self, press_id, series_id):
        """
        Get editors for the given series.
        """
        se = self.db.series_editors
        u = self.db.users
        q = ((se.press_id == press_id)
             & (se.series_id == series_id)
             & (u.user_id == se.user_id)
             )

        return self.db(q).select(u.ALL)

    def getLocalizedCategorySettings(self, category_id, setting_name, locale):
        """
        Get row for a given category
        """
        cs = self.db.category_settings
        q = ((cs.locale == locale)
             & (cs.category_id == category_id)
             & (cs.setting_name == setting_name)
             )
        return self.db(q).select(cs.ALL).first()

    def getLocalizedSeriesSettings(self, series_id, locale):
        """
        Get row for a given series id.
        """
        return self.db.series[series_id]

    def getSeriesSettings(self, series_id):
        """
        Get settings for a given series.
        """
        ss = self.db.series_settings
        q = (ss.series_id == series_id)

        return self.db(q).select(ss.ALL)

    def getChaptersBySubmission(self, submission_id):
        """
        Get all chapters associated with the given submission.
        """
        sc = self.db.submission_chapters
        q = (sc.submission_id == submission_id)

        return self.db(q).select(
                sc.ALL,
                orderby=sc.seq
                )

    def getChapter(self, chapter_id):
        """
        Get row for a given chapter id.
        """
        return self.db.submission_chapters[chapter_id]

    def getChapterSettings(self, chapter_id):
        """
        Get settings for a given chapter id.
        """
        scs = self.db.submission_chapter_settings
        q = (scs.chapter_id == chapter_id)

        return self.db(q).select(scs.ALL)

    def getPublicationFormatsBySubmission(self, submission_id, available=True, approved=True):
        """
        Get all approved and available publication formats for the given submission.
        """
        pf = self.db.publication_formats
        q = ((pf.submission_id == submission_id)
             & (pf.is_available == available)
             & (pf.is_approved == approved)
             )

        return self.db(q).select(pf.ALL)

    def getAllPublicationFormatsBySubmission(self, submission_id, available=True, approved=True):
        """
        Get all approved and available publication formats for the given submission.
        """
        pf = self.db.publication_formats
        q = (pf.submission_id == submission_id)

        return self.db(q).select(pf.ALL)

    def getPhysicalPublicationFormats(self, submission_id, available=True, approved=True):
        """
        Get all publication formats marked as physical format for the given submission.
        """
        pf = self.db.publication_formats
        q = ((pf.submission_id == submission_id)
             & (pf.is_available == available)
             & (pf.is_approved == approved)
             & (pf.physical_format == True)
             )

        return self.db(q).select(pf.ALL)

    def getControlledVocabsBySubmission(self, submission_id):
        cv = self.db.controlled_vocabs
        q = (cv.assoc_id == submission_id)
        return self.db(q).select(cv.ALL)

    def getControlledVocabEntriesByID(self, vocab_id):
        cv = self.db.controlled_vocab_entries
        q = (cv.controlled_vocab_id == vocab_id)
        return self.db(q).select(cv.ALL)

    def controlledVocabEntrySettingsByID(self, entry_id):
        cv = self.db.controlled_vocab_entry_settings
        q = (cv.controlled_vocab_entry_id == entry_id)
        return self.db(q).select(cv.ALL)


    def getDigitalPublicationFormats(self, submission_id, available=True, approved=True):
        """
        Get all publication formats not marked as physical format for the given submission.
        """
        pf = self.db.publication_formats
        q = ((pf.submission_id == submission_id)
             & (pf.is_available == available)
             & (pf.is_approved == approved)
             & (pf.physical_format == False)
             )

        return self.db(q).select(pf.ALL)

    def getPublicationFormat(self, publication_format_id):
        """
        Get row for a given publication format id.
        """
        return self.db.publication_formats[publication_format_id]

    def getPublicationFormatByName(self, submission_id, name, available=True, approved=True):
        """
        Get publication format for the given submission where any of the settings for 'name' matches the given string
        name.
        """
        pf = self.db.publication_formats
        pfs = self.db.publication_format_settings
        q = ((pf.submission_id == submission_id)
             & (pf.is_available == available)
             & (pf.is_approved == approved)
             & (pfs.publication_format_id == pf.publication_format_id)
             & (pfs.setting_name == "name")
             & (pfs.setting_value.lower() == name.lower())
             )
        return self.db(q).select(pf.ALL, groupby=pf.submission_id)

    def getPublicationFormatSettings(self, publication_format_id):
        """
        Get settings for a given publication format id.
        """
        pfs = self.db.publication_format_settings
        q = (pfs.publication_format_id == publication_format_id)

        return self.db(q).select(pfs.ALL)

    def getLatestRevisionOfChapterFileByPublicationFormat(self, chapter_id, publication_format_id):
        """
        Get the latest revision of the file associated with a given chapter and publication format.
        """
        sfs = self.db.submission_file_settings
        sf = self.db.submission_files

        q = ((sfs.setting_name.lower() == "chapterid")
             & (sfs.setting_value == chapter_id)
             & (sf.file_id == sfs.file_id)
             & (sf.assoc_id == publication_format_id)
             & (sf.file_stage == 10)
             )

        res = self.db(q).select(sf.ALL, orderby=sf.revision)
        if res:
            return res.last()

    def getLatestRevisionOfFullBookFileByPublicationFormat(self, submission_id, publication_format_id):
        """
        Get the latest revision of a file of genre "Book" for a given publication format.
        """
        try:
            monograph_type_id = self.conf.take('omp.monograph_type_id')
        except:
            return []
        sf = self.db.submission_files
        q = ((sf.submission_id == submission_id)
             & (sf.genre_id == monograph_type_id)
             & (sf.file_stage == 10)
             & (sf.assoc_id == publication_format_id)
             )

        res = self.db(q).select(sf.ALL, orderby=sf.revision)
        if res:
            return res.last()

    def getLatestRevisionOfEBook(self, submission_id, publication_format_id):
        """
        Get the latest revision of a file of genre "Book" for a given publication format.
        """
        try:
            monograph_type_id = self.conf.take('omp.epub_monograph_type_id')
        except:
            return []
        sf = self.db.submission_files
        q = ((sf.submission_id == submission_id)
             & (sf.genre_id == monograph_type_id)
             & (sf.file_stage == 10)
             & (sf.assoc_id == publication_format_id)
             )

        res = self.db(q).select(sf.ALL, orderby=sf.revision)
        if res:
            return res.last()

    def getLatestRevisionOfFileByPublicationFormatAndGenreKey(self, submission_id, publication_format_id, genre_key):
        """
        Get the latest revision of a file of genre "Book" for a given publication format.
        """
        sf = self.db.submission_files
        g = self.db.genres
        q = ((sf.submission_id == submission_id)
             & (sf.file_stage == 10)
             & (sf.assoc_id == publication_format_id)
             & (sf.genre_id == g.genre_id)
             & (g.entry_key == genre_key)
             )

        res = self.db(q).select(sf.ALL, orderby=sf.revision)
        if res:
            return res.last()

    def getReviewFilesByPublicationFormat(self, submission_id, publication_format_id):
        """
        Get the latest revision of a file of a review for a given publication format.
        """
        try:
            monograph_type_id = self.conf.take('omp.review_type_id')
        except:
            return []
        sf = self.db.submission_files
        q = ((sf.submission_id == submission_id)
             & (sf.genre_id == monograph_type_id)
             & (sf.file_stage == 10)
             & (sf.assoc_id == publication_format_id)
             )

        res = self.db(q).select(sf.ALL, orderby=sf.revision)
        return res

    def getSubmissionFileBySubmission(self, submission_id):
        """
        Get files of a submission.
        """
        sf = self.db.submission_files
        q = (sf.submission_id == submission_id)

        return self.db(q).select(sf.ALL)

    def getDependentFilesBySubmissionFileId(self, submission_file_id):
        """

        :param submission_file_id:
        :return:
        """
        sf = self.db.submission_files
        # assoc_type 515 is ASSOC_TYPE_SUBMISSION_FILE
        # See OMP source file : lib/pkp/classes/core/PKPApplication.inc.php:28
        q = (sf.assoc_id == submission_file_id) & (sf.assoc_type == 515) & (sf.file_stage == 17)
        files = {}
        for row in self.db(q).select(sf.ALL, orderby=~sf.revision):
            if row.file_id not in files:
                files[row.file_id] = row
        return list(files.values())

    def getSubmissionFileSettingsByIds(self, file_ids, locale=None):
        """
        Get settings for a given submission file.
        """
        sfs = self.db.submission_file_settings
        q = (sfs.file_id.belongs(file_ids))
        if locale:
            q &= (sfs.locale == locale)

        return self.db(q).select(sfs.ALL)

    def getSubmissionFileSettings(self, file_id):
        """
        Get settings for a given submission file.
        """
        sfs = self.db.submission_file_settings
        q = (sfs.file_id == file_id)

        return self.db(q).select(sfs.ALL)

    def getPublicationDatesByPublicationFormat(self, publication_format_id, role=None):
        """
        Get all publication dates associated with a given publication format.
        """
        pd = self.db.publication_dates
        q = (pd.publication_format_id == publication_format_id)
        if role:
            q &= (pd.role == role)

        return self.db(q).select(pd.ALL)

    def getIdentificationCodesByPublicationFormat(self, publication_format_id):
        """
        Get the identification codes (ISBN) associated with a given publication format.
        """
        ic = self.db.identification_codes
        q = (ic.publication_format_id == publication_format_id)

        return self.db(q).select(ic.ALL)

    def getRepresentativesBySubmission(self, submission_id, representative_id):
        """
        Get all representatives of a certain id for the given submission.
        """
        r = self.db.representatives
        q = ((r.submission_id == submission_id)
             & (r.representative_id_type == representative_id)
             )
        return self.db(q).select(r.ALL)

    def getMetaDataPublishedDates(self, submission_id):
        el = self.db.event_log
        assoc_type_monograph = 1048585

        q = ((el.assoc_id == submission_id)
             & (el.assoc_type == assoc_type_monograph)
             & (el.message == 'submission.event.metadataPublished')
             )

        return self.db(q).select(el.date_logged, orderby=el.date_logged)

    def getMarketsByPublicationFormat(self, publication_format_id):
        m = self.db.markets
        q = (m.publication_format_id == publication_format_id)
        return self.db(q).select(m.ALL)

    def getPluginSettingsByNameAndPress(self, plugin_name, press_id):
        ps = self.db.plugin_settings
        q = ((ps.plugin_name == plugin_name) & (ps.context_id == press_id))

        return self.db(q).select(ps.ALL)

    def getGenreById(self, genre_id):
        g = self.db.genres
        return self.db(g.genre_id == genre_id).select(g.ALL)

    def getGenresByPress(self, press_id):
        g = self.db.genres
        return self.db(g.context_id == press_id).select(g.ALL)
