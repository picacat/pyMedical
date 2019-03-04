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
from libs import number_utils
from libs import charge_utils
from libs import date_utils
from libs import personnel_utils


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintMedicalChart:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_key = args[2]
        self.apply_date = args[3]
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
        export_dir = '{0}/emr{1}'.format(nhi_utils.XML_OUT_PATH, self.apply_date)
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)

        pdf_file_name = '{0}/chart_{1}.pdf'.format(
            export_dir,
            self.patient_key
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
        # self.printer.setOrientation(QPrinter.Landscape)
        self.printer.setPaperSize(QPrinter.A4)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(5)
        document.setHtml(self._get_html())
        if printing:
            document.print(self.printer)

    def _get_html(self):
        patient_row = patient_utils.get_patient_row(self.database, self.patient_key)
        sql = '''
            SELECT * FROM cases 
            WHERE
                InsType = "健保" AND
                PatientKey = {0}
            ORDER BY CaseDate LIMIT 1
        '''.format(self.patient_key)
        rows = self.database.select_record(sql)
        case_row = rows[0]

        init_date = patient_utils.get_init_date(self.database, self.patient_key)
        prescript_record = printer_utils.get_prescript_html(
            self.database, self.system_settings,
            case_row['CaseKey'], medicine_set=1,
            print_alias=False, print_total_dosage=False, blocks=3)
        instruction = printer_utils.get_instruction_html(
            self.database, case_row['CaseKey'], medicine_set=1
        )

        html = '''
            <html>
              <body>
                <h2 style="text-align: center">{clinic_name} 病歷表</h2>
                <table align=center width="98%" cellspacing="0">
                  <tbody>
                    <tr>
                        <td>病歷號碼: {patient_key}</td>
                        <td style="text-align: right">初診日期: {init_date}</td>
                    </tr>
                  </tbody>  
                </table>
                <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
                  <tbody>
                    <tr>
                        <th>姓名</th>
                        <td>{name}</td>
                        <th>出生日期</th>
                        <td>{birthday}</td>
                        <th>性別</th>
                        <td>{gender}</td>
                    </tr>
                    <tr>
                        <th>身份證字號</th>
                        <td>{id}</td>
                        <th>電話</th>
                        <td>{telephone}</td>
                        <th>行動電話</th>
                        <td>{cellphone}</td>
                    </tr>
                    <tr>
                        <th>地址</th>
                        <td colspan="5">{address}</td>
                    </tr>
                    <tr>
                        <th>職業</th>
                        <td>{occupation}</td>
                        <th>教育程度</th>
                        <td>{education}</td>
                        <th>婚姻狀況</th>
                        <td>{marriage}</td>
                    </tr>
                  </tbody>  
                </table>
                <table align=center cellpadding="10" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
                  <tbody>
                    <tr>
                        <th width="10%" style="vertical-align: middle">病史</th>
                        <td><br>{history}<br><br><br>
                    </tr>
                    <tr>
                        <th style="vertical-align: middle">主訴</th>
                        <td>{symptom}<br><br></td>
                    </tr>
                    <tr>
                        <th style="vertical-align: middle">四診</th>
                        <td>
                            <br>舌診: {tongue}<br>
                            <br>脈象: {pulse}<br>
                            <br>辨證: {distinct}<br>
                        </td>
                    </tr>
                    <tr>
                        <th style="vertical-align: middle">病理檢驗</th>
                        <td><br><br><br><br><br></td>
                    </tr>
                    <tr>
                        <th style="vertical-align: middle">診斷治則</th>
                        <td>
                            <br>疑似: 病名碼: {disease_code}  病名: {disease_name}<br><br><br>
                            <br>{cure}<br><br>
                        </td>
                    </tr>
                    <tr>
                        <th style="vertical-align: middle">治療處方</th>
                        <td>
                            <table align=center width="98%" cellspacing="0">
                              <tbody>
                                {prescript}
                              </tbody>  
                            </table>
                            <br>
                            <center>{instruction}</center>
                            <br><br>
                        </td>
                    </tr>
              </body>
            </html>
        '''.format(
            clinic_name=self.system_settings.field('院所名稱'),
            patient_key=string_utils.xstr(patient_row['PatientKey']),
            name=string_utils.xstr(patient_row['Name']),
            gender=string_utils.xstr(patient_row['Gender']),
            birthday=string_utils.xstr(patient_row['Birthday']),
            id=string_utils.xstr(patient_row['ID']),
            init_date=init_date,
            telephone=string_utils.xstr(patient_row['Telephone']),
            cellphone=string_utils.xstr(patient_row['Cellphone']),
            address=string_utils.xstr(patient_row['Address']),
            occupation=string_utils.xstr(patient_row['Occupation']),
            education=string_utils.xstr(patient_row['Education']),
            marriage=string_utils.xstr(patient_row['Marriage']),
            history=string_utils.get_str(patient_row['History'], 'utf-8'),
            symptom=string_utils.get_str(case_row['Symptom'], 'utf-8'),
            tongue=string_utils.get_str(case_row['Tongue'], 'utf-8'),
            pulse=string_utils.get_str(case_row['Pulse'], 'utf-8'),
            distinct=string_utils.get_str(case_row['Distincts'], 'utf-8'),
            disease_code=string_utils.xstr(case_row['DiseaseCode1']),
            disease_name=string_utils.xstr(case_row['DiseaseName1']),
            cure=string_utils.xstr(case_row['Cure']),
            prescript=prescript_record,
            instruction=instruction,
        )

        return html

