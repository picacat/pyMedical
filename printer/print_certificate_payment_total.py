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


# 費用明細總表
# 2018.09.26
class PrintCertificatePaymentTotal:
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
        export_dir = '{0}/certificate'.format(nhi_utils.get_dir(self.system_settings, '申報路徑'))
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
        html_payment = self._get_html_payment(row)
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
            <h1 style="text-align: center">{clinic_name} 醫療費用收據</h1>
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
        case_list = self._get_case_list(row)
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
                        <th bgcolor="LightGray">門診期間</th>
                        <td colspan="3" style="text-align: center; vertical-align: middle">{case_date} 共{case_time}次</td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            case_date=case_date,
            case_time=len(case_list),
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

    def _get_case_list(self, row):
        sql = '''
            SELECT CaseDate FROM certificate_items
            WHERE
                CertificateKey = {certificate_key}
            ORDER BY CaseDate
        '''.format(
            certificate_key=self.certificate_key,
        )

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            rows = self._get_rows_by_script(row)

        case_list = []
        for row in rows:
            case_list.append(string_utils.xstr(row['CaseDate'].date()))

        return case_list

    def _get_html_payment(self, row):
        ins_type = string_utils.xstr(row['InsType'])
        fees_detail = self._get_fees_detail(ins_type)
        certificate_fee = number_utils.get_integer(row['CertificateFee'])
        if ins_type in ['健保']:
            certificate_fee = 0

        html = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" 
                   style="font-size: 18px; border-width: 1px; border-style: solid;">
                <tbody>
                    <tr>
                        <td>
                            <b>醫療費用明細表</b><br><br>
                            茲收到 {name} 君於本院就診醫療費用共NT${total_cash_fee}元整, 費用明細如下:<br>
                            <div align="left" style="margin-left: 60px">
                                掛號金額: {regist_fee}<br>
                                門診負擔: {diag_share_fee}<br>
                                藥品負擔: {drug_share_fee}<br>
                                自費金額: {total_fee}<br>
                                處置費用: 0<br>
                                其他費用: 0<br>
                                診斷證明: {certificate_fee}<br>
                            </div>
                        </td>
                    </tr>
                    <tr>
                        <td>
                            <b>健保給付點數表</b><br><br>
                            {name} 君於本院就診期間 {start_date} 至 {end_date}, 健保醫療給付點數共{ins_apply_fee}點整<br>
                            給付點數明細如下:<br>
                            <div align="left" style="margin-left: 60px">
                                門診診察費: {diag_fee}<br>
                                健保內服藥: {drug_fee}<br>
                                藥事服務費: {pharmacy_fee}<br>
                                針灸治療費: {acupuncture_fee}<br>
                                傷科治療費: {massage_fee}<br>
                                脫臼治療費: {dislocate_fee}<br>
                            </div><br>
                            扣除門診負擔NT${diag_share_fee}及藥品負擔NT${drug_share_fee}後, 實付淨額為{ins_apply_fee}點整<br>
                            (以上所列點數僅供參考)
                        </td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            name=string_utils.xstr(row['Name']),
            start_date=string_utils.xstr(row['StartDate']),
            end_date=string_utils.xstr(row['EndDate']),
            total_cash_fee=fees_detail['total_cash_fee'],
            regist_fee=fees_detail['total_regist_fee'],
            diag_share_fee=fees_detail['total_diag_share_fee'],
            drug_share_fee=fees_detail['total_drug_share_fee'],
            total_fee=fees_detail['total_total_fee']-certificate_fee,
            certificate_fee=certificate_fee,
            diag_fee=fees_detail['total_diag_fee'],
            drug_fee=fees_detail['total_drug_fee'],
            pharmacy_fee=fees_detail['total_pharmacy_fee'],
            acupuncture_fee=fees_detail['total_acupuncture_fee'],
            massage_fee=fees_detail['total_massage_fee'],
            dislocate_fee=fees_detail['total_dislocate_fee'],
            ins_apply_fee=fees_detail['total_ins_apply_fee']
        )

        return html

    def _get_fees_detail(self, ins_type):
        sql = 'SELECT * FROM certificate_items WHERE CertificateKey = {0} ORDER BY CaseDate'.format(
            self.certificate_key
        )

        rows = self.database.select_record(sql)

        fees_detail = {
            'total_cash_fee': 0,
            'total_regist_fee': 0,
            'total_diag_share_fee': 0,
            'total_drug_share_fee': 0,
            'total_diag_fee': 0,
            'total_drug_fee': 0,
            'total_pharmacy_fee': 0,
            'total_acupuncture_fee': 0,
            'total_massage_fee': 0,
            'total_dislocate_fee': 0,
            'total_total_fee': 0,
            'total_ins_apply_fee': 0,
        }

        for row in rows:
            regist_fee = number_utils.get_integer(row['RegistFee'])
            diag_share_fee = number_utils.get_integer(row['SDiagShareFee'])
            drug_share_fee = number_utils.get_integer(row['SDrugShareFee'])
            total_fee = number_utils.get_integer(row['TotalFee'])
            if ins_type in ['健保']:
                total_fee = 0

            diag_fee = number_utils.get_integer(row['DiagFee'])
            drug_fee = number_utils.get_integer(row['InterDrugFee'])
            pharmacy_fee = number_utils.get_integer(row['PharmacyFee'])
            acupuncture_fee = number_utils.get_integer(row['AcupunctureFee'])
            massage_fee = number_utils.get_integer(row['MassageFee'])
            dislocate_fee = number_utils.get_integer(row['DislocateFee'])
            ins_apply_fee = number_utils.get_integer(row['InsApplyFee'])

            fees_detail['total_regist_fee'] += regist_fee
            fees_detail['total_diag_share_fee'] += diag_share_fee
            fees_detail['total_drug_share_fee'] += drug_share_fee
            fees_detail['total_diag_fee'] += diag_fee
            fees_detail['total_drug_fee'] += drug_fee
            fees_detail['total_pharmacy_fee'] += pharmacy_fee
            fees_detail['total_acupuncture_fee'] += acupuncture_fee
            fees_detail['total_massage_fee'] += massage_fee
            fees_detail['total_dislocate_fee'] += dislocate_fee

            fees_detail['total_total_fee'] += total_fee
            fees_detail['total_cash_fee'] += regist_fee + diag_share_fee + drug_share_fee + total_fee
            fees_detail['total_ins_apply_fee'] += ins_apply_fee

        return fees_detail

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
                                開立醫療費用收據日期: {certificate_date}
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


