import io
import urllib.parse

from django.shortcuts import render, get_object_or_404
from django.views.generic import CreateView
from django.http import HttpResponse, Http404

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .models import Generator

def chunks(lst, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Create your views here.
class GeneratorCreateView(CreateView):
    model = Generator
    fields = {'text_field'}

import re
import json
import time
start_t = time.time()
#from kanji_info import get_kanji_data

## UNICODE BLOCKS ##
kanji_block = r'[㐀-䶵一-鿋豈-頻]'


def extract_unicode_block(unicode_block, string):
    ''' extracts and returns all texts from a unicode block from string argument.
        Note that you must use the unicode blocks defined above, or patterns of similar form '''
    return re.findall( unicode_block, string)

def load_json(name):
    with open('sheetgen/json/' + name + '.json', 'r') as f:
        return json.load(f)


kanji_lookup = load_json("kanji_lookup")
trans_lookup = load_json("trans_lookup")
font_lookup = load_json("font_lookup")

USER = "kokimame"
TESTFILE = "sheetgen/testdoc.txt"
TRANSFILE = "sheetgen/translation_results.txt".format(USER)


FONTS = [
    ('sheetgen/fonts/AozoraMinchoRegular.ttf', 'Hiragino'),
    ('sheetgen/fonts/ShirakawaKoukotsu.ttf', 'Bone'),
    ('sheetgen/fonts/ShirakawaTenbun.ttf', 'Tenbun'),
    ('sheetgen/fonts/KanjiStrokeOrders.ttf', 'Stroke'),
    ('sheetgen/fonts/times.ttf', 'Times'),
    ('sheetgen/fonts/timesi.ttf', 'Times-Italic')
]
for font_data in FONTS:
    path, name = font_data
    pdfmetrics.registerFont(TTFont(name, path))

GRAY = colors.Color(red=(150 / 255), green=(150 / 255), blue=(150 / 255), alpha=0.8)
LIGHTGRAY = colors.Color(red=(180 / 255), green=(180 / 255), blue=(180 / 255), alpha=0.3)
NAVY = colors.Color(red=(0 / 255), green=(0 / 255), blue=(128 / 255))
BLACK = colors.Color(0, 0, 0)
RED30 = colors.Color(.9, 0, 0, alpha=0.3)
GREEN30 = colors.Color(0, .7, 0, alpha=0.3)



def export(request):
    if request.method != 'GET':
        raise Http404



    kanjis = extract_unicode_block(kanji_block, request.GET['text_field'])
    # Cannot use set operation to remove duplication because the order matters
    # kanji_list = list(set(kanjis))
    kanji_list = []
    for kanji in kanjis:
        if kanji not in kanji_list:
            kanji_list.append(kanji)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="joytan_kanji.pdf"'

    buffer = io.BytesIO()

    can = canvas.Canvas(buffer, pagesize=A4)
    can.setTitle("Joytan Kanji Sheets")

    ncol, nrow = 8, 16
    if kanji_list == []:
        kanji_list = ['' * ncol]

    chunked_list = [l for l in chunks(kanji_list, nrow)]
    for i, entries in enumerate(chunked_list):
        make_a_table(can, ncol, nrow, entries, "%d of %d" % (i+1, len(chunked_list)))
    can.save()

    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    return response


def make_a_table(canvas, ncol, nrow, entries, str_index):
    width, height = A4
    cell_size = 16 * mm

    table_data = []
    for i in range(nrow):
        row = []
        for j in range(ncol):
            if 1 < j < ncol - 1:
                row.append('')
            else:
                try:
                    row.append(entries[i])
                except:
                    row.append('')
        table_data.append(row)

    kanji_tbl_style = []
    kanji_tbl_style.append(('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black))
    kanji_tbl_style.append(('BOX', (0, 0), (-1, -1), 0.25, colors.black))
    for i in range(ncol):
        kanji_tbl_style.append(('ALIGN', (i, 0), (i, -1), 'CENTER'))
        kanji_tbl_style.append(('VALIGN', (i, 0), (i, -1), 'BOTTOM'))
        kanji_tbl_style.append(('FONT', (i, 0), (i, -1), 'Stroke', 36))
        if i == ncol - 1:
            kanji_tbl_style.append(('TEXTCOLOR', (i, 0), (i, -1), NAVY))
        elif i < 2:
            kanji_tbl_style.append(('TEXTCOLOR', (i, 0), (i, -1), GRAY))

    kanji_tbl = Table(table_data, colWidths=cell_size, rowHeights=cell_size)
    kanji_tbl.setStyle(TableStyle(kanji_tbl_style))
    kanji_tbl.wrapOn(canvas, width, height)
    table_x, table_y = 12*mm, 21*mm
    kanji_tbl.drawOn(canvas, table_x, table_y)

    kanji_info = []
    info_tbl_style = []
    info_style = ParagraphStyle(
        name='Info',
        fontName='Hiragino',
        fontSize=7,
    )
    for i in range(nrow):
        try:
            text = Paragraph(kanji_lookup[entries[i]], info_style)
            kanji_info.append([text])
        except:
            kanji_info.append([''])
    info_tbl_style.append(('VALIGN', (0, 0), (-1, -1), 'TOP'))
    info_tbl = Table(kanji_info, colWidths=50*mm, rowHeights=cell_size)
    info_tbl.setStyle(TableStyle(info_tbl_style))
    info_tbl.wrapOn(canvas, width, height)
    info_tbl.drawOn(canvas, table_x + cell_size * ncol, table_y)


    for i in range(nrow):
        coord_trans = (table_x + cell_size * ncol + 50*mm, table_y + cell_size * i)
        if i % 2 == 1:
            char_x = table_x + cell_size * ncol + 5 * mm
        else:
            char_x = table_x + cell_size * ncol + 22*mm
        coord_char = (char_x, table_y + cell_size * i + 2*mm)

        try:
            kanji = entries[nrow - i - 1]
            canvas.setFillColor(BLACK)
            canvas.setFont('Times-Italic', 8)
            canvas.drawRightString(*coord_trans, trans_lookup[kanji])

            if kanji in font_lookup['bone']:
                canvas.setFillColor(GREEN30)
                canvas.setFont('Bone', 55)
            elif kanji in font_lookup['tenbun']:
                canvas.setFillColor(RED30)
                canvas.setFont('Tenbun', 55)
            else:
                continue
            canvas.drawString(*coord_char, kanji)
        except:
            pass

    sep_x = table_x + cell_size * ncol + 0.5*mm
    canvas.setLineWidth(0.1 * mm)
    canvas.line(sep_x, table_y, sep_x, table_y + cell_size * nrow)
    canvas.setFillColor(LIGHTGRAY)
    rect_x, rect_y = table_x, height - 16*mm
    canvas.roundRect(rect_x, rect_y, 70*mm, 10*mm, 1*mm, fill=1, stroke=0)
    canvas.setFont('Hiragino', 12)
    canvas.setFillColor(BLACK)
    canvas.drawString(rect_x + 2*mm, rect_y +3*mm, "Joytan Kanji Practice | 漢字練習帳")

    # Name with underline
    canvas.setLineWidth(0.1 * mm)
    canvas.setFillColor(BLACK)
    canvas.setFont('Hiragino', 10)
    name_x, name_y = width - 90*mm, height - 14*mm
    canvas.drawString(name_x, name_y, "名前：")
    canvas.line(name_x, name_y - 2*mm, name_x + 70*mm, name_y - 2*mm)

    # Left footer
    canvas.setFont('Helvetica-Bold', 10)
    coord_msg = (table_x, table_y - 5*mm)
    canvas.drawString(*coord_msg, "Support our project: https://kokimame.github.io/joytan/")
    coord_index = (table_x, table_y - 12*mm)
    canvas.drawString(*coord_index, "%s | © Joytan" % str_index)

    # Right footer
    coord_l1 = (width - 20*mm, table_y - 5 * mm)
    coord_l2 = (width - 20*mm, table_y - 10 * mm)
    coord_l3 = (width - 20*mm, table_y - 13 * mm)
    canvas.setFont('Hiragino', 9)
    canvas.drawRightString(*coord_l1, "【部首】/画数/学年 オンヨミ くんよみ")
    canvas.setFont('Hiragino', 8)
    canvas.drawRightString(*coord_l2, "【radical】/#stroke/grade Onyomi(Katakana) Kunyomi (Hiragana)")
    canvas.setFont('Times-Italic', 7)
    canvas.drawRightString(*coord_l3, "* Rough kanji-wise translation")

    # Additional lines
    canvas.setDash([0.1 * mm, 1.2 * mm])
    canvas.setLineCap(1)

    # Dotted vertical lines
    for i in range(ncol):
        x = table_x + cell_size / 2 + cell_size * i
        canvas.line(x, table_y, x, table_y + nrow * cell_size)
    # Dotted horizontal  lines
    for i in range(nrow):
        trans_y = table_y + cell_size / 2 + cell_size * i
        canvas.line(table_x, trans_y, table_x + ncol * cell_size, trans_y)
    # Separation between the Info panel
    for i in range(nrow + 1):
        x = table_x + cell_size * ncol
        trans_y = table_y + cell_size * i
        canvas.line(x, trans_y, x + 50*mm, trans_y)

    canvas.showPage()
