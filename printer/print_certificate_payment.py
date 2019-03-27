#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtPrintSupport import QPrinter
import datetime
import os

from libs import printer_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import patient_utils
from libs import personnel_utils
from libs import number_utils


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintCertificatePayment:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.certificate_key = args[2]

        self.ui = None

        self.printer = printer_utils.get_printer(self.system_settings, '報表印表機')
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

    def save_to_pdf(self):
        export_dir = '{0}/certificate'.format(nhi_utils.XML_OUT_PATH)
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)

        pdf_file_name = '{0}/certificate_{1}.pdf'.format(
            export_dir,
            self.certificate_key
        )
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(pdf_file_name)
        self.print_html(True)

    def print_painter(self):
        self.current_print = self.print_painter
        self.printer.setPaperSize(QtCore.QSizeF(80, 80), QPrinter.Millimeter)

        painter = QtGui.QPainter()
        painter.setFont(self.font)
        painter.begin(self.printer)
        painter.drawText(0, 10, 'print test line1 中文測試')
        painter.drawText(0, 30, 'print test line2 中文測試')
        painter.end()

    def print_html(self, printing):
        self.current_print = self.print_html
        self.printer.setPaperSize(QPrinter.A4)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(5)
        document.setHtml(self._get_html())
        if printing:
            document.print(self.printer)

    def _get_html(self):
        sql = '''
            SELECT * FROM certificate 
            WHERE
                CertificateKey = {0}
        '''.format(self.certificate_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]

        html_title = self._get_html_title(row)
        html_patient = self._get_html_patient(row)
        html_payment = self._get_html_payment()
        html_summary = self._get_html_summary(row)
        html_remark = self._get_html_remark()

        html = '''
            <html>
              <body>
                {html_title}
                {html_patient}
                {html_payment}
                {html_summary}
                {html_remark}
              </body>
            </html>
        '''.format(
            html_title=html_title,
            html_patient=html_patient,
            html_payment=html_payment,
            html_summary=html_summary,
            html_remark=html_remark,
        )

        return html

    def _get_html_title(self, row):
        html = '''
            <h1 style="text-align: center">{clinic_name} 醫療費用明細</h1>
            <table align=center width="98%" cellspacing="0">
                <tbody>
                    <tr>
                        <td><h3>編號: {certificate_key}</h3></td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            clinic_name=self.system_settings.field('院所名稱'),
            certificate_key='{0:0>8}'.format(row['CertificateKey']),
        )

        return html

    def _get_html_patient(self, row):
        patient_row = patient_utils.get_patient_row(self.database, row['PatientKey'])
        case_date = string_utils.xstr(row['StartDate'])

        if row['EndDate'] != row['StartDate']:
            case_date += ' 至 {0}'.format(string_utils.xstr(row['EndDate']))

        html = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" style="font-size: 14px; border-width: 1px; border-style: solid;">
                <tbody>
                    <tr>
                        <th bgcolor="LightGray">姓名</th>
                        <td style="text-align: center; vertical-align: middle">{name}</td>
                        <th bgcolor="LightGray">性別</th>
                        <td style="text-align: center; vertical-align: middle">{gender}</td>
                        <th bgcolor="LightGray">出生日期</th>
                        <td style="text-align: center; vertical-align: middle">{birthday}</td>
                    </tr>
                    <tr>
                        <th bgcolor="LightGray">病歷號碼</th>
                        <td style="text-align: center; vertical-align: middle">{patient_key}</td>
                        <th bgcolor="LightGray">身份證號</th>
                        <td style="text-align: center; vertical-align: middle">{id}</td>
                        <th bgcolor="LightGray">電話</th>
                        <td style="text-align: center; vertical-align: middle">{telephone}</td>
                    <tr>
                        <th bgcolor="LightGray">地址</th>
                        <td colspan="5" style="text-align: left; vertical-align: middle">{address}</td>
                    </tr>
                    <tr>
                        <th bgcolor="LightGray" style="vertical-align: middle">科別</th>
                        <td style="text-align: center; vertical-align: middle">60 中醫科</td>
                        <th bgcolor="LightGray">診療日期</th>
                        <td colspan="3" style="text-align: center; vertical-align: middle">{case_date}</td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            case_date=case_date,
            patient_key='{0:0>6}'.format(row['PatientKey']),
            name=string_utils.xstr(row['Name']),
            gender=string_utils.xstr(patient_row['Gender']),
            birthday=string_utils.xstr(patient_row['Birthday']),
            id=string_utils.xstr(patient_row['ID']),
            telephone=string_utils.xstr(patient_row['Telephone']),
            cellphone=string_utils.xstr(patient_row['Cellphone']),
            address=string_utils.xstr(patient_row['Address']),

        )

        return html

    def _get_html_payment(self):
        fees_detail = self._get_fees_detail()

        html = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" style="font-size: 14px; border-width: 1px; border-style: solid;">
                <tbody>
                    <tr bgcolor="LightGray">
                        <th>序號</th>
                        <th>門診日期</th>
                        <th>保險類別</th>
                        <th>掛號費</th>
                        <th>門診負擔</th>
                        <th>藥品負擔</th>
                        <th>自付金額</th>
                        <th>健保申報</th>
                        <th>自費金額</th>
                        <th>自付合計</th>
                    </tr>
                    {fees_detail}
                </tbody>
            </table>
        '''.format(
            fees_detail=fees_detail,
        )

        return html

    def _get_fees_detail(self):
        sql = 'SELECT * FROM certificate_items WHERE CertificateKey = {0} ORDER BY CaseDate'.format(
            self.certificate_key
        )

        rows = self.database.select_record(sql)

        total_regist_fee = 0
        total_diag_share_fee = 0
        total_drug_share_fee = 0
        total_cash_fee = 0
        total_ins_apply_fee = 0
        total_total_fee = 0
        total_cash_total = 0

        html = ''
        for row_no, row in zip(range(1, len(rows)+1), rows):
            regist_fee = number_utils.get_integer(row['RegistFee'])
            diag_share_fee = number_utils.get_integer(row['SDiagShareFee'])
            drug_share_fee = number_utils.get_integer(row['SDrugShareFee'])
            cash_fee = regist_fee + diag_share_fee + drug_share_fee
            ins_apply_fee = number_utils.get_integer(row['InsApplyFee'])
            total_fee = number_utils.get_integer(row['TotalFee'])
            cash_total = cash_fee + total_fee

            total_regist_fee += regist_fee
            total_diag_share_fee += diag_share_fee
            total_drug_share_fee += drug_share_fee
            total_cash_fee += cash_fee
            total_ins_apply_fee += ins_apply_fee
            total_total_fee += total_fee
            total_cash_total += cash_total
            if row_no % 2 > 0:
                bgcolor = '#E3E3E3'
            else:
                bgcolor = 'White'

            html += '''
                <tr>
                    <td bgcolor="{bgcolor}" style="text-align: center">{row_no}</td>
                    <td bgcolor="{bgcolor}" style="text-align: center">{case_date}</td>
                    <td bgcolor="{bgcolor}" style="text-align: center">{ins_type}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{regist_fee}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{diag_share_fee}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{drug_share_fee}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{cash_fee}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{ins_apply_fee}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{total_fee}</td>
                    <td bgcolor="{bgcolor}" style="text-align: right">{cash_total}</td>
                </tr>
            '''.format(
                row_no=row_no,
                bgcolor=bgcolor,
                case_date=string_utils.xstr(row['CaseDate'].date()),
                ins_type=string_utils.xstr(row['InsType']),
                regist_fee=string_utils.xstr(regist_fee),
                diag_share_fee=string_utils.xstr(diag_share_fee),
                drug_share_fee=string_utils.xstr(drug_share_fee),
                cash_fee=string_utils.xstr(cash_fee),
                ins_apply_fee=string_utils.xstr(ins_apply_fee),
                total_fee=string_utils.xstr(total_fee),
                cash_total=string_utils.xstr(cash_total),
            )

        html += '''
            <tr>
                <td bgcolor="LightGray" style="text-align: center" colspan=3>合計</td>
                <td style="text-align: right">{total_regist_fee}</td>
                <td style="text-align: right">{total_diag_share_fee}</td>
                <td style="text-align: right">{total_drug_share_fee}</td>
                <td style="text-align: right">{total_cash_fee}</td>
                <td style="text-align: right">{total_ins_apply_fee}</td>
                <td style="text-align: right">{total_total_fee}</td>
                <td style="text-align: right">{total_cash_total}</td>
            </tr>
        '''.format(
            total_regist_fee=string_utils.xstr(total_regist_fee),
            total_diag_share_fee=string_utils.xstr(total_diag_share_fee),
            total_drug_share_fee=string_utils.xstr(total_drug_share_fee),
            total_cash_fee=string_utils.xstr(total_cash_fee),
            total_ins_apply_fee=string_utils.xstr(total_ins_apply_fee),
            total_total_fee=string_utils.xstr(total_total_fee),
            total_cash_total=string_utils.xstr(total_cash_total),
        )

        return html

    def _get_html_summary(self, row):
        physician = string_utils.xstr(row['Doctor'])
        pyysician_cert_no = personnel_utils.get_personnel_field_value(
            self.database, physician, 'Certificate')
        president = self.system_settings.field('負責醫師')
        license_no = self.system_settings.field('院所代號')
        clinic_telephone = self.system_settings.field('院所電話')
        clinic_address = self.system_settings.field('院所地址')

        certificate_date = '{0} 年 {1} 月 {2} 日'.format(
            row['CertificateDate'].year,
            row['CertificateDate'].month,
            row['CertificateDate'].day,
        )

        html = '''
            <table align=center cellpadding="10" cellspacing="0" width="98%" style="font-size: 14px; border-width: 1px; border-style: solid;">
                <tbody>
                    <tr>
                        <td>
                            <h2>本收據可為報稅之憑證，請妥善保存，遺失恕不補發。</h2>
                            <h3>
                                主治醫師: {physician}<br>
                                醫師證書號碼: {physician_cert_no}<br>
                                院長: {president}<br>
                                開業執照號碼: {license_no}
                            </h3>
                            <h3>
                                院所電話: {clinic_telephone}<br>
                                院所地址: {clinic_address}
                            </h3>
                            <h3>
                                開立醫療費用證明日期: {certificate_date}
                            </h3>
                        </td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            certificate_date=certificate_date,
            physician=physician,
            physician_cert_no=pyysician_cert_no,
            president=president,
            license_no=license_no,
            clinic_telephone=clinic_telephone,
            clinic_address=clinic_address,
        )

        return html

    def _get_html_remark(self):
        html = '''
            <table align=center width="98%" cellspacing="0">
                <tbody>
                    <tr>
                        <td>本證明書經塗改或未加蓋本院印章者無效</td>
                    </tr>
                </tbody>  
            </table>
        '''

        return html


