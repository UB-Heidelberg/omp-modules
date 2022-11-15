from typing import Iterable

from ompdal import OMPItem
from ompformat import haveMultipleAuthors, formatName, downloadLink
from gluon import current, DIV, TD, A, URL, I

import heiviewer


def table_of_contents(submission_id: int, chapters: Iterable[OMPItem], digital_publication_formats: Iterable[OMPItem], locale: str):
    T = current.T
    table_head = DIV(
        DIV(T('Contents'), _class="chapter_cell"), _class="chapter_row table_head")
    table = DIV(table_head, _id="downloadTable")

    for pf in digital_publication_formats:
        format_name=pf.settings.getLocalizedValue('name', locale)
        if format_name != 'EPUB':
            table_head.append(DIV( TD(format_name), _class="chapter_cell"))

    display_authors=haveMultipleAuthors(chapters)

    for c in chapters:
        c_title = c.settings.getLocalizedValue('title', locale)
        c_subtitle = c.settings.getLocalizedValue('subtitle', locale)
        c_pub_id_doi = c.settings._settings.get('pub-id::doi')
        c_authors = c.associated_items.get('authors', [])
        c_files = c.associated_items.get('files', [])
        c_id = c.attributes.chapter_id
        title_cell = DIV(_class="chapter_cell")
        chapter_row = DIV(title_cell, _class="chapter_row")
        if c_authors and display_authors:
            title_cell.append(DIV(", ".join([formatName(a.settings) for a in c_authors]), _class="chapter_author"))
        if c_pub_id_doi:
            chapter_title = A(c_title, _href=URL('catalog','book',args=(submission_id, 'c'+str(c_id))))
        else:
            chapter_title = c_title
        title_cell.append(DIV(chapter_title,_class="chapter_title"))
        if c_subtitle:
            title_cell.append(DIV(c_subtitle, _class="chapter_subtitle"))

        # Build HTML for the file links
        for pf in digital_publication_formats:
            full_file = pf.associated_items.get('full_file')
            format_name = pf.settings.getLocalizedValue('name', locale)
            if format_name != 'EPUB':
                files_cell = DIV(_class="chapter_cell")
                chapter_row.append(files_cell)
                if full_file and heiviewer.is_enabled(pf, c):
                    href = heiviewer.build_reader_url(pf, full_file, c)
                    files_cell.append(DIV(A(I(_class="fa fa-html5"), _target="_target", _href=href), _class="chapter_file"))
                elif c_files and pf.attributes.publication_format_id in c_files:
                    c_file = c_files.get(pf.attributes.publication_format_id)
                    if "xml" in c_file.attributes.file_type or "html" in c_file.attributes.file_type:
                        css_class = "fa fa-html5"
                    else:
                        css_class = "fa fa-file-text-o"
                    # WARNING vgWort settings are attached to a specific file
                    # in the future they should be attached to the chapter to work with heiViewer
                    vgwPixelPublic = c_file.settings.getLocalizedValue("vgWortPublic", "")
                    onclick = "vgwPixelCall('{}')".format(vgwPixelPublic) if vgwPixelPublic else ""
                    files_cell.append(DIV(
                        A(I(_class=css_class), _target="_target", _onclick=onclick, _href=downloadLink(c_file.attributes)), _class="chapter_file"))

        table.append(chapter_row)
    return DIV(table, _class="widget")
