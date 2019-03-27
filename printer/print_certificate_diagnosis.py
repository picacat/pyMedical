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


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintCertificateDiagnosis:
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
        html_detail = self._get_html_detail(row)
        html_remark = self._get_html_remark()

        html = '''
            <html>
              <body>
                {html_title}
                {html_patient}
                {html_detail}
                {html_remark}
              </body>
            </html>
        '''.format(
            html_title=html_title,
            html_patient=html_patient,
            html_detail=html_detail,
            html_remark=html_remark,
        )

        return html

    def _get_html_title(self, row):
        html = '''
            <h1 style="text-align: center">{clinic_name} 診斷證明書<br>CERTIFICATE OF DIAGNOSIS</h1>
            <table align=center width="98%" cellspacing="0">
                <tbody>
                    <tr>
                        <td><h3>編號 <font size="3">Certificate No.</font> {certificate_key}</h3></td>
                    </tr>
                </tbody>  
            </table>
        '''.format(
            certificate_key='{0:0>8}'.format(row['CertificateKey']),
            clinic_name=self.system_settings.field('院所名稱'),
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
                        <th bgcolor="LightGray">姓名<br><font size="3">Name</font></th>
                        <td style="text-align: center; vertical-align: middle">{name}</td>
                        <th bgcolor="LightGray">性別<br><font size="3">Gender</font></th>
                        <td style="text-align: center; vertical-align: middle">{gender}</td>
                        <th bgcolor="LightGray">出生日期<br><font size="3">Date of Birth</font></th>
                        <td style="text-align: center; vertical-align: middle">{birthday}</td>
                    </tr>
                    <tr>
                        <th bgcolor="LightGray">病歷號碼<br><font size="3">Chart No.</font></th>
                        <td style="text-align: center; vertical-align: middle">{patient_key}</td>
                        <th bgcolor="LightGray">身份證號<br><font size="3">ID No.</font></th>
                        <td style="text-align: center; vertical-align: middle">{id}</td>
                        <th bgcolor="LightGray">電話<br><font size="3">Telephone</font></th>
                        <td style="text-align: center; vertical-align: middle">{telephone}</td>
                    <tr>
                        <th bgcolor="LightGray">地址<br><font size="3">Address</font></th>
                        <td colspan="5" style="text-align: left; vertical-align: middle">{address}</td>
                    </tr>
                    <tr>
                        <th bgcolor="LightGray" style="vertical-align: middle">科別<br><font size="3">Speciality</font></th>
                        <td style="text-align: center; vertical-align: middle">60 中醫科</td>
                        <th bgcolor="LightGray">診療日期<br><font size="3">Date of Examination</font></th>
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

    def _get_html_detail(self, row):
        certificate_date = '{0} 年 {1} 月 {2} 日'.format(
            row['CertificateDate'].year,
            row['CertificateDate'].month,
            row['CertificateDate'].day,
        )
        physician = string_utils.xstr(row['Doctor'])
        physician_cert_no = personnel_utils.get_personnel_field_value(
            self.database, physician, 'Certificate')
        president = self.system_settings.field('負責醫師')
        license_no = self.system_settings.field('院所代號')
        clinic_telephone = self.system_settings.field('院所電話')
        clinic_address = self.system_settings.field('院所地址')

        html = '''
            <table align=center cellpadding="10" cellspacing="0" width="98%" style="font-size: 14px; border-width: 1px; border-style: solid;">
                <tbody>
                    <tr>
                        <th bgcolor="LightGray" style="text-align: left; vertical-align: middle">診斷 <font size="3">Diagnosis</font></th>
                    </tr>
                    <tr>
                        <td>{diagnosis}<br><br><br><br></td>
                    </tr>
                    <tr>
                        <th bgcolor="LightGray" style="text-align: left; vertical-align: middle">醫囑 <font size="3">Doctor's Comment</font></th>
                    </tr>
                    <tr>
                        <td>{doctor_comment}<br><br><br><br></td>
                    </tr>
                    <tr>
                        <td>
                            <h3>
                                以上病人經本院(所)醫師診斷屬實特予證明<br>
                                <font size="3">
                                    This certificate is invalid without the seal of the Hospital Director.
                                </font>
                            </h3>
                            <h3>
                                主治醫師 <font size="3">Physician</font>: {physician}<br>
                                醫師證書號碼 <font size="3">Physician Certificate No.</font>: {physician_cert_no}<br>
                                院長 <font size="3">President</font>: {president}<br>
                                開業執照號碼 <font size="3">License Number</font>: {license_no}
                            </h3>
                            <h3>
                                院所電話 <font size="3">Telephone</font>: {clinic_telephone}<br>
                                院所地址 <font size="3">Address</font>: {clinic_address}
                            </h3>
                            <h3>
                                開立診斷證明書日期 <font size="3">Certificate Date</font>: {certificate_date}
                            </h3>
                        </td>
                    </tr>
                </tbody>
            </table>
        '''.format(
            certificate_date=certificate_date,
            diagnosis=string_utils.get_str(row['Diagnosis'], 'utf-8'),
            doctor_comment=string_utils.get_str(row['DoctorComment'], 'utf-8'),
            physician=physician,
            physician_cert_no=physician_cert_no,
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
                    <tr>
                        <td>本證明書訴訟無效</td>
                    </tr>
                </tbody>  
            </table>
        '''

        return html


