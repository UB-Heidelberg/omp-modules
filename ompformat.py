# -*- coding: utf-8 -*-
'''
Copyright (c) 2015 Heidelberg University Library
Distributed under the GNU GPL v3. For full terms see the file
LICENSE.md
'''

from gluon.html import URL, I
from gluon import current
from datetime import datetime
from locale import getlocale, setlocale, getdefaultlocale, LC_TIME
from os.path import exists, join
from re import findall
from urllib import urlopen

ONIX_INPUT_DATE_MAP = {
    "00": "%Y%m%d",    #Year month day (default).
    "01": "%Y%m",    #Year and month.
    "02": "%Y%m%W",    #Year and week number.
    "03": "%Y%w",    #Year and quarter (Q = 1, 2, 3, 4). – datetime can't represent the quarter so we pretend it's the weekday (and do not output it)
    "04": "%Y%w",    #Year and season (S = 1, 2, 3, 4, with 1 = “Spring”). – datetime can't represent the season so we pretend it's the weekday (and do not output it)
    "05": "%Y",    #Year.
    "13": "Y%m%d%H%M",    #Exact time. Use ONLY when exact times with hour/minute precision are relevant. By default, time is local. Alternatively, the time may be suffixed with an optional ‘Z’ for UTC times, or with ‘+’ or ‘-’ and an hhmm timezone offset from UTC. Times without a timezone are ‘rolling’ local times, times qualified with a timezone (using Z, + or -) specify a particular instant in time.
    "14": "Y%m%d%H%M%S",    #Exact time. Use ONLY when exact times with second precision are relevant. By default, time is local. Alternatively, the time may be suffixed with an optional ‘Z’ for UTC times, or with ‘+’ or ‘-’ and an hhmm timezone offset from UTC. Times without a timezone are ‘rolling’ local times, times qualified with a timezone (using Z, + or -) specify a particular instant in time.
    "20": "%Y%m%d",    #Year month day (Hijri calendar).
    "21": "%Y%m",    #Year and month (Hijri calendar).
    "25": "%Y",    # Year (Hijri calendar).
#    "06": "YYYYMMDDYYYYMMDD",    #Spread of exact dates. – not supported
#    "07": "YYYYMMYYYYMM",    #Spread of months. – not supported
#    "08": "YYYYWWYYYYWW",    #Spread of week numbers. – not supported
#    "09": "YYYYQYYYYQ",    #Spread of quarters. – not supported
#    "10": "YYYYSYYYYS",    #Spread of seasons. – not supported
#    "11": "YYYYYYYY",    #Spread of years. – not supported  
}

ONIX_OUTPUT_DATE_MAP = {
    "00": "%x",         #Locale’s appropriate date representation.
    "01": "%B %Y",
    "02": "%B %Y",
    "03": "%Y",
    "04": "%Y",
    "05": "%Y",
    "13": "%x", #Locale’s appropriate date representation.
    "14": "%x", #Locale’s appropriate date representation.
    "20": "%x AH",  #Locale’s appropriate date representation.
    "21": "%Y AH",
    "25": "%Y AH",
}

ONIX_DATE_ROLES = {
    "01": current.T('Publication date'),    #Nominal date of publication.
    "02": current.T('Embargo date') ,   #If there is an embargo on retail sales in this market before a certain date, the date from which the embargo is lifted and retail sales are permitted.
    "09": current.T('Public announcement date'),    #Date when a new product may be announced to the general public.
    "10": current.T('Trade announcement date'),    #Date when a new product may be announced for trade only.
    "11": current.T('Date of first publication'),    #Date when the work incorporated in a product was first published.
    "12": current.T('Last reprint date'),    #Date when a product was last reprinted.
    "13": current.T('Out-of-print / deletion date'),    #Date when a product was (or will be) declared out-of-print or deleted.
    "16": current.T('Last reissue date'),    #Date when a product was last reissued.
    "19": current.T('Publication date of print counterpart'),    #Date of publication of a printed book which is the print counterpart to a digital edition.
    "20": current.T('Date of first publication in original language'),    #Year when the original language version of work incorporated in a product was first published (note, use only when different from code 11).
    "21": current.T('Forthcoming reissue date'),    #'Date when a product will be reissued.
    "22": current.T('Expected availability date after temporary withdrawal'),    #'Date when a product that has been temporary withdrawn from sale or recalled for any reason is expected to become available again, eg after correction of quality or technical issues.
    "23": current.T('Review embargo date'),    #Date from which reviews of a product may be published eg in newspapers and magazines or online. Provided to the book trade for information only: newspapers and magazines are not expected to be recipients of ONIX metadata.
    "25": current.T('Publisher’s reservation order deadline'),    #Latest date on which an order may be placed with the publisher for guaranteed delivery prior to the publication date. May or may not be linked to a special reservation or pre-publication price.
    "26": current.T('Forthcoming reprint date'),    #Date when a product will be reprinted.
    "27": current.T('Preorder embargo date'),    #Earliest date a retail ‘preorder’ can be placed (where this is distinct from the public announcement date). In the absence of a preorder embargo, advance orders can be placed as soon as metadata is available to the consumer (this would be the public announcement date, or in the absence of a public announcement date, the earliest date metadata is available to the retailer). 
}

