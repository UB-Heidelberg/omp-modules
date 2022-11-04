"""

Prepares all data necessary to display the heiviewer

"""
from gluon import URL
from ompdal import OMPDAL


def prepare_heiviewer(submission_id, publication_format_id, file_id, ompdal: OMPDAL, chapter_id=None):
    # pub_format = ompdal.getPublicationFormat(publication_format_id)
    # ompdal.getPublicationFormatSettings(publication_format_id)
    submission = ompdal.getSubmission(submission_id)
    # setup Heiviewer
    plugin_settings = {}
    for row in ompdal.getPluginSettingsByNameAndPress('heiviewerompgalleyplugin', submission.context_id):
        plugin_settings[row.setting_name] = row.setting_value

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
    }
