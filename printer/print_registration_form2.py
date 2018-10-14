#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import string_utils
from libs import number_utils


# 掛號收據格式2 3"空白掛號單
# 2018.07.09
class PrintRegistrationForm2:
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
        self.font = QtGui.QFont("Noto Sans Mono", 10, QtGui.QFont.PreferQuality)

    def _set_signal(self):
        pass

    def print(self):
        self.print_html(True)
        # self.print_painter()

    def preview(self):
        geometry = QtWidgets.QApplication.desktop().screenGeometry()

        self.preview_dialog.paintRequested.connect(self.print_html)
        self.preview_dialog.resize(geometry.width(), geometry.height())  # for use in Linux
        self.preview_dialog.setWindowState(QtCore.Qt.WindowMaximized)
        self.preview_dialog.exec_()

    def print_painter(self):
        self.current_print = self.print_painter
        self.printer.setPaperSize(QtCore.QSizeF(241, 93), QPrinter.Millimeter)

        painter = QtGui.QPainter()
        painter.setFont(self.font)
        painter.begin(self.printer)
        painter.drawText(0, 10, 'print test line1 中文測試')
        painter.drawText(0, 30, 'print test line2 中文測試')
        painter.end()

    def print_html(self, printing):
        self.current_print = self.print_html
        self.printer.setPaperSize(QtCore.QSizeF(241, 93), QPrinter.Millimeter)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(printer_utils.get_document_margin())
        document.setHtml(self._html())
        if printing:
            document.print(self.printer)

    def _html(self):
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
        row = self.database.select_record(sql)[0]
        card = string_utils.xstr(row['Card'])
        if number_utils.get_integer(row['Continuance']) >= 1:
            card += '-' + string_utils.xstr(row['Continuance'])
        total_amount = (number_utils.get_integer(row['RegistFee']) +
                        number_utils.get_integer(row['SDiagShareFee']) +
                        number_utils.get_integer(row['DepositFee']))

        html = '''
            <html>
            <body>
                <p style="font-size:24px"><b>{0} 門診掛號單</b></p>
                <table cellspacing=0 cellpadding=8 style="border-width:1px; border-style: solid; border-color: darkgrey">
                    <tr>
                        <td>掛號時間</td><td>{1}</td>
                        <td>病患姓名</td><td>{2:0>6}-{3}</td>
                        <td>保險類別</td><td>{4}-{5}</td>
                    </tr>
                    <tr>
                        <td>健保卡序</td><td>{6}</td>
                        <td>掛號費</td><td style="text-align:right">{7}元</td>
                        <td>門診負擔</td><td style="text-align:right">{8}元</td>
                    </tr>
                    <tr>
                     <td>欠卡費</td><td style="text-align:right">{9}元</td>
                     <td>實收金額</td><td style="text-align:right">{10}元</td>
                     <td>經手人</td><td>{11}</td>
                    </tr>
                    <tr>
                        <td>診療室</td><td><center style="font-size:28px"><b>{12}診</b></center></td>
                        <td>就診號碼</td><td><center style="font-size:28px"><b>{13:0>3}號</b></center></td>
                        <td>蓋章</td>
                        
                    </tr>
                </table>
                本單據僅供看診叫號使用，不作報稅證明用途<br>
            </body>
            </html>
        '''.format(
            self.system_settings.field('院所名稱'),
            row['CaseDate'],
            row['PatientKey'],
            row['Name'],
            row['InsType'],
            row['Share'], card,
            row['RegistFee'],
            row['SDiagShareFee'],
            row['DepositFee'],
            total_amount,
            row['Register'],
            row['Room'],
            row['RegistNo'],
        )

        return html
