#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore, QtPrintSupport
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import system_utils
from libs import string_utils
from libs import number_utils


# 自費收據格式3 5 x 3 inches
# 2018.10.09
class PrintReceiptSelfForm3:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.medicine_set = args[3]
        self.ui = None

        self.printer = printer_utils.get_printer(self.system_settings, '自費醫療收據印表機')
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
        self.font = QtGui.QFont(font, 8, QtGui.QFont.PreferQuality)

    def _set_signal(self):
        pass

    def print(self):
        self.print_html(True)

    def preview(self):
        geometry = QtWidgets.QApplication.desktop().screenGeometry()

        self.preview_dialog.paintRequested.connect(self.print_html)
        self.preview_dialog.resize(geometry.width(), geometry.height())  # for use in Linux
        self.preview_dialog.setWindowState(QtCore.Qt.WindowMaximized)
        self.preview_dialog.exec_()

    def print_html(self, printing=None):
        self.current_print = self.print_html
        self.printer.setPaperSize(QtCore.QSizeF(4.5, 3), QPrinter.Inch)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(printer_utils.get_document_margin())
        document.setHtml(self._html())
        if printing:
            document.print(self.printer)

    def _html(self):
        case_record = printer_utils.get_case_html_2(self.database, self.case_key, '自費')
        prescript_record = printer_utils.get_prescript_html(
            self.database, self.system_settings,
            self.case_key, self.medicine_set,
            print_alias=False, print_total_dosage=True, blocks=2)
        fees_record = printer_utils.get_self_fees_html(self.database, self.case_key)
        remark = '<hr>* 本收據可為報稅之憑證, 請妥善保存, 遺失恕不補發'

        prescript_html = '''
            <table cellspacing="0">
              <thead>
                <tr>
                  <th align="left">處方名稱</th>
                  <th align="right">劑量</th>
                  <th align="right">總量</th>
                  <th></th>
                  <th align="left">處方名稱</th>
                  <th align="right">劑量</th>
                  <th align="right">總量</th>
                </tr>
              </thead>
              <tbody>
                {prescript}
              </tbody>
            </table>
        '''.format(
            prescript=prescript_record,
        )

        if self.medicine_set is None:
            prescript_html = '無處方'

        if self.medicine_set is None or self.medicine_set >= 3:
            fees_record = ''
            remark = ''

        html = '''
            <html>
              <body>
                <table width="98%" cellspacing="0">
                  <thead>
                    <tr>
                      <th style="text-align: left" colspan="4">
                        {clinic_name}({clinic_id}) 醫療費用收據
                      </th>
                    </tr>
                    <tr>
                      <th style="text-align: left; font-size: 9px" colspan="4">
                        電話:{clinic_telephone} 院址:{clinic_address}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {case}
                  </tbody>  
                </table>
                <hr>
                {prescript_html}
                <table width="100%" cellspacing="0">
                  <tbody>
                    {fees}
                  </tbody>
                </table>
                {remark}
              </body>
            </html>
        '''.format(
            clinic_name=self.system_settings.field('院所名稱'),
            clinic_id=self.system_settings.field('院所代號'),
            clinic_telephone=self.system_settings.field('院所電話'),
            clinic_address=self.system_settings.field('院所地址'),
            case=case_record,
            prescript_html=prescript_html,
            fees=fees_record,
            remark=remark,
        )

        return html

