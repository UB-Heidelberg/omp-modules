"""

Prepares all data necessary to display the heiviewer and links to the reader page

"""
from gluon import URL, HTTP
from ompdal import OMPDAL, OMPItem, OMPSettings
import ompformat


def is_enabled(publication_format: OMPItem, chapter: OMPItem = None):
    pf_enabled = publication_format.settings.getLocalizedValue('useHeiViewer', '') == '1'
    if chapter:
        return pf_enabled and chapter.settings.getLocalizedValue('heiViewerChapterId', '') != ''
    return pf_enabled


def build_reader_url(publication_format: OMPItem, full_file: OMPItem, chapter: OMPItem = None):
    args = [
        full_file.attributes.submission_id,
        publication_format.attributes.publication_format_id,
        full_file.attributes.file_id
    ]
    if chapter and chapter.settings.getLocalizedValue('heiViewerChapterId', ''):
        args.append(chapter.settings.getLocalizedValue('heiViewerChapterId', ''))
    return URL(c='reader', f='index', args=args)


def load_and_check_settings(press_id, ompdal):
    plugin_settings = {}
    for row in ompdal.getPluginSettingsByNameAndPress('heiviewerompgalleyplugin', press_id):
        plugin_settings[row.setting_name] = row.setting_value

    if plugin_settings.get('enabled') != '1':
        return None
    if not plugin_settings.get('heiViewerEditionID') or not plugin_settings.get('heiViewerEditionServiceURL'):
        return None
    return plugin_settings


def build_media_mapping(file_id, submission_locale, ompdal):
    map = {}
    dependent_file_rows = ompdal.getDependentFilesBySubmissionFileId(file_id)
    for file in dependent_file_rows:
        url = str(file)
        print(file)
        map[file.file_id] = url
    for settings_row in ompdal.getSubmissionFileSettingsByIds(map.keys(), locale=submission_locale):
        if settings_row.setting_name == 'name':
            # Set the file name stored in the file settings as key of the dict
            # We want to map "filename in OMP" -> "download URL for OMP Portal"
            map[settings_row.setting_value] = map[settings_row.file_id]
            map.pop(settings_row.file_id)
    return map


def prepare_heiviewer(press_id, submission_id, publication_format_id, file_id, ompdal: OMPDAL, locale: str, settings,
                      chapter_id=None):
    # pub_format = ompdal.getPublicationFormat(publication_format_id)
    # ompdal.getPublicationFormatSettings(publication_format_id)
    submission = ompdal.getSubmission(submission_id)
    if submission is None or submission.context_id != int(press_id):
        raise HTTP(404)
    # setup Heiviewer
    plugin_settings = load_and_check_settings(press_id, ompdal)
    if not plugin_settings:
        raise HTTP(500, "heiviewer not correctly configured for press")
    submission_settings = OMPSettings(ompdal.getSubmissionSettings(submission_id))
    book_title = " ".join([submission_settings.getLocalizedValue('prefix', locale),
                           submission_settings.getLocalizedValue('title', locale)])
    url_args = [submission_id, publication_format_id, file_id]
    if chapter_id:
        url_args.append(chapter_id)
    # All template variables for the heiviewer template
    return {
        'submission_id': submission_id,
        'publication_format_id': publication_format_id,
        'editionservice_url': plugin_settings['heiViewerEditionServiceURL'],
        'edition_id': plugin_settings['heiViewerEditionID'],
        'base_url_media': URL(c='reader', f='download_image', args=[submission_id]),
        'media_mapping': build_media_mapping(file_id, submission.locale, ompdal),
        'content_id': "{}_{}_{}".format(submission_id, publication_format_id, file_id),
        'granularity': 'chapter' if chapter_id else 'text',
        'chapter_id': str(chapter_id) if chapter_id else '',
        'logo_url': plugin_settings['heiViewerLogoURL'],
        'backlink': URL(c='catalog', f='book', args=[submission_id]),
        'page_title': "{} - {}".format(book_title, settings.title),
        'locale': locale,
        'langlink_ger': URL(args=url_args, vars={'lang': 'de'}),
        'langlink_eng': URL(args=url_args, vars={'lang': 'en'})
    }
