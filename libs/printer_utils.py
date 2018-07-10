
from PyQt5.QtPrintSupport import QPrinter, QPrinterInfo

PRINT_REGISTRATION_FORM = ['01-熱感紙掛號單', '02-11"中二刀空白掛號單']
PRINT_MODE = ['不印', '列印', '詢問', ]


# 取得印表機列表
def get_printer_list():
    printer_info = QPrinterInfo()
    printer_list = printer_info.availablePrinterNames()

    return printer_list


# 取得印表機
def get_printer(system_settings, printer_name):
    # printer = QPrinter(QPrinter.HighResolution)
    printer = QPrinter(QPrinter.ScreenResolution)
    # printer = QPrinter()
    printer.setPrinterName(system_settings.field(printer_name))

    return printer
