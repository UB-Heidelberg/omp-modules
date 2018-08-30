# -*- coding: utf-8 -*-

from decimal import Decimal
from lxml import etree, objectify
from gluon import current
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch, mm, cm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.graphics.shapes import Line, Drawing
styleSheet = getSampleStyleSheet()
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import textwrap
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

########################################################################
class PDFOrder():
    """"""

#----------------------------------------------------------------------
    def __init__(self, xml_file, pdf_file):
        """Constructor"""

        self.xml_file = xml_file
        self.pdf_file = pdf_file
        self.request = current.request


        self.xml_obj = self.getXMLObject()

#----------------------------------------------------------------------
    def coord(self, x, y, unit=1):
        """
        # http://stackoverflow.com/questions/4726011/wrap-text-in-a-table-reportlab
        Helper class to help position flowables in Canvas objects
        """
        x, y = x * unit, self.height -  y * unit
        return x, y

#----------------------------------------------------------------------
    def createPDF(self):
        """
        Create a PDF based on the XML data
        """
        # internal methods
        def drawStringUTF(x,y,text):
            self.canvas.drawString(x, y, u'{}'.format(text.encode('utf-8')))


        # global variables
        self.canvas = canvas.Canvas(self.pdf_file, pagesize=A4)
        width, self.height = A4
        styles = getSampleStyleSheet()
        xml = self.xml_obj
        pdfmetrics.registerFont(TTFont('ArialMT','Arial.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVu','DejaVuSans.ttf'))
        self.canvas.setFont("ArialMT", 10)
        self.canvas.setFont("DejaVu", 9.5)

        im_path_heiBooks = '{}{}{}'.format(self.request.env.web2py_path,'/applications/knv/static/images/','Logo_heiBOOKS.png')
        im_path_arth = '{}{}{}'.format(self.request.env.web2py_path,'/applications/knv/static/images/','Logo_Arthistoricum.png')
        im_path_prop = '{}{}{}'.format(self.request.env.web2py_path,'/applications/knv/static/images/','Logo_Propylaeum.png')
        im_path_Xasia = '{}{}{}'.format(self.request.env.web2py_path,'/applications/knv/static/images/','Logo_Crossasia.png')
        im_path_heiUP = '{}{}{}'.format(self.request.env.web2py_path,'/applications/knv/static/images/','Logo_heiUP.png')


        press_id_xml = int(xml.LS_Data.PressId)
        logo = ""
        impathdict = dict()

        impathdict = {
                     1:{'logo':(im_path_heiBooks,150,255,50,40)},
                     2:{'logo':(im_path_arth,120,262,80,40)},
                     3:{'logo':(im_path_prop,140,262,60,30)},
                     4:{'logo':(im_path_Xasia,150,262,50,30)},
                     6:{'logo':(im_path_heiUP,61,244,135,55)}
                     }

        for k,v in impathdict.items():
            if k == press_id_xml:
                logo = v.get('logo')
                self.canvas.drawImage(logo[0], logo[1] * mm, logo[2] * mm, width=logo[3] * mm, height=logo[4]*mm, preserveAspectRatio=True, mask='auto')

        #if press_id_xml == 1:
            #self.canvas.drawImage(im_path_heiBooks, 6 * cm, 25 * cm, width=20 * cm, height = 4*cm, preserveAspectRatio=True, mask='auto')
        #if press_id_xml == 2:
            #self.canvas.drawImage(im_path_arth, 8 * cm, 26 * cm, width=12 * cm, height = 3* cm, preserveAspectRatio=True, mask='auto')
        #if press_id_xml == 3:
           #self.canvas.drawImage(im_path_prop, 9 * cm, 26 * cm, width=11 * cm, height = 3* cm, preserveAspectRatio=True, mask='auto')
        #if press_id_xml == 3:
           #self.canvas.drawImage(im_path_Xasia, 10 * cm, 25.5 * cm, width=9* cm, height = 3* cm, preserveAspectRatio=True, mask='auto')
        #if press_id_xml == 6:
            #self.canvas.drawImage(im_path_heiUP, 6 * cm, 25 * cm, width=12 * cm, height  = 4*cm,  preserveAspectRatio=True, mask='auto')



        senderaddressLine1 = '<font size="6">%s</font>' % xml.SenderAddress.SenderLine1

        p = Paragraph(senderaddressLine1, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 60, mm))

        senderaddressLine2 = '<font size="6">%s</font>' % xml.SenderAddress.SenderLine2

        p = Paragraph(senderaddressLine2, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 62.5, mm))


        
        if xml.LS_Data.OrderType == "WH":
            shippingaddress = """<font size="10">
            %s<br />
            %s<br />
            %s<br />
            %s<br />
            %s %s<br />
            %s<br />
            </font>
            """ % (xml.ShippingAddress.AddressLine1, xml.ShippingAddress.AddressLine2, xml.ShippingAddress.FromPerson,
               xml.ShippingAddress.Street, xml.ShippingAddress.ZIP, xml.ShippingAddress.City, xml.ShippingAddress.Country)
        else:
            if xml.ShippingAddress.AddressLine3:
                shippingaddress = """<font size="10">
                %s<br />
                %s<br />
                %s<br />
                %s<br />
                %s %s<br />
                %s<br />
                </font>
                """ % (xml.ShippingAddress.AddressLine1, xml.ShippingAddress.AddressLine2, xml.ShippingAddress.AddressLine3,
                xml.ShippingAddress.Street, xml.ShippingAddress.ZIP, xml.ShippingAddress.City, xml.ShippingAddress.Country)
            elif xml.ShippingAddress.AddressLine2:
                shippingaddress = """<font size="10">
                %s<br />
                %s<br />
                %s<br />
                %s %s<br />
                %s<br />
                </font>
                """ % (xml.ShippingAddress.AddressLine1, xml.ShippingAddress.AddressLine2,
                xml.ShippingAddress.Street, xml.ShippingAddress.ZIP, xml.ShippingAddress.City, xml.ShippingAddress.Country)
            else:
                shippingaddress = """<font size="10">
                %s<br />
                %s<br />
                %s %s<br />
                %s<br />
                </font>
                """ % (xml.ShippingAddress.AddressLine1,
                xml.ShippingAddress.Street, xml.ShippingAddress.ZIP, xml.ShippingAddress.City, xml.ShippingAddress.Country)


        p = Paragraph(shippingaddress, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 88, mm))

        sentdate = '<font size="10">Lieferschein vom %s</font>' % xml.LS_Data.SentDate

        p = Paragraph(sentdate, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 125, mm))

        ordernumber = '<font size="10">Lieferschein Nr. %s</font>' % xml.LS_Data.OrderNumber

        p = Paragraph(ordernumber, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 129.5, mm))

        Pos = Paragraph('''
                       <b>Pos.</b>
                       ''',
                        styleSheet["BodyText"])
        Menge = Paragraph('''
                       <b>Menge</b>
                       ''',
                          styleSheet["BodyText"])
        Kurztitel = Paragraph('''
                       <b>Kurztitel</b>
                       ''',
                              styleSheet["BodyText"])
        Einband = Paragraph('''
                       <b>Einband</b>
                       ''',
                            styleSheet["BodyText"])
        ISBN = Paragraph('''
                       <b>ISBN</b>
                       ''',
                         styleSheet["BodyText"])

        KT_Split = str(xml.LS_Data.Kurztitel).split(":")
        KT_name = KT_Split[0]  + ":"

        #KT_name = Paragraph(KT_Split[0]  + ":", styleSheet['BodyText'])

        self.canvas.line(75, 441, 540, 441)

        drawStringUTF(156,429,KT_name)

        wrap_text = []
        if len(KT_Split[1]) > 45 and len(KT_Split[1]) <=90:
            wrap_text = textwrap.wrap(KT_Split[1], width=45)
            drawStringUTF(153,416,wrap_text[0])
            drawStringUTF(156,405,wrap_text[1])
        elif len(KT_Split[1]) > 90  and len(KT_Split[1]) <=120:
            wrap_text = textwrap.wrap(KT_Split[1], width=45)
            drawStringUTF(153,416,wrap_text[0])
            drawStringUTF(156,405,wrap_text[1])
            drawStringUTF(156,395,wrap_text[2])
        elif len(KT_Split[1]) > 120:
            wrap_text = textwrap.wrap(KT_Split[1], width=45)
            drawStringUTF(153,416,wrap_text[0])
            drawStringUTF(156,405,wrap_text[1])
            drawStringUTF(156,395,wrap_text[2])
            drawStringUTF(156,385,wrap_text[3])
        else:
            drawStringUTF(153,417,KT_Split[1])

        data = []

        data.append([Pos, Menge, Kurztitel, Einband, ISBN])
        #data.append([xml.LS_Data.Position, xml.LS_Data.Copies, KT_name, xml.LS_Data.Einband, xml.LS_Data.EAN])
        data.append(["1", xml.LS_Data.Copies, "" , xml.LS_Data.Einband, xml.LS_Data.EAN])

        t = Table(data, colWidths=(1.2 * cm, 1.6 * cm, 8.5 * cm, 2 * cm, 4 * cm), rowHeights=(0.6*cm, 0.4*cm))
        t.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), "TOP"),
            ('ALIGN', (0,0), (-1,-1), "LEFT"),
            ('INNERGRID', (0,0), (-1,-1), 0.25, colors.transparent),
            ('BOX', (0,0), (-1,-1), 0.25, colors.transparent)
            ]))

        t.wrapOn(self.canvas, width, self.height)
        t.drawOn(self.canvas, *self.coord(25, 145, mm))

        txt = '<font size="9">Bitte nicht buchen, Rechnung folgt.</font>'
        p = Paragraph(txt, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 240, mm))

        txt = '<font size="9">%s <a href="mailto:heiUP@ub.uni-heidlberg.de"><u><font color="blue">heiUP@ub.uni-heidelberg.de</font></u></a>, Tel.: +49 6221 542383.</font>' %('Bei Rückfragen wenden Sie sich bitte an')
        p = Paragraph(txt, styles["Normal"])
        p.wrapOn(self.canvas, width, self.height)
        p.drawOn(self.canvas, *self.coord(25, 255, mm))
        self.canvas.save()

#----------------------------------------------------------------------
    def getXMLObject(self):
        """
        Open the XML document and return an lxml XML document
        """
        with open(self.xml_file) as f:
            xml = f.read()

        return objectify.fromstring(xml)
