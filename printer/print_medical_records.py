#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtCore, QtPrintSupport, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from PyQt5.QtPrintSupport import QPrinter
import datetime
import os

from libs import printer_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import patient_utils


# 掛號收據格式1 80mm * 80mm 熱感紙
# 2018.07.09
class PrintMedicalRecords:
    # 初始化
    def __init__(self, parent=None, *args):
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_key = args[2]
        self.sql = args[3]
        self.start_date = args[4]
        self.end_date = args[5]
        self.ui = None

        if self.start_date is not None:
            apply_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S')
            self.apply_date = '{0:0>3}{1:0>2}'.format(
                apply_date.year-1911,
                apply_date.month
            )
        else:
            self.apply_date = None

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
        xml_dir = nhi_utils.get_dir(self.system_settings, '申報路徑')
        export_dir = '{0}/emr{1}'.format(xml_dir, self.apply_date)
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)

        pdf_file_name = '{0}/case_{1}.pdf'.format(
            export_dir,
            self.patient_key
        )
        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(pdf_file_name)
        self.print_html(True)

    def save_to_pdf_by_dialog(self):
        xml_dir = nhi_utils.get_dir(self.system_settings, '申報路徑')
        export_dir = '{0}'.format(xml_dir)
        if not os.path.exists(export_dir):
            os.mkdir(export_dir)

        if self.patient_key is not None:
            pdf_file_name = '{0}/病歷號{1}病歷表.pdf'.format(
                export_dir,
                self.patient_key
            )
        else:
            pdf_file_name = '病歷表.pdf'

        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self.parent, "匯出實體病歷表",
            pdf_file_name,
            "所有檔案 (*);;pdf檔 (*.pdf)", options = options
        )
        if not file_name:
            return

        self.printer.setOutputFormat(QPrinter.PdfFormat)
        self.printer.setOutputFileName(file_name)
        self.print_html(True)
        system_utils.show_message_box(
            QMessageBox.Information,
            '匯出完成',
            '<font size="4" color="red"><b>實體病歷pdf檔案已匯出完成</b></font>',
            '',
        )

    def print_html(self, printing):
        self.current_print = self.print_html
        # database.printer.setOrientation(QPrinter.Landscape)
        self.printer.setPaperSize(QPrinter.A4)

        document = printer_utils.get_document(self.printer, self.font)
        document.setDocumentMargin(5)
        document.setHtml(self._get_html())
        if printing:
            document.print(self.printer)

    def _get_html(self):
        patient_row = patient_utils.get_patient_row(self.database, self.patient_key)
        medical_record_html = self.get_medical_record_html()

        if patient_row is None:
            html = medical_record_html
        else:
            init_date = patient_utils.get_init_date(self.database, self.patient_key)
            telephone = string_utils.xstr(patient_row['Telephone'])
            if telephone == '':
                telephone = string_utils.xstr(patient_row['Cellphone'])

            html = '''
                <html>
                  <body>
                    <h3 style="text-align: center">{clinic_name} 病歷表</h3>
                    <table width="98%" cellspacing="0">
                      <tbody>
                        <tr>
                            <td>病歷號: {patient_key}</td>
                            <td>姓名: {name}</td>
                            <td>性別: {gender}</td>
                            <td>生日: {birthday}</td>
                            <td>身份證: {id}</td>
                        </tr>
                        <tr>
                            <td>初診日: {init_date}</td>
                            <td>電話: {telephone}</td>
                            <td colspan="3">地址: {address}</td>
                        </tr>
                      </tbody>  
                    </table>
                    <hr>
                    {medical_record}
                    <h4>院所名稱: ({clinic_id}) {clinic_name} 電話: {clinic_telephone} 院址: {clinic_address}</h4>
                  </body>
                </html>
            '''.format(
                clinic_name=self.system_settings.field('院所名稱'),
                clinic_id=self.system_settings.field('院所代號'),
                clinic_telephone=self.system_settings.field('院所電話'),
                clinic_address=self.system_settings.field('院所地址'),
                medical_record=medical_record_html,
                patient_key=string_utils.xstr(patient_row['PatientKey']),
                name=string_utils.xstr(patient_row['Name']),
                gender=string_utils.xstr(patient_row['Gender']),
                birthday=string_utils.xstr(patient_row['Birthday']),
                id=string_utils.xstr(patient_row['ID']),
                init_date=init_date,
                telephone=telephone,
                address=string_utils.xstr(patient_row['Address']),
            )

        return html

    def get_medical_record_html(self):
        if self.sql is None:
            sql = '''
                SELECT * FROM cases
                WHERE
                    PatientKey = {patient_key} AND
                    InsType = "健保" AND
                    CaseDate BETWEEN "{start_date}" AND "{end_date}"
                ORDER BY CaseDate
            '''.format(
                patient_key = self.patient_key,
                start_date = self.start_date,
                end_date = self.end_date,
            )
        else:
            sql = self.sql

        if self.end_date is not None:
            current_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S')
        else:
            current_date = None

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return None

        medical_record_html= ''
        for row in rows:
            case_key = row['CaseKey']
            medicine_set = 1

            if (current_date is not None and
                    row['CaseDate'].year == current_date.year and
                    row['CaseDate'].month == current_date.month):
                color = 'yellow'
            else:
                color = None

            case_record = printer_utils.get_case_html_1(
                self.database, case_key, '健保',
                background_color=color
            )
            symptom_record = printer_utils.get_symptom_html(self.database, case_key, colspan=5)
            disease_record = printer_utils.get_disease(self.database, case_key)
            prescript_record = printer_utils.get_prescript_html(
                self.database, self.system_settings,
                case_key, medicine_set,
                '過去病歷', print_alias=False, print_total_dosage=True, blocks=3)
            instruction = printer_utils.get_instruction_html(
                self.database, self.system_settings, case_key, medicine_set
            )

            medical_record_html += '''
                <table width="98%" cellspacing="0">
                  <tbody>
                    {case}
                    {symptom}
                  </tbody>  
                </table>
                {disease}
                <table width="98%" cellspacing="0" style="font-weight: bold; background-color: lightgray">
                  <tbody>
                    {prescript}
                  </tbody>
                </table>        
                {instruction}
                <hr>
            '''.format(
                case=case_record,
                symptom=symptom_record,
                disease=disease_record,
                prescript=prescript_record,
                instruction=instruction,
            )

        return medical_record_html
