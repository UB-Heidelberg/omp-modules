"""

Prepares all data necessary to display the heiviewer

"""
from ompdal import OMPDAL


def prepare_heiviewer(submission_id, publication_format_id, file_id, ompdal: OMPDAL):
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
        'base_url_media': '',
        'media_mapping': {},
        'granularity': '',
        'chapter_id': '',
        'logo_url': plugin_settings['heiViewerLogoURL'],
        'backlink': '',
    }
