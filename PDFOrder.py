# -*- coding: utf-8 -*-

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

LOCALE = 'de_DE'

styleSheet = getSampleStyleSheet()
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
from os.path import join
import sys
from gluon.http import HTTP
import importlib

importlib.reload(sys)

# sys.setdefaultencoding('utf-8')
from ompdal import OMPDAL
#'Bitte nicht buchen, Rechnung folgt.',

class PDFOrder():
    ADDRESS_FIELDS = ['adresszeile1', 'adresszeile2', 'adresszeile3', 'strasse_und_nr']
    IMG_PATH = 'applications/knv/static/images'
    PRESS_CONFIGURATON = {
        1: ('Logo_heiBOOKS.png', 150, 255, 50, 40),
        2: ('Logo_Arthistoricum.png', 120, 262, 80, 40),
        3: ('Logo_Propylaeum.png', 140, 262, 60, 30),
        4: ('Logo_Crossasia.png', 150, 262, 50, 30),
        6: ('Logo_heiUP.png', 61, 244, 135, 55)
    }
    FOOTER = [
              'Bei Rückfragen wenden Sie sich bitte an <a '
              'href="mailto:heiUP@ub.uni-heidlberg.de"><u><font '
              'color="blue">heiUP@ub.uni-heidelberg.de</font></u></a>, '
              'Tel.: +49 6221 542383.'
              ]
    FONTS = [('ArialMT', 'Arial.ttf', 10), ('DejaVu', 'DejaVuSans.ttf', 9.5)]
    TABLE_STYLE = TableStyle(
        [('VALIGN', (0, 0), (-1, -1), "TOP"),
         ('ALIGN', (0, 0), (-1, -1), "LEFT"),
         ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.transparent),
         ('BOX', (0, 0), (-1, -1), 0.25, colors.transparent)
         ])
    TABLE_HEADERS = ['Pos.', 'Menge', 'Kurztitel', 'Einband', 'ISBN', 'Preis']
    WIDTH, HEIGHT = A4


    def __init__(self, pdf_file, request, record, db, conf):

        self.IM_PATH = join(request.env.web2py_path, PDFOrder.IMG_PATH)
        self.record = record.as_dict()


        self.submission_id = int(self.record.get('submission_id'))

        self.db = db

        self.ompdal = OMPDAL(db, conf)

        self.press_id = self.ompdal.getSubmission(self.submission_id)['context_id']

        self.styles = getSampleStyleSheet()

        self.canvas = canvas.Canvas(pdf_file, pagesize=A4)

        self.setFont(self.canvas)


    def coordinates(self, x, y, unit=1):

        x, y = x * unit, PDFOrder.HEIGHT - y * unit
        return x, y


    def drawUTFText(self, canvas, x, y, text):

        canvas.drawString(x, y, u'{}'.format(text))


    def drawParagraph(self, text, size, style, top_margin, left_margin=25):

        p = Paragraph('<font size="{}">{}</font>'.format(size, text),
                      self.styles[style])
        p.wrapOn(self.canvas, PDFOrder.WIDTH, PDFOrder.HEIGHT)
        p.drawOn(self.canvas, *self.coordinates(left_margin, top_margin, mm))


    def createPDF(self):

        self.drawLogo()

        self.drawSenderAddress()

        self.drawReceiverAddress()

        self.drawDelliveryNote()

        self.drawOrderSignareOfCustomer()

        self.canvas.line(75, 447, 565, 447)

        self.createTable()

        self.createShortTitleFlowable()

        self.createFooter()

        self.canvas.save()


    def createFooter(self):
        customer_notice = ''
        invoice_check = self.record.get('invoice_check')
        if self.record.get('customer_notice'):
            customer_notice = textwrap.wrap(str(self.record.get('customer_notice')), 120)

        for i, line in enumerate(customer_notice):
            self.drawParagraph(line, 9, "Normal", 230 - len(customer_notice) * 5 + 5 * i)
        if invoice_check:
            invc = textwrap.wrap("Bitte nicht buchen, Rechnung folgt.", 120)
            for i, line in enumerate(invc):
                self.drawParagraph(line, 9, "Normal", 245 - len(invc) * 5 + 5 * i)
        for i, part in enumerate(PDFOrder.FOOTER):
            self.drawParagraph(part, 9, "Normal", 250 + 10 * i)


    def createShortTitleFlowable(self):

        for i, line in enumerate(self.getShortTitle()):
            self.drawUTFText(self.canvas, 150, 434 - 10 * i, line)


    def createTable(self):

        data = []

        data.append([self.createTableTH(val) for val in PDFOrder.TABLE_HEADERS])
        data.append(["1", self.record.get('copies'), "",
                     self.record.get('format'), self.getISBN(),
                     self.getPrice()])

        t = Table(data, colWidths=(
            1.2 * cm, 1.6 * cm, 7.0 * cm, 2 * cm, 4 * cm, 2 * cm),
                  rowHeights=(0.6 * cm, 0.6 * cm))

        t.setStyle(PDFOrder.TABLE_STYLE)

        t.wrapOn(self.canvas, PDFOrder.WIDTH, PDFOrder.HEIGHT)

        t.drawOn(self.canvas, *self.coordinates(25, 145, mm))


    def getAuthorList(self, submission_id, chapter_id=0):
        contribs = []
        aut = self.db.authors
        ugs = self.db.user_group_settings
        sca = self.db.submission_chapter_authors
        if chapter_id > 0:
            contribs = self.db(sca.chapter_id == chapter_id).select(sca.author_id, distinct=True).as_list()
        else:
            contribs = self.db((aut.submission_id == submission_id) & (aut.user_group_id == ugs.user_group_id) & (ugs.setting_name == 'abbrev') & (ugs.setting_value != "CA")).select(aut.author_id,
                                                                                                                                                                                      distinct=True).as_list()

        authors = []
        for contrib in contribs:
            author = {}
            role = self.db((ugs.user_group_id == aut.user_group_id) & (aut.author_id == contrib["author_id"]) & (
                    ugs.setting_name == "name")).select(ugs.setting_value)
            if role:
                author["role"] = role.first().as_dict().get("setting_value")

            author_settings = self.ompdal.getAuthorSettings(contrib["author_id"]).as_list()
            for setting in author_settings:
                author[setting['setting_name']] = setting["setting_value"]
            authors.append(author)
        return authors


    def getShortTitle(self):
        result = []
        authorsList = self.getAuthorList(self.submission_id)
        lastNames = [i.get('familyName') for i in authorsList]

        if len(lastNames) > 4:
            lastNames = lastNames[0:4]
            lastNames[3] += ' et al'

        authors = '/'.join(lastNames)

        submission_settings = self.ompdal.getSubmissionSettings(
            self.submission_id).find(lambda row: row.locale == LOCALE).find(
            lambda row: row.setting_name == 'title')
        if len(submission_settings) == 0:
            raise HTTP(403, 'Title not found')

        result += textwrap.wrap(authors, 40)
        result += textwrap.wrap(submission_settings.first()['setting_value'], 40)

        return result


    def createTableTH(self, content):

        return Paragraph('<b>%s</b>' % content, styleSheet["BodyText"])


    def drawOrderSignareOfCustomer(self):
        if self.record.get('item_number'):
            self.drawParagraph('{} {}'.format('Bestellzeichen Kunde:', self.record.get('item_number')), 10, "Normal", 129.5, left_margin=140)


    def drawDelliveryNote(self):

        self.drawParagraph(
            '{} {}'.format('Lieferschein vom',
                           self.record.get('sent_date')),
            10, "Normal", 125)
        self.drawParagraph(
            '{} {}-{}'.format('Lieferschein Nr. ub-pub-',
                              self.record.get('curyear'),
                              str(self.record.get('order_number')).rjust(5,
                                                                         "0")),
            10, "Normal", 129.5)


    def drawSenderAddress(self):

        self.drawParagraph(self.record.get('abs_zeile1'), 6, "Normal", 60)
        self.drawParagraph(self.record.get('abs_zeile2'), 6, "Normal", 62.5)


    def drawReceiverAddress(self):
        address = []
        for line in PDFOrder.ADDRESS_FIELDS:
            if len(str(self.record.get(line))) > 0 and self.record.get(line) is not None:
                address.append(str(self.record.get(line)))

        address.append(' '.join([self.record.get(l) for l in ['laendercode', 'plz', 'ort'] if len(str(self.record.get(l))) > 0]))

        for i, line in enumerate(address):
            self.drawParagraph(line, 10, "Normal", 70 + i * 4)


    def setFont(self, canvas):

        for f in PDFOrder.FONTS:
            pdfmetrics.registerFont(TTFont(f[0], f[1]))
            canvas.setFont(f[0], f[2])


    def drawLogo(self):

        for k, v in PDFOrder.PRESS_CONFIGURATON.items():
            press_id = self.ompdal.getSubmission(int(self.submission_id))['context_id']
            if k == int(press_id):
                self.canvas.drawImage(join(self.IM_PATH, v[0]), v[1] * mm,
                                      v[2] * mm, width=v[3] * mm,
                                      height=v[4] * mm,
                                      preserveAspectRatio=True, mask='auto')


    def getISBN(self):
        pf_id = self.getPublicationFormatID(self.submission_id)
        ics = self.ompdal.getIdentificationCodesByPublicationFormat(pf_id) if pf_id else None
        isbn = ics.first().get('value') if ics else ''
        return isbn


    def getPublicationFormatID(self, submission_id):
        pfs = self.ompdal.getPublicationFormatByName(submission_id,
                                                     self.record.get('format'))
        pf_id = pfs.first().get('publication_format_id') if pfs else None
        return pf_id


    def getPrice(self):
        pf_id = self.getPublicationFormatID(self.submission_id)
        markets = self.ompdal.getMarketsByPublicationFormat(pf_id)

        if markets:
            price = float(markets.first().get('price', 0).replace(',', '.'))
        else:
            raise HTTP(403, 'Bitte geben Sie den Preis für {}  ein'.format(self.record.get('format')))

        copies = self.record.get('copies', 1)
        copies = int(copies) if str(copies).isdigit() else None
        currency_rate = int(self.record.get('currency_rate', 1.0))

        total = '{:5.2f}'.format(price * copies * currency_rate) if copies and price else ''

        if self.record.get('price_formattng') == 'Komma':
            total = total.replace('.', '.')

        return '{} {}'.format(total, self.record.get("currency", "€"))
