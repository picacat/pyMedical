#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import string_utils
from libs import number_utils


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintRegistrationForm1:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.ui = None

        self.printer = printer_utils.get_printer(self.system_settings, '門診掛號單印表機')
        self.preview_dialog = QtPrintSupport.QPrintPreviewDialog(self.printer)
        self.current_print = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.font = QtGui.QFont("Noto Sans Mono", 10, QtGui.QFont.Normal)

    def _set_signal(self):
        pass

    def print(self):
        self.print_html()
        # self.print_painter()

    def preview(self):
        self.print()
        self.preview_dialog.paintRequested.connect(self.current_print)
        self.preview_dialog.exec_()

    def print_painter(self):
        self.current_print = self.print_painter
        self.printer.setPaperSize(QtCore.QSizeF(80, 80), QPrinter.Millimeter)
        self.printer.setFullPage(True)
        self.printer.setPageMargins(0.08, 0.08, 0.08, 0.08, QPrinter.Inch)  # left, right, top, bottom

        painter = QtGui.QPainter()
        painter.setFont(self.font)
        painter.begin(self.printer)
        painter.drawText(0, 10, 'print test line1 中文測試')
        painter.drawText(0, 30, 'print test line2 中文測試')
        painter.end()

    def print_html(self):
        self.current_print = self.print_html
        self.printer.setPaperSize(QtCore.QSizeF(80, 80), QPrinter.Millimeter)
        self.printer.setFullPage(True)
        self.printer.setPageMargins(0.08, 0.08, 0.08, 0.08, QPrinter.Inch)  # left, right, top, bottom

        paper_size = QtCore.QSizeF()
        paper_size.setWidth(self.printer.width())
        paper_size.setHeight(self.printer.height())

        document = QtGui.QTextDocument()
        document.setDefaultFont(self.font)
        document.setPageSize(paper_size)
        document.setDocumentMargin(10)
        document.setHtml(self._html())
        document.print(self.printer)

    def _html(self):
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
        row = self.database.select_record(sql)[0]
        card = string_utils.xstr(row['Card'])
        if number_utils.get_integer(row['Continuance']) >= 1:
            card += '-' + string_utils.xstr(row['Continuance'])
        html = '''
            <html>
            <body>
                <center style="font-size:20px"><b>{0}</b></center>
                <center style="font-size:18px"><b>門診掛號單</b></center><br>
                掛號時間: {1}<br>
                病患姓名: {2:0>6} - {3}<br>
                保險類別: {4} - {5}<br>
                健保卡序: {6}<br>
                掛號費: {7} 門診負擔: {8} 欠卡費: {9}<br>
                <center style="font-size:28px"><b>{10}診 {11:0>3}號</b></center>
                <center>本單據僅供看診叫號使用，不作報稅證明用途</center><br>
            </body>
            </html>
        '''.format(
            self.system_settings.field('院所名稱'), row['CaseDate'], row['PatientKey'], row['Name'],
            row['InsType'], row['TreatType'], card, row['RegistFee'], row['SDiagShareFee'], row['DepositFee'],
            row['Room'], row['RegistNo']
        )

        return html