def formatCitation(title, subtitle, authors, editors, date_published, location, press_name, doi, locale,
                   series_name="", series_pos="", max_contrib=3, date_first_published=None):
    """
    Format a citation in CML.
    """
    cit, et_al, edt = "", "", ""
    if editors:
        contributors = list(editors)
        if len(editors) == 1:
            edt = " "+current.T.translate('(Ed.)', {})
        else:
            edt = " "+current.T.translate('(Eds.)', {})
    else:
        contributors = list(authors)
    if len(contributors) > max_contrib:
        contributors = contributors[:1]
        et_al = " et al."
    if len(contributors) == 1:
        cit = formatName(contributors[0].attributes, reverse=True)
    else:
        cit = " , ".join([formatName(c.attributes, reverse=True) for c in contributors[:-1]])
        if contributors:
            cit = " ".join(
            [cit, current.T.translate('and', {}), formatName(contributors[-1].attributes, reverse=True)])

    cit = "".join([cit, et_al, edt])+": "
    cit += title
    if subtitle:
        cit += ": "+subtitle

    #cit += ", "+location+": "+press_name + ", " + dateToStr(date_published, locale, "%Y")
    cit += ", {}: {}, {}".format(location,press_name,dateToStr(date_published, locale, "%Y"))
    if date_first_published and date_first_published.year != date_published.year:
        cit += dateToStr(date_first_published, locale, " (%Y)")

    if series_name and series_pos:
        cit += " ({}, {})".format(series_name, formatSeriesPosition(series_pos))
    cit += "."
    if doi:
        cit += " DOI: "
    return cit


def formatSeriesPosition(series_pos):
    if series_pos[:1].isdigit():
        # Add translated Vol. for numerical series position
        return " ".join((current.T.translate('Vol.', {}), series_pos))
    else:
        # Add translation of prefix from series_pos string
        parts = series_pos.split(' ')
        return " ".join((current.T(parts[0], lazy=False), parts[1]))


def formatContributors(contributors=[], max_contributors=3, et_al=True):
    """
    Format a list of contributors.
    """
    if len(contributors) > max_contributors:
        # Only output the first contributor
        res = formatName(contributors[0].attributes)
        if et_al:
            res += " et al."
    else:
        res = ", ".join([formatName(c.attributes) for c in contributors])
    return res

def formatName(author_row, reverse=False):
    """
    Format author names for citations.
    """
    if not reverse:
        return " ".join([author_row.first_name, author_row.middle_name, author_row.last_name])
    else:
        return "{}, {}".format(author_row.last_name, " ".join([author_row.first_name, author_row.middle_name]).strip())
    
def formatONIXDateWithText(date_row, locale="de_DE", f_out=""):
    """
    Format different types of ONIX publication date info with an introductory phrase.
    """
    date = dateFromRow(date_row)
    if date == datetime(1, 1, 1):
        formatter = current.T('Published %(date)s.')
        date = date_row.date
        
    if not f_out:
        f_out = ONIX_OUTPUT_DATE_MAP.get(date_row.date_format, "%x")
    
    if (date-datetime.now()).days > 0:
        # publication date in the future
        formatter = current.T("To be published %(date_str)s. ## "+f_out)
    else:
        # publication date in the past
        formatter = current.T("Published %(date_str)s. ## "+f_out)

    return formatter % dict(date_str = dateToStr(date, locale, f_out))
    
