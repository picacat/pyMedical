#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import string_utils
from libs import number_utils
from libs import system_utils


# 掛號收據格式4 2.5 x 3 inches 熱感紙
# 2019.05.06
class PrintRegistrationForm4:
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
        self.return_card = None

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
        font = system_utils.get_font()
        self.font = QtGui.QFont(font, 10, QtGui.QFont.PreferQuality)

    def _set_signal(self):
        pass

    def print(self, return_card=None):
        self.return_card = return_card
        self.print_html(True)

    def preview(self, return_card=None):
        self.return_card = return_card
        geometry = QtWidgets.QApplication.desktop().screenGeometry()

        self.preview_dialog.paintRequested.connect(self.print_html)
        self.preview_dialog.resize(geometry.width(), geometry.height())  # for use in Linux
        self.preview_dialog.setWindowState(QtCore.Qt.WindowMaximized)
        self.preview_dialog.exec_()

    def print_painter(self):
        self.current_print = self.print_painter
        self.printer.setPaperSize(QtCore.QSizeF(2.5, 3), QPrinter.Inch)

        painter = QtGui.QPainter()
        painter.setFont(self.font)
        painter.begin(self.printer)
        painter.drawText(0, 10, 'print test line1 中文測試')
        painter.drawText(0, 30, 'print test line2 中文測試')
        painter.end()

    def print_html(self, printing):
        self.current_print = self.print_html
        self.printer.setPaperSize(QtCore.QSizeF(2.5, 3), QPrinter.Inch)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(5)
        document.setHtml(self._html())
        if printing:
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
                掛號費: {7}元 門診負擔: {8}元<br>
                <center style="font-size:24px">{9}診 {10:0>3}號</b></center><br>
                <center>本單據僅供叫號，不作報稅證明</center>
            </body>
            </html>
        '''.format(
            self.system_settings.field('院所名稱'),
            row['CaseDate'], row['PatientKey'], row['Name'],
            row['InsType'], row['TreatType'], card, row['RegistFee'], row['SDiagShareFee'],
            row['Room'], row['RegistNo']
        )

        return html
