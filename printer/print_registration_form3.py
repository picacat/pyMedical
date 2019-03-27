#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import string_utils
from libs import number_utils
from libs import system_utils


# 掛號收據格式3 3"空白掛號單
# 2019.02.14
class PrintRegistrationForm3:
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
        font = system_utils.get_font()
        self.font = QtGui.QFont(font, 10, QtGui.QFont.PreferQuality)

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
        self.printer.setPaperSize(QtCore.QSizeF(5, 3), QPrinter.Inch)

        painter = QtGui.QPainter()
        painter.setFont(self.font)
        painter.begin(self.printer)
        painter.drawText(0, 10, 'print test line1 中文測試')
        painter.drawText(0, 30, 'print test line2 中文測試')
        painter.end()

    def print_html(self, printing):
        self.current_print = self.print_html
        self.printer.setPaperSize(QtCore.QSizeF(5, 3), QPrinter.Inch)

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

        if self.system_settings.field('列印院所名稱') == 'Y':
            clinic_name = self.system_settings.field('院所名稱')
        else:
            clinic_name = ''

        html = '''
            <html>
            <body>
                <p style="font-size:20px"><b>{clinic_name}<br>
                電話:{clinic_telephone}</b></p>
                <br>
                <table cellspacing=16 cellpadding=8>
                    <tr>
                        <td width="30%" style="font-size: 16px; text-align: center">
                            {patient_key}
                        </td>
                        <td width="40%" style="font-size: 16px; text-align: center" colspan="3">
                            {patient_name}
                        </td>
                        <td width="30%" style="font-size: 16px; text-align: center">
                            <b>{registration_no}</br>
                        </td>
                    </tr>
                </table>
                <br>
                <table cellspacing=0 cellpadding=8>
                    <tr>
                        <td width="20%" style="text-align: center">{room}</td>
                        <td width="15%">{ins_type}</td>
                        <td width="20%" style="text-align:center">{regist_fee}</td>
                        <td width="15%" style="text-align:right">{deposit_fee}</td>
                        <td width="25%" style="text-align:center">{case_date}</td>
                    </tr>
                </table>
                <table cellspacing=0 cellpadding=8>
                    <tr>
                        <td width="20%"></td>
                        <td width="30%">卡序:{card}</td>
                        <td width="30%">部份負擔:{diag_share_fee}元</td>
                        <td width="20%">班別:{period}</td>
                    </tr>
                </table>
                本單據僅供看診叫號使用，不作報稅證明用途
            </body>
            </html>
        '''.format(
            clinic_name=clinic_name,
            clinic_telephone=self.system_settings.field('院所電話'),
            patient_key=string_utils.xstr(row['PatientKey']),
            patient_name=string_utils.xstr(row['Name']),
            registration_no=string_utils.xstr(row['RegistNo']),
            room=string_utils.xstr(row['Room']),
            ins_type=string_utils.xstr(row['InsType']),
            regist_fee=string_utils.xstr(row['RegistFee']),
            deposit_fee=string_utils.xstr(row['DepositFee']),
            case_date=string_utils.xstr(row['CaseDate'].date()),
            share=string_utils.xstr(row['Share']),
            period=string_utils.xstr(row['Period']),
            card=card,
            diag_share_fee=string_utils.xstr(row['SDiagShareFee']),
        )

        return html
