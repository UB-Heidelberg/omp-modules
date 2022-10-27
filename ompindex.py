"""

"""
import unicodedata

from gluon.html import P, DIV, A, URL, H5, SPAN, BR
from gluon import current
T = current.T


def author_names(search_initial, author_rows):
    authors = []
    initials = set()
    author_index = []
    prev_author, prev_index = '', ''
    prev = 1

    for a in author_rows:
        last_name = a['last_name'].strip()
        first_name = a['first_name'].strip()
        initial = unicodedata.normalize('NFKD', last_name)[:1].upper()
        if initial and initial != prev_index:
            a['initial'] = initial
        this_author = '{}{}'.format(last_name, first_name)
        prev = prev + 1 if prev_author == this_author else 1
        a['index'] = prev
        if search_initial and initial == search_initial:
            authors.append(a)
        elif not search_initial:
            authors.append(a)
        if initial and initial not in initials:
            author_index.append(initial)
            print("author_index initial", initial.encode("unicode_escape"))
            initials.add(initial)

        prev_author = this_author
        prev_index = initial

    buttons = DIV(_class="btn-group")
    for a in author_index:
        buttons.append(A(a, _href=URL('authors', vars=dict(searchInitial=a.encode('utf-8'))), _class="btn btn-default"))
    buttons.append(A(T('All'), _href=URL('authors'), _class="btn btn-default"))

    author_list = DIV()
    for i, a in enumerate(authors):
        if a.get('initial'):
            author_list.append(H5(a['initial']))
        pass
        book_url = URL('catalog', 'book', args=a['submission_id'])
        if a['index'] == 1:
            if a['last_name']:
                name = "{}, {}".format(a['last_name'], a['first_name'])
            else:
                name = a['first_name']
            pass
            author_list.append(A(name, ' ', _href=book_url))
        else:
            author_list.append(A(SPAN(_class="glyphicon glyphicon-new-window small"), ' ', _href=book_url))
        pass

        if i < (len(authors) - 1) and authors[i+1]['index'] == 1:
            author_list.append(BR())

    return {'author_index': buttons, 'author_list': author_list}
