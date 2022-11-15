"""

Prepares all data necessary to display the heiviewer and links to the reader page

"""
from gluon import URL
from ompdal import OMPDAL, OMPItem, OMPSettings


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


def prepare_heiviewer(submission_id, publication_format_id, file_id, ompdal: OMPDAL, locale: str, settings,
                      chapter_id=None):
    # pub_format = ompdal.getPublicationFormat(publication_format_id)
    # ompdal.getPublicationFormatSettings(publication_format_id)
    submission = ompdal.getSubmission(submission_id)
    # setup Heiviewer
    plugin_settings = {}
    for row in ompdal.getPluginSettingsByNameAndPress('heiviewerompgalleyplugin', submission.context_id):
        plugin_settings[row.setting_name] = row.setting_value
    submission_settings = OMPSettings(ompdal.getSubmissionSettings(submission_id))
    book_title = " ".join([submission_settings.getLocalizedValue('prefix', locale),
                           submission_settings.getLocalizedValue('title', locale)])
    return {
        'submission_id': submission_id,
        'publication_format_id': publication_format_id,
        'editionservice_url': plugin_settings['heiViewerEditionServiceURL'],
        'edition_id': plugin_settings['heiViewerEditionID'],
        'base_url_media': URL(c='reader', f='download_image', args=[submission_id]),
        'media_mapping': {},
        'content_id': "{}_{}_{}".format(submission_id, publication_format_id, file_id),
        'granularity': 'chapter' if chapter_id else 'text',
        'chapter_id': str(chapter_id) if chapter_id else '',
        'logo_url': plugin_settings['heiViewerLogoURL'],
        'backlink': URL(c='catalog', f='book', args=[submission_id]),
        'page_title': "{} - {}".format(book_title, settings.title)
    }
