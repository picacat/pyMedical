#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore, QtPrintSupport
from PyQt5.QtPrintSupport import QPrinter
from libs import printer_utils
from libs import system_utils
from libs import case_utils


# 健保處方箋格式5 6.5 x 2.5 inches
# 2019.07.03 明醫
class PrintReceiptInsForm5:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.ui = None
        self.medicine_set = 1

        self.printer = printer_utils.get_printer(self.system_settings, '健保醫療收據印表機')
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

    def preview(self):
        geometry = QtWidgets.QApplication.desktop().screenGeometry()

        self.preview_dialog.paintRequested.connect(self.print_html)
        self.preview_dialog.resize(geometry.width(), geometry.height())  # for use in Linux
        self.preview_dialog.setWindowState(QtCore.Qt.WindowMaximized)
        self.preview_dialog.exec_()

    def print_html(self, printing=None):
        self.current_print = self.print_html
        self.printer.setPaperSize(QtCore.QSizeF(7.2, 2.5), QPrinter.Inch)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(printer_utils.get_document_margin())
        document.setHtml(self._html())
        if printing:
            document.print(self.printer)

    def _html(self):
        if self.system_settings.field('列印處方別名') == 'Y':
            print_alias = True
        else:
            print_alias = False

        if self.system_settings.field('列印藥品總量') == 'Y':
            print_total_dosage = True
        else:
            print_total_dosage = False

        case_record = printer_utils.get_case_html_1(self.database, self.case_key, '健保')
        symptom_record = printer_utils.get_symptom_html(self.database, self.case_key, colspan=5)
        disease_record = printer_utils.get_disease(self.database, self.case_key)
        prescript_record = printer_utils.get_prescript_html(
            self.database, self.system_settings,
            self.case_key, self.medicine_set,
            '費用收據', print_alias, print_total_dosage, blocks=2)
        # prescript_record = printer_utils.get_prescript_block3_html(
        #     database.database, database.system_settings,
        #     database.massage_case_key, database.medicine_set,
        #     '費用收據', print_alias=False, print_total_dosage=True, blocks=3)
        instruction = printer_utils.get_instruction_html(
            self.database, self.system_settings, self.case_key, self.medicine_set
        )
        fees_record = printer_utils.get_ins_fees_html(self.database, self.case_key)

        html = '''
            <html>
              <body>
                <table width="95%" cellspacing="0">
                  <thead>
                    <tr>
                      <th style="text-align: left; font-size: 14px" colspan="5">
                        {clinic_name}({clinic_id}) 醫療費用收據
                      </th>
                    </tr>
                    <tr>
                      <th align="left" colspan="5">電話:{clinic_telephone} 院址:{clinic_address}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {case}
                  </tbody>  
                </table>
                {disease}
                <hr style="line-height:0.5">
                <table cellspacing="0">
                  <tbody>
                    {prescript}
                  </tbody>
                </table>
                {instruction}
              </body>
            </html>
        '''.format(
            clinic_name=self.system_settings.field('院所名稱'),
            clinic_id=self.system_settings.field('院所代號'),
            clinic_telephone=self.system_settings.field('院所電話'),
            clinic_address=self.system_settings.field('院所地址'),
            case=case_record,
            symptom=symptom_record,
            disease=disease_record,
            prescript=prescript_record,
            instruction=instruction,
            fees=fees_record,
        )

        return html

