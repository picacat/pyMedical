import sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo

PRINT_REGISTRATION_FORM = ['01-熱感紙掛號單', '02-11"中二刀空白掛號單']
PRINT_MODE = ['不印', '列印', '詢問', ]


# 取得印表機列表
def get_printer_list():
    printer_info = QPrinterInfo()
    printer_list = printer_info.availablePrinterNames()

    return printer_list


# 取得 text document 邊界
def get_document_margin():
    if sys.platform == 'win32':
        return 0
    else:
        return 0  # EPSON LQ-310 (driver: EPSON 24-pin series, resolution 360 * 180, paper size: US Letter


# 取得 text document
def get_document(printer, font):
    paper_size = QtCore.QSizeF()
    paper_size.setWidth(printer.width())
    paper_size.setHeight(printer.height())

    document = QtGui.QTextDocument()
    document.setDefaultFont(font)
    document.setPageSize(paper_size)

    return document


# 取得印表機
def get_printer(system_settings, printer_name):
    printer = QPrinter(QPrinter.ScreenResolution)
    printer.setPrinterName(system_settings.field(printer_name))
    printer.setPageMargins(0.08, 0.08, 0.08, 0.08, QPrinter.Inch)  # left, right, top, bottom

    return printer