def formatONIXDate(date_row, locale="de_DE", f_out=""):
    """
    Format different types of ONIX publication date info.
    """
    date = dateFromRow(date_row)
    if date == datetime(1, 1, 1):
        # unknown input date format, return date as string
        return date_row.date
    if not f_out:
        f_out = ONIX_OUTPUT_DATE_MAP.get(date_row.date_format, "%x")

    return dateToStr(date, locale, f_out)

def dateToStr(date, locale="de_DE", f_out="%x"):
    # save current locale
    c_locale = getlocale(LC_TIME)
    try:
        setlocale(LC_TIME, (locale, 'UTF-8'))
    except:
        setlocale(LC_TIME, getdefaultlocale())
    try:
        date = datetime.strftime(date, f_out)
    except:
        pass
    # reset locale
    setlocale(LC_TIME, c_locale)
    
    return date

def dateFromRow(date_row):
    """
    Convert OMP publication date to datetime object.
    """
    if not date_row:
        return None
    f_inp = ONIX_INPUT_DATE_MAP.get(date_row.date_format, None)
    if f_inp:
        try:
            return datetime.strptime(date_row.date, f_inp)
        except ValueError as e:
            raise ValueError('date_row.date: ' + date_row.date + ' does not match format' + f_inp)
    else:
        return datetime(1, 1, 1)

def downloadLink(request, file_row, url="", vgwPublicCode=None, vgwServer=None):
    """
    Generate download link from file info.
    """
    file_type = file_row.original_file_name.split('.').pop().strip().lower()
    file_name_items = [file_row.submission_id,
                       file_row.genre_id,
                       file_row.file_id,
                       file_row.revision,
                       file_row.file_stage,
                       file_row.date_uploaded.strftime('%Y%m%d'),
                       ]
    file_name = '-'.join([str(i) for i in file_name_items])+'.'+file_type
    
    if file_type == 'xml' or file_type == 'html':
        op = 'index'
    else:
        op = 'download'
    
    redirect = ""
    if vgwPublicCode:
        if not vgwServer:
            vgwServer = "http://vg07.met.vgwort.de/na"
        # check, if server is available
        if urlopen(vgwServer).getcode() == 200:
            redirect = join(vgwServer, vgwPublicCode)+"?l="+url
    return redirect+URL(
        a=request.application,
        c='reader',
        f=op,
        args=[file_row.submission_id, file_name],
        )
    
def coverImageLink(request, press_id, submission_id):
    """
    Check, if cover image for a given submission exists, and build link.
    """
    cover_image = ''
    path = request.folder+join('static', 'files', 'presses', str(press_id), 'monographs', str(submission_id), 'simple', 'cover')+'.'
    for t in ['jpg','png','gif']:
        if exists(path+t):
            cover_image = URL(request.application, 'static', join('files', 'presses', str(press_id), 'monographs', str(submission_id), 'simple', 'cover')+'.'+t)
    return cover_image

def getSeriesImageLink(request, press_id, image):
    """
    Build series image link.
    """
    series_image = ''
    try:
        series_image = URL(request.application, 'static', join('files', 'presses', str(press_id), 'series', image[4:].split(';')[1].split('"')[1]))
    except:
        pass
    
    return series_image

def haveMultipleAuthors(chapters):
    """
    Check, whether a list of chapters features different authors or whether all
    chapters were written by the same author (used to decide whether to display
    all author names or not).
    """
    authors = []
    for c in chapters:
        authors.append(tuple([a.attributes.author_id for a in c.associated_items.get('authors', [])]))
    if len(set(authors)) == 1:
        return False
    else:
        return True

def seriesPositionCompare(s1, s2):
    p1 = s1.attributes.series_position
    p2 = s2.attributes.series_position
    # Cannot compare to empty value
    if not p1 or not p2:
        return 0
    try:
        # Try casting to integer
        p1 = float(p1)
        p2 = float(p2)
    except ValueError:
        try:
            # Try finding an integer substring
            p1 = int(findall("[0-9]+", str(p1)).pop())
            p2 = int(findall("[0-9]+", str(p2)).pop())
        except IndexError:
            # No integer value found – keep position values as is for comparison
            pass
    
    if p1 > p2:
        return 1
    elif p2 > p1:
        return -1
    else:
        return 0

