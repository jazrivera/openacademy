from odoo import modules
from PyPDF2 import PdfFileWriter, PdfFileReader
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import GOV_LEGAL
from reportlab.pdfbase.pdfmetrics import stringWidth
from tempfile import TemporaryFile
import base64
import textwrap
import logging


_logger = logging.getLogger(__name__)


class CustomReport(object):
    def __init__(self, name, instructor, company, start_date, end_date):
        self.__base_pdf = modules.module.get_resource_path(
            'openacademy', 'reports', '2307_Jan_2018_ENCS_v3.pdf')
        _logger.debug('======================')
        _logger.debug(name)
        _logger.debug(instructor)
        _logger.debug(company)
        _logger.debug('======================')
        self._data = {
            'name': name,
            'instructor': instructor,
            'company': company,
            'start_date': start_date,
            'end_date': end_date
        }

    def print(self):
        buffer = BytesIO()
        self._p = canvas.Canvas(buffer, pagesize=GOV_LEGAL, bottomup=0)

        self._write_tin()
        self._write_start_end_date()
        self._write_payee_name()

        self._p.showPage()
        self._p.save()

        # move to the beginning of the StringIO buffer
        buffer.seek(0)
        newPdf = PdfFileReader(buffer)

        # read your existing PDF
        existingPdf = PdfFileReader(open(self.__base_pdf, 'rb'))
        # add the "watermark" (which is the new pdf) on the existing page
        page = existingPdf.getPage(0)
        page.mergePage(newPdf.getPage(0))

        output = PdfFileWriter()
        output.addPage(page)
        output.addPage(existingPdf.getPage(1))
        # finally, write "output" to a real file
        outputStream = TemporaryFile()
        output.write(outputStream)
        outputStream.seek(0)
        retval = base64.b64encode(outputStream.read())
        outputStream.close()

        return retval

    def _write_start_end_date(self):
        y = 120
        date = self._p.beginText()

        start_date = self._data['start_date'].strftime("%m%d%Y")
        end_date = self._data['end_date'].strftime("%m%d%Y")

        start_day = start_date[:2]
        start_month = start_date[2:4]
        start_year = start_date[4:]

        date.setCharSpace(8)
        date.setTextOrigin(153, y)
        date.textLines(f"{start_day}")

        date.setTextOrigin(180, y)
        date.textLines(f"{start_month}")

        date.setCharSpace(7)
        date.setTextOrigin(207, y)
        date.textLines(f"{start_year}")

        date.setCharSpace(7)
        date.setTextOrigin(400, y)
        date.textLines(f"{end_date}")

        self._p.drawText(date)

    def _write_tin(self):
        y = 152
        tin = self._p.beginText()

        tin_number = self._data['instructor']['instructor_tin']

        tin.setCharSpace(5)
        tin.setTextOrigin(210, y)
        tin.textLines(f"{tin_number[:3]}")

        tin.setCharSpace(7)
        tin.setTextOrigin(261, y)
        tin.textLines(f"{tin_number[3:6]}")

        tin.setCharSpace(7)
        tin.setTextOrigin(312, y)
        tin.textLines(f"{tin_number[6:9]}")

        tin.setCharSpace(8)
        tin.setTextOrigin(366, y)
        tin.textLines(f"{tin_number[9:]}")

        self._p.drawText(tin)

    def _write_payee_name(self):
        y = 178 # Row
        instructor = self._p.beginText()

        instructor_data = self._data['instructor']

        instructor.setCharSpace(1)
        instructor.setTextOrigin(35, y)
        instructor.textLines(f"{instructor_data['instructor_name']}")

        self._p.drawText(instructor)

    def _print_company(self):
        # Company Data
        x = 267
        tin = self._p.beginText()
        tin.setCharSpace(7)
        tin.setTextOrigin(210, x)
        tin.textLines(f"{self._data['vendor']['tin'][:3]}")
        tin.setTextOrigin(261, x)
        tin.textLines(f"{self._data['vendor']['tin'][3:6]}")
        tin.setTextOrigin(312, x)
        tin.textLines(f"{self._data['vendor']['tin'][6:9]}")
        tin.setCharSpace(8)
        tin.setTextOrigin(366, x)
        tin.textLines(f"{self._data['company']['tin'][9:]}")
        self._p.drawText(tin)

        x = 293
        name = self._p.beginText()
        name.setCharSpace(1)
        name.setTextOrigin(40, x)
        name.textLines(self._data['company']['name'])
        self._p.drawText(name)

        x = 321
        address = self._p.beginText()
        address.setCharSpace(1)
        address.setTextOrigin(40, x)
        font_name = address._fontname
        font_size = address._fontsize
        address.setFont(font_name, 9)
        address.textLines(self._data['company']['address'])
        # Zip
        address.setCharSpace(7)
        address.setTextOrigin(543, x)
        address.setFont(font_name, font_size)
        address.textLines(self._data['company']['zip'])
        self._p.drawText(address)

    def _print_signatory(self):
        # Signatory
        x = 270 - (len(self._data['signatory']['name'])/2)
        name = self._p.beginText()
        name.setCharSpace(1)
        name.setTextOrigin(x, 747)
        name.textLines(self._data['signatory']['name'])
        self._p.drawText(name)