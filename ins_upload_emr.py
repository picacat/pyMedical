#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtGui, QtCore
from PyPDF2 import PdfFileMerger
import os
import shutil
import datetime
from lxml import etree as ET
import subprocess

from libs import printer_utils
from libs import nhi_utils
from libs import date_utils
from libs import string_utils
from libs import xml_utils
from libs import system_utils


# 健保電子化抽審 2018.11.05
class InsUploadEMR(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsUploadEMR, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_date = args[2]
        self.apply_type = args[3]
        self.apply_period = args[4]
        self.clinic_id = args[5]
        self.apply_upload_date = args[6]
        self.ui = None
        self.start_no = 1

        self.apply_type_code = nhi_utils.APPLY_TYPE_CODE[self.apply_type]
        self.apply_year = int(self.apply_date[:3]) + 1911
        self.apply_month = int(self.apply_date[3:5])
        self.EXPORT_DIR = '{0}/emr{1}'.format(
            nhi_utils.get_dir(self.system_settings, '申報路徑'), self.apply_date
        )

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
        pass

    # 設定信號
    def _set_signal(self):
        pass

    def upload_emr_files(self):
        apply_date = '{0}-{1:0>2}'.format(self.apply_year, self.apply_month)

        sql = '''
            SELECT * FROM system_log
            WHERE
                LogType = "抽審日期" AND
                LogName = "{apply_date}"
        '''.format(
            apply_date=apply_date,
        )
        rows = self.database.select_record(sql)
        self.start_no += len(rows) * 1000

        if not self._generate_emr_files():
            return

        type_code = '15'  # 費用抽審批次上傳
        zip_file = self._get_zip_file_name()
        nhi_utils.NHI_SendB(self.system_settings, type_code, zip_file)

        generate_date = datetime.date.today().strftime("%Y-%m-%d")
        fields = ['LogType', 'LogName', 'Log']
        data = ['抽審日期', apply_date, generate_date]
        self.database.insert_record('system_log', fields, data)

    def _generate_emr_files(self):
        shutil.rmtree(self.EXPORT_DIR, ignore_errors=True)

        sql = '''
            SELECT 
                InsApplyKey, ApplyDate, CaseType, Sequence, PatientKey, ID
            FROM insapply
            WHERE
                ApplyDate = "{apply_date}" AND
                ApplyType = "{apply_type}" AND
                ApplyPeriod = "{apply_period}" AND
                ClinicID = "{clinic_id}" AND
                Note = "*"
            ORDER BY CaseType, Sequence
        '''.format(
            apply_date=self.apply_date,
            apply_type=self.apply_type_code,
            apply_period=self.apply_period,
            clinic_id=self.clinic_id,
        )

        rows = self.database.select_record(sql)

        row_count = len(rows)

        if row_count <= 0:
            system_utils.show_message_box(
                QtWidgets.QMessageBox.Critical,
                '無抽審資料',
                '<font size="4" color="red"><b>找不到註記的資料, 請註記流水號後再執行抽審上傳作業.</b></font>',
                '請確定讀卡機是否連接, 或VPN網路是否暢通.'
            )
            return False

        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生電子抽審檔中, 請稍後...', '取消', 0, row_count, self
        )

        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no, row in zip(range(row_count), rows):
            progress_dialog.setValue(row_no)
            if progress_dialog.wasCanceled():
                break

            pdf_file = self._create_pdf_files(row)
            self._zip_pdf_file(row_no, pdf_file)
            self._create_xml_files(row_no, row, pdf_file)

        progress_dialog.setValue(row_count)
        self._zip_all_files()

        return True

    # 建立抽審用pdf檔
    def _create_pdf_files(self, row):
        ins_apply_key = row['InsApplyKey']
        patient_key = row['PatientKey']

        printer_utils.print_ins_apply_order(
            self, self.database, self.system_settings,
            self.apply_year, self.apply_month,
            self.apply_type, ins_apply_key, 'pdf'
        )

        start_date, end_date = date_utils.get_two_month_date(
            self.database, patient_key,
            self.apply_year, self.apply_month,
        )

        printer_utils.print_medical_records(
            self, self.database, self.system_settings,
            patient_key, None, start_date, end_date, 'pdf'
        )

        printer_utils.print_medical_chart(
            self, self.database, self.system_settings,
            patient_key, self.apply_date, 'pdf'
        )

        ins_order_file = '{0}/ins_order_{1}{2:0>6}.pdf'.format(
            self.EXPORT_DIR,
            string_utils.xstr(row['CaseType']),
            string_utils.xstr(row['Sequence']),
        )
        chart_file = '{0}/chart_{1}.pdf'.format(self.EXPORT_DIR, patient_key)
        medical_records_file = '{0}/case_{1}.pdf'.format(self.EXPORT_DIR, patient_key)

        pdfs = [chart_file, medical_records_file, ins_order_file]
        if self.system_settings.field('健保業務') == '台北業務組':
            pdfs = [chart_file, medical_records_file]

        merger = PdfFileMerger()

        pdf_files_stream = []
        for pdf in pdfs:
            pdf_file = open(pdf, 'rb')
            merger.append(pdf_file)
            pdf_files_stream.append(pdf_file)

        file_name = '14A{0}{1:0>6}001.pdf'.format(
            string_utils.xstr(row['CaseType']),
            string_utils.xstr(row['Sequence']),
        )

        merged_pdf = '{0}/{1}'.format(self.EXPORT_DIR, file_name)

        with open(merged_pdf, 'wb') as f_out:
            merger.write(f_out)

        for pdf, pdf_stream in zip(pdfs, pdf_files_stream):
            pdf_stream.close()
            os.remove(pdf)

        return file_name

    def _zip_pdf_file(self, row_no, pdf_file):
        att_file = 'ATT{0}_{1}{2:0>8}.7z'.format(
            self.system_settings.field('院所代號'),
            datetime.datetime.now().strftime('%Y%m%d'),
            row_no+self.start_no,  # 應該是 +1, 暫時的，for 抽審測試
        )

        zip_file = '{0}/{1}'.format(self.EXPORT_DIR, att_file)
        source_file = '{0}/{1}'.format(self.EXPORT_DIR, pdf_file)

        cmd = ['7z', 'a', zip_file, source_file, '-o{0}'.format(self.EXPORT_DIR)]
        sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        sp.communicate()

        return att_file

    # 建立抽審用xml檔
    def _create_xml_files(self, row_no, row, pdf_file):
        xml_file_name = '{0}/XML{1}_{2}{3:0>8}.XML'.format(
            self.EXPORT_DIR,
            self.system_settings.field('院所代號'),
            datetime.datetime.now().strftime('%Y%m%d'),
            row_no+self.start_no,  # 應該是 +1, 暫時的，for 抽審測試
        )

        root = ET.Element('feereview')
        tree = ET.ElementTree(root)

        cdata = ET.SubElement(root, 'cdata')
        chead = ET.SubElement(cdata, 'chead')
        c1 = ET.SubElement(chead, 'c1')
        c1.text = '2'  # 1=當期送審 2=事後審查 3=補件
        c2 = ET.SubElement(chead, 'c2')
        c2.text = self.system_settings.field('院所代號')
        c3 = ET.SubElement(chead, 'c3')
        c3.text = '14'  # 醫事類別: 14=中醫
        c4 = ET.SubElement(chead, 'c4')
        c4.text = self.apply_date
        c5 = ET.SubElement(chead, 'c5')
        c5.text = self.apply_type_code
        c6 = ET.SubElement(chead, 'c6')
        c6.text = self.apply_upload_date.toString('yyyyMMdd')

        cbody = ET.SubElement(cdata, 'cbody')
        c7 = ET.SubElement(cbody, 'c7')
        c7.text = string_utils.xstr(row['CaseType'])
        c8 = ET.SubElement(cbody, 'c8')
        c8.text = string_utils.xstr(row['Sequence'])
        c9 = ET.SubElement(cbody, 'c9')
        c9.text = string_utils.xstr(row['PatientKey'])
        c10 = ET.SubElement(cbody, 'c10')
        c10.text = string_utils.xstr(row['ID'])

        fdata = ET.SubElement(cbody, 'fdata')
        f1 = ET.SubElement(fdata, 'f1')
        f1.text = pdf_file
        f2 = ET.SubElement(fdata, 'f2')
        f2.text = 'PDF'
        f3 = ET.SubElement(fdata, 'f3')
        f3.text = 'ATT'
        f4 = ET.SubElement(fdata, 'f4')
        f4.text = '病歷本文(含病歷首頁, 雙月病歷及服務點數醫令清單)'

        tree.write(xml_file_name, pretty_print=True, xml_declaration=True, encoding="Big5")
        xml_utils.set_xml_file_to_big5(xml_file_name)

    def _get_zip_file_name(self):
        zip_file_name = '{0}/{1}_{2}_001.zip'.format(
            self.EXPORT_DIR,
            self.system_settings.field('院所代號'),
            date_utils.west_date_to_nhi_date(datetime.datetime.now()),
        )

        return zip_file_name

    def _zip_all_files(self):
        zip_file = self._get_zip_file_name()

        list_files = [f for f in os.listdir(self.EXPORT_DIR) if os.path.isfile(os.path.join(self.EXPORT_DIR, f))]
        list_files.sort()
        for file in list_files:
            ext_file_name = file.split('.')[1]
            if ext_file_name not in ['XML', '7z']:
                continue

            source_file = '{0}/{1}'.format(self.EXPORT_DIR, file)

            cmd = ['7z', 'a', '-tzip', zip_file, source_file, '-o{0}'.format(self.EXPORT_DIR)]
            sp = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            sp.communicate()

            os.remove(source_file)
