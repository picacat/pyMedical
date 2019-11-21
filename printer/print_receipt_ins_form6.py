#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore, QtPrintSupport
from PyQt5.QtPrintSupport import QPrinter
import sys
from libs import printer_utils
from libs import system_utils
from libs import string_utils
from libs import number_utils


# 健保收據格式3 4.5 x 3 inches
# 2018.10.09
class PrintReceiptInsForm6:
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
        if sys.platform == 'win32':
            font = '新細明體'
        else:
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

    def _get_prescript_html(self, row):
        if self.system_settings.field('列印處方別名') == 'Y':
            print_alias = True
        else:
            print_alias = False

        if self.system_settings.field('列印藥品總量') == 'Y':
            print_total_dosage = True
        else:
            print_total_dosage = False

        case_record = printer_utils.get_case_html_3(
            self.database, self.case_key, '健保', self.medicine_set,
        )
        disease_record = printer_utils.get_disease(self.database, self.case_key)
        prescript_record = printer_utils.get_prescript_html2(
            self.database, self.system_settings,
            self.case_key, self.medicine_set,
            '費用收據', print_alias, print_total_dosage, blocks=2)
        instruction = printer_utils.get_instruction_html2(
            self.database, self.system_settings, self.case_key, self.medicine_set
        )

        prescript_html = '''
            <table cellspacing="0">
              <thead>
                <tr>
                  <th style="text-align: center" colspan="3">
                    <u>處方暨費用收據</u>
                  </th>
                </tr>
              </thead>
              <tbody>
                {case}
              </tbody>  
            </table>
            <hr style="line-height:0.5">
            <table cellspacing="0">
              <tbody>
                {prescript}
              </tbody>
            </table>
            <hr style="line-height:0.5">
            {instruction}
            適應症: {disease_name1}<br> 
            副作用: 本處方於醫學文獻中尚無副作用之記載<br> 
            院所:{clinic_id} {clinic_name}<br>
            院址:{clinic_address} 電話: {clinic_telephone}<br>
            * 本收據可為報稅之憑證, 請妥善保存, 遺失恕不補發
        '''.format(
            clinic_name=self.system_settings.field('院所名稱'),
            clinic_id=self.system_settings.field('院所代號'),
            clinic_telephone=self.system_settings.field('院所電話'),
            clinic_address=self.system_settings.field('院所地址'),
            case=case_record,
            disease=disease_record,
            disease_name1=string_utils.xstr(row['DiseaseName1']),
            prescript=prescript_record,
            instruction=instruction,
        )

        return prescript_html

    def _get_ins_fees_html(self, row):
        regist_fee = number_utils.get_integer(row['RegistFee'])
        diag_share_fee = number_utils.get_integer(row['SDiagShareFee'])
        drug_share_fee = number_utils.get_integer(row['SDrugShareFee'])
        deposit_fee = number_utils.get_integer(row['DepositFee'])
        diag_fee = number_utils.get_integer(row['DiagFee'])
        drug_fee = number_utils.get_integer(row['InterDrugFee'])
        pharmacy_fee = number_utils.get_integer(row['PharmacyFee'])
        acupuncture_fee = number_utils.get_integer(row['AcupunctureFee'])
        massage_fee = number_utils.get_integer(row['MassageFee'])
        ins_total_fee = number_utils.get_integer(row['InsTotalFee'])
        ins_apply_fee = number_utils.get_integer(row['InsApplyFee'])

        fees_html = '''
            <table width="98%" cellspacing="0">
              <tbody>
                <tr>
                  <td></td>
                  <td></td>
                </tr>
                <tr>
                  <td></td>
                  <td></td>
                </tr>
                <tr>
                  <td></td>
                  <td></td>
                </tr>
                <tr>
                  <td>掛號金額</td>
                  <td align="right">{regist_fee}</td>
                </tr>
                <tr>
                  <td>門診負擔</td>
                  <td align="right">{diag_share_fee}</td>
                </tr>
                <tr>
                  <td>藥品負擔</td>
                  <td align="right">{drug_share_fee}</td>
                </tr>
                <tr>
                  <td>負擔合計</td>
                  <td align="right">{total_share_fee}</td>
                </tr>
                <tr>
                  <td>欠卡金額</td>
                  <td align="right">{total_share_fee}</td>
                </tr>
                <tr>
                  <td>實收金額</td>
                  <td align="right">{total_fee}</td>
                </tr>
                <tr>
                  <td>診察費用</td>
                  <td align="right">{diag_fee}</td>
                </tr>
                <tr>
                  <td>內服藥費</td>
                  <td align="right">{drug_fee}</td>
                </tr>
                <tr>
                  <td>藥事服務</td>
                  <td align="right">{pharmacy_fee}</td>
                </tr>
                <tr>
                  <td>處置費用</td>
                  <td align="right">{treat_fee}</td>
                </tr>
                <tr>
                  <td>健保合計</td>
                  <td align="right">{ins_total_fee}</td>
                </tr>
                <tr>
                  <td>健保申請</td>
                  <td align="right">{ins_apply_fee}</td>
                </tr>
              </tbody>
            </table>
            健保申報非一點一元給付
        '''.format(
            regist_fee=regist_fee,
            diag_share_fee=diag_share_fee,
            drug_share_fee=drug_share_fee,
            total_share_fee=diag_share_fee + drug_share_fee,
            deposit_fee=deposit_fee,
            total_fee=regist_fee + diag_share_fee + drug_share_fee + deposit_fee,
            diag_fee=diag_fee,
            drug_fee=drug_fee,
            pharmacy_fee=pharmacy_fee,
            treat_fee=acupuncture_fee + massage_fee,
            ins_total_fee=ins_total_fee,
            ins_apply_fee=ins_apply_fee,
        )

        return fees_html

    def _html(self):
        sql = '''
            SELECT * FROM cases 
            WHERE
                CaseKey = {0}
        '''.format(self.case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]

        prescript_html = self._get_prescript_html(row)
        fees_html = self._get_ins_fees_html(row)

        html = '''
            <html>
              <body>
                <table width="100%" cellspacing="0">
                  <tbody>
                    <tr>
                      <td width="80%">
                        {prescript_html}
                      </td>
                      <td width="20%">
                        {fees_html}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </body>
            </html>
        '''.format(
            prescript_html=prescript_html,
            fees_html=fees_html,
        )

        return html

