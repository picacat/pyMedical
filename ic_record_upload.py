#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from lxml import etree as ET

import sys
import time

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import date_utils
from libs import case_utils
from libs import personnel_utils
from libs import nhi_utils
from libs import system_utils
from libs import xml_utils
from libs import cshis_utils

from dialog import dialog_ic_record_upload

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 主視窗
class ICRecordUpload(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ICRecordUpload, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.dialog_setting = {
            "dialog_executed": False,
            "start_date": None,
            "end_date": None,
            "period": None,
        }
        self.ui = None
        self.upload_type = '1'  # 預設-正常上傳

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_medical_record_list(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_IC_RECORD_UPLOAD, self)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_ic_record, self.database)
        self.table_widget_medical_record.set_column_hidden([0])
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_close.triggered.connect(self.close_medical_record_list)
        self.ui.action_open_record.triggered.connect(self.open_medical_record)
        self.ui.action_upload_file.triggered.connect(self.upload_xml_file)
        self.ui.action_remark.triggered.connect(self.remark_record)
        self.ui.action_correct_errors.triggered.connect(self._correct_errors)
        self.ui.tableWidget_ic_record.doubleClicked.connect(self.open_medical_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [70, 10, 80, 80, 160, 50, 80, 80, 40, 120, 50, 80, 80, 70, 40, 40, 80, 200, 500]
        self.table_widget_medical_record.set_table_heading_width(width)

    # 讀取病歷
    def open_dialog(self):
        dialog = dialog_ic_record_upload.DialogICRecordUpload(self, self.database, self.system_settings)
        if self.dialog_setting['dialog_executed']:
            dialog.ui.dateEdit_start_date.setDate(self.dialog_setting['start_date'])
            dialog.ui.dateEdit_end_date.setDate(self.dialog_setting['end_date'])
            dialog.ui.comboBox_period.setCurrentText(self.dialog_setting['period'])

        result = dialog.exec_()
        self.dialog_setting['dialog_executed'] = True
        self.dialog_setting['start_date'] = dialog.ui.dateEdit_start_date.date()
        self.dialog_setting['end_date'] = dialog.ui.dateEdit_end_date.date()
        self.dialog_setting['period'] = dialog.comboBox_period.currentText()
        if dialog.ui.radioButton_normal.isChecked():
            self.upload_type = '1'
        else:
            self.upload_type = '2'

        self.sql = dialog.get_sql()
        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return

        self.table_widget_medical_record.set_db_data(self.sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = 1
        '''.format(row['CaseKey'])
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            pres_days = rows[0]['Days']
        else:
            pres_days = None

        security_row = case_utils.get_treat_data_xml_dict(string_utils.get_str(row['Security'], 'utf-8'))
        upload_type = case_utils.extract_security_xml(row['Security'], '資料格式')
        treat_after_check = case_utils.extract_security_xml(row['Security'], '補卡註記')
        upload_time = case_utils.extract_security_xml(row['Security'], '上傳時間')

        error_message = self._check_error(row, security_row)
        if error_message != '':
            remark = ''
        else:
            remark = '*'

        medical_record = [
            string_utils.xstr(row['CaseKey']),
            remark,
            cshis_utils.UPLOAD_TYPE_DICT[upload_type],
            cshis_utils.UPLOAD_TYPE_DICT[treat_after_check],
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['CaseInsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.int_to_str(row['Continuance']).strip('0'),
            string_utils.int_to_str(pres_days),
            string_utils.xstr(row['Doctor']),
            upload_time,
            error_message,
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_ic_record.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [5, 6, 14, 15, 19, 20, 21, 22]:
                self.ui.tableWidget_ic_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [1, 8]:
                self.ui.tableWidget_ic_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if error_message != '':
                self.ui.tableWidget_ic_record.item(
                    row_no, column).setForeground(
                    QtGui.QColor('red')
                )

    def _check_error(self, row, security_row):
        if string_utils.xstr(row['DoctorDone']) == 'False':
            return '[尚未就診, 請登錄完成後再上傳]'

        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(row['PatientKey'])
        patient_record = self.database.select_record(sql)[0]

        error_message = []
        # if string_utils.xstr(row['Card']) in nhi_utils.ABNORMAL_CARD:
        #     return error_message

        if security_row['upload_type'] == '1':
            if security_row['registered_date'] == '':
                error_message.append('無IC卡掛號時間')
            if security_row['security_signature'] == '':
                error_message.append('無安全簽章')
            if security_row['sam_id'] == '':
                error_message.append('無安全模組代碼')
            if security_row['clinic_id']== '':
                error_message.append('無院所代碼')
            if string_utils.xstr(patient_record['CardNo']) == '':
                error_message.append('病患資料無卡片號碼')

        if string_utils.xstr(patient_record['ID']) == '':
            error_message.append('病患資料無身份證號碼')
        if string_utils.xstr(patient_record['Birthday']) == '':
            error_message.append('病患資料無生日')
        if security_row['upload_type'] == '':
            error_message.append('無上傳格式')
        if security_row['treat_after_check']== '':
            error_message.append('無補卡註記')
        if string_utils.xstr(row['Card']) == '':
            error_message.append('無卡序')

        doctor_id = personnel_utils.get_personnel_field_value(
            self.database, string_utils.xstr(row['Doctor']), 'ID')
        position_list = personnel_utils.get_personnel(self.database, '醫師')

        if doctor_id == '':
            error_message.append('無醫師身份證號')
        elif string_utils.xstr(row['Doctor']) not in position_list:
            error_message.append('醫師欄位非醫師')
        if string_utils.xstr(row['DiseaseCode1']) == '':
            error_message.append('無主診斷碼')
        if string_utils.xstr(row['InsTotalFee']) == '':
            error_message.append('無申報費用')
        for i in range(1, 4):
            disease_code = string_utils.xstr(row['DiseaseCode{0}'.format(i)])
            if disease_code == '':
                continue

            if not case_utils.is_disease_code_neat(self.database, disease_code):
                error_message.append('病名{0}非最細碼'.format(i))

        return ', '.join(error_message)

    def open_medical_record(self):
        case_key = self.table_widget_medical_record.field_value(0)
        self.parent.open_medical_record(case_key, '病歷查詢')

    def remark_record(self):
        row = self.ui.tableWidget_ic_record.currentRow()
        remark = self.ui.tableWidget_ic_record.item(row, 1).text()
        if remark == '*':
            remark = ''
        else:
            remark = '*'

        self.ui.tableWidget_ic_record.setItem(
            row, 1, QtWidgets.QTableWidgetItem(remark)
        )
        self.ui.tableWidget_ic_record.item(row, 1).setTextAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

    # 取得上傳筆數
    def get_upload_record_count(self):
        record_count = 0

        for i in range(self.ui.tableWidget_ic_record.rowCount()):
            remark = self.ui.tableWidget_ic_record.item(i, 1).text()
            if remark == '*':
                record_count += 1

        return record_count

    # 上傳資料
    def upload_xml_file(self):
        xml_file_name = '{0}/IC-{1}-{2}.xml'.format(
            nhi_utils.XML_OUT_PATH,
            self.upload_type,
            date_utils.date_to_str()
        )
        if not self.create_xml_file(xml_file_name):
            return

        record_count = self.get_upload_record_count()

        ic_card = cshis.CSHIS(self.database, self.system_settings)
        if ic_card.upload_data(xml_file_name, record_count):
            self._set_uploaded_records()

            system_utils.show_message_box(
                QMessageBox.Information,
                '上傳成功',
                '''
                    <h3>健保IC卡資料上傳成功, 回傳結果如下:</h3>
                    安全模組: {0}<br>
                    院所代號: {1}<br>
                    上傳時間: {2}<br>
                    接收時間: {3}
                '''.format(
                    ic_card.xml_feedback_data['sam_id'],
                    ic_card.xml_feedback_data['clinic_id'],
                    ic_card.xml_feedback_data['upload_time'],
                    ic_card.xml_feedback_data['receive_time']
                ),
                '上傳結果請於2小時後再查詢'
            )

    # 更新健保上傳時間
    def _set_uploaded_records(self):
        upload_time = date_utils.now_to_str()

        for row in range(self.ui.tableWidget_ic_record.rowCount()):
            self.ui.tableWidget_ic_record.setCurrentCell(row, 0)
            remark = self.ui.tableWidget_ic_record.item(row, 1).text()
            if remark != '*':
                continue

            case_key = self.ui.tableWidget_ic_record.item(row, 0).text()
            case_utils.update_xml(
                self.database, 'cases', 'Security', 'upload_time',
                upload_time, 'CaseKey', case_key,
            )

    def create_xml_file(self, xml_file_name):
        root = ET.Element('RECS')

        for row in range(self.ui.tableWidget_ic_record.rowCount()):
            self.ui.tableWidget_ic_record.setCurrentCell(row, 0)
            remark = self.ui.tableWidget_ic_record.item(row, 1).text()
            if remark != '*':
                continue

            case_key = self.ui.tableWidget_ic_record.item(row, 0).text()
            medical_record = self.database.select_record(
                'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key))[0]
            upload_type = self.get_upload_type(medical_record)
            if not self.add_rec(root, medical_record, upload_type):
                return False

        tree = ET.ElementTree(root)
        tree.write(xml_file_name, pretty_print=True, xml_declaration=True, encoding="Big5")
        xml_utils.set_xml_file_to_big5(xml_file_name)

        return True

    def get_upload_type(self, medical_record):
        upload_type = case_utils.extract_security_xml(medical_record['Security'], '資料格式')
        if upload_type == '':
            upload_type = '1'
        if self.upload_type == '2':  # 補正上傳
            upload_type = string_utils.xstr(int(upload_type) + 2)  # 轉換成補正上傳 1->3, 2->4

        return string_utils.xstr(upload_type)

    # 每一筆資料上傳內容
    def add_rec(self, root, medical_record, upload_type):
        rec = ET.SubElement(root, 'REC')

        self.add_msh(rec, upload_type)  # 表頭
        if not self.add_mb(rec, medical_record, upload_type):   # 資料本體
            return False

        return True

    # 表頭內容
    def add_msh(self, rec, upload_type):
        msh = ET.SubElement(rec, 'MSH')

        a00 = ET.SubElement(msh, 'A00')
        a00.text = '1'
        a01 = ET.SubElement(msh, 'A01')
        a01.text = string_utils.xstr(upload_type)
        a02 = ET.SubElement(msh, 'A02')
        a02.text = '1.0'

    # 每一筆資料本體
    def add_mb(self, rec, medical_record, upload_type):
        mb = ET.SubElement(rec, 'MB')

        if not self.add_mb1(mb, medical_record, upload_type):
            return False

        if not self.add_mb2(mb, medical_record, upload_type):
            return False

        return True

    # 健保資料段
    def add_mb1(self, mb, medical_record, upload_type):
        mb1 = ET.SubElement(mb, 'MB1')

        case_key = string_utils.xstr(medical_record['CaseKey'])
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(
            string_utils.xstr(medical_record['PatientKey'])
        )
        patient_record = self.database.select_record(sql)[0]

        if upload_type in ['1', '3']:
            clinic_id = case_utils.extract_security_xml(medical_record['Security'], '院所代號')
            card = case_utils.extract_security_xml(medical_record['Security'], '健保卡序')
            registered_date = date_utils.west_datetime_to_nhi_datetime(
                case_utils.extract_security_xml(medical_record['Security'], '寫卡時間')
            )
        else:
            clinic_id = self.system_settings.field('院所代號')
            card = string_utils.xstr(medical_record['Card'])
            registered_date = date_utils.west_datetime_to_nhi_datetime(
                medical_record['CaseDate']
            )

        xcard = string_utils.xstr(medical_record['XCard'])
        if xcard != '':
            card = xcard

        card = string_utils.xstr(card)[:4]

        treat_after_check = case_utils.extract_security_xml(medical_record['Security'],'補卡註記')
        treat_item = cshis_utils.get_treat_item(medical_record['Continuance'])
        disease_code1 = string_utils.xstr(medical_record['DiseaseCode1'])
        disease_code2 = string_utils.xstr(medical_record['DiseaseCode2'])
        disease_code3 = string_utils.xstr(medical_record['DiseaseCode3'])
        ins_total_fee = number_utils.get_integer(medical_record['InsTotalFee'])
        share_fee = (
                number_utils.get_integer(medical_record['DiagShareFee']) +
                number_utils.get_integer(medical_record['DrugShareFee'])
        )

        if upload_type in ['1', '3']:
            a11 = ET.SubElement(mb1, 'A11')
            a11.text = string_utils.xstr(patient_record['CardNo'])

        a12 = ET.SubElement(mb1, 'A12')
        a12.text = string_utils.xstr(string_utils.xstr(patient_record['ID']))
        a13 = ET.SubElement(mb1, 'A13')
        a13.text = string_utils.xstr(date_utils.west_date_to_nhi_date(patient_record['Birthday']))
        a14 = ET.SubElement(mb1, 'A14')
        a14.text = string_utils.xstr(clinic_id)
        a15 = ET.SubElement(mb1, 'A15')
        a15.text = string_utils.xstr(personnel_utils.get_personnel_field_value(
            self.database, string_utils.xstr(medical_record['Doctor']), 'ID')
        )

        if upload_type in ['1', '3']:
            sam_id = case_utils.extract_security_xml(medical_record['Security'], '安全模組')
            a16 = ET.SubElement(mb1, 'A16')
            a16.text = string_utils.xstr(sam_id)

        a17 = ET.SubElement(mb1, 'A17')
        a17.text = string_utils.xstr(registered_date)
        a18 = ET.SubElement(mb1, 'A18')
        a18.text = string_utils.xstr(card)

        '''
        1. 當A01為(1、3正常卡序)且A23就醫類別為(01-08內科或首次)時，A18必須為數字欄位且不可空白，若大於1500退件。
        2. 當A01為(1、3)且A23非(01-08、AC療程)時，A18需為空值
        3. 當A01為(2、4)，A18必須符合左列的內容
        4. 當A23值非01 - 08，則A18可接受空值
        5. 當A23為AC且A01 = (1、3)，A18必須足4碼且為IC開頭ICxx
        6. 當A01為(1、3) 但A23不等於(01~08, AC)， 則A18可以等於"IC08"
        '''

        a19 = ET.SubElement(mb1, 'A19')
        a19.text = string_utils.xstr(treat_after_check)

        if upload_type in ['1', '3']:
            security_signature = case_utils.extract_security_xml(medical_record['Security'], '安全簽章')
            a22 = ET.SubElement(mb1, 'A22')
            a22.text = string_utils.xstr(security_signature)

        a23 = ET.SubElement(mb1, 'A23')
        a23.text = string_utils.xstr(treat_item)
        a25 = ET.SubElement(mb1, 'A25')
        a25.text = string_utils.xstr(disease_code1)

        if disease_code2 != '':
            a26 = ET.SubElement(mb1, 'A26')
            a26.text = string_utils.xstr(disease_code2)

        if disease_code3 != '':
            a27 = ET.SubElement(mb1, 'A27')
            a27.text = string_utils.xstr(disease_code3)

        a31 = ET.SubElement(mb1, 'A31')
        a31.text = string_utils.xstr(ins_total_fee)
        a32 = ET.SubElement(mb1, 'A32')
        a32.text = string_utils.xstr(share_fee)
        a54 = ET.SubElement(mb1, 'A54')
        a54.text = string_utils.xstr(date_utils.west_datetime_to_nhi_datetime(
            medical_record['CaseDate'])
        )

        return True

    # 醫療專區
    def add_mb2(self, mb, medical_record, upload_type):
        if not self.add_treat(mb, medical_record, upload_type):
            return False

        if not self.add_medicine(mb, medical_record, upload_type):
            return False

        return True

    def add_treat(self, mb, medical_record, upload_type):
        treatment = string_utils.xstr(medical_record['Treatment'])
        if treatment == '':
            return True

        case_key = medical_record['CaseKey']
        prescript_type = '3'  # 3-診療
        days = 0
        dosage = 1
        pharmacy_type = '03'  # 物理治療

        mb2 = ET.SubElement(mb, 'MB2')

        if upload_type in ['1', '3']:
            registered_date = date_utils.west_datetime_to_nhi_datetime(
                case_utils.extract_security_xml(medical_record['Security'], '寫卡時間')
            )
        else:
            registered_date = date_utils.west_datetime_to_nhi_datetime(
                medical_record['CaseDate']
            )

        a71 = ET.SubElement(mb2, 'A71')
        a71.text = string_utils.xstr(registered_date)
        a72 = ET.SubElement(mb2, 'A72')
        a72.text = string_utils.xstr(prescript_type)
        a73 = ET.SubElement(mb2, 'A73')
        a73.text = string_utils.xstr(nhi_utils.TREAT_DICT[treatment])
        a76 = ET.SubElement(mb2, 'A76')
        a76.text = string_utils.xstr('{0:0>2}'.format(days))
        a77 = ET.SubElement(mb2, 'A77')
        a77.text = string_utils.xstr('{0:07.1f}'.format(dosage))
        a78 = ET.SubElement(mb2, 'A78')
        a78.text = string_utils.xstr(pharmacy_type)

        if upload_type in ['1', '3']:
            sql = '''
            SELECT Content AS PrescriptSign FROM presextend WHERE 
                PrescriptKey = {0} AND
                ExtendType = "處置簽章"
            '''.format(case_key)
            rows = self.database.select_record(sql)
            if len(rows) > 0:
                prescript_sign = string_utils.xstr(rows[0]['PrescriptSign'])
                a79 = ET.SubElement(mb2, 'A79')
                a79.text = string_utils.xstr(prescript_sign)

        return True

    def add_medicine(self, mb, medical_record, upload_type):
        case_key = string_utils.xstr(medical_record['CaseKey'])

        if upload_type in ['1', '3']:  # 正常卡序
            sql = '''
                SELECT 
                    prescript.MedicineName, prescript.InsCode, prescript.Dosage, 
                    presextend.ExtendType, presextend.Content AS PrescriptSign 
                FROM prescript
                    LEFT JOIN presextend ON presextend.PrescriptKey = prescript.PrescriptKey 
                WHERE
                    prescript.CaseKey = {0} AND
                    prescript.MedicineSet = 1 AND 
                    prescript.InsCode IS NOT NULL AND
                    presextend.ExtendType = "處方簽章" AND
                    presextend.Content IS NOT NULL
                ORDER BY prescript.PrescriptNo, prescript.PrescriptKey
            '''.format(case_key)
        else:  # 異常卡序
            sql = '''
                SELECT  *
                FROM prescript
                WHERE
                    CaseKey = {0} AND
                    MedicineSet = 1 AND 
                    InsCode IS NOT NULL
                ORDER BY PrescriptNo, PrescriptKey
            '''.format(case_key)

        rows = self.database.select_record(sql)

        sql = 'SELECT * FROM dosage WHERE CaseKey = {0}'.format(case_key)
        dosage_row = self.database.select_record(sql)

        for prescript_row in rows:
            if not self.add_medicine_rows(
                    mb, medical_record, prescript_row, dosage_row, case_key, upload_type):
                return False

        return True

    def add_medicine_rows(self, mb, medical_record, prescript_row, dosage_row,
                          case_key, upload_type):
        mb2 = ET.SubElement(mb, 'MB2')

        if upload_type in ['1', '3']:
            registered_date = date_utils.west_datetime_to_nhi_datetime(
                case_utils.extract_security_xml(medical_record['Security'], '寫卡時間')
            )
        else:
            registered_date = date_utils.west_datetime_to_nhi_datetime(
                medical_record['CaseDate']
            )
        prescript_type = '1'  # 1-長期藥品
        if len(dosage_row) > 0:
            frequency = nhi_utils.FREQUENCY[dosage_row[0]['Packages']]
            days = number_utils.get_integer(dosage_row[0]['Days'])
            try:
                dosage = prescript_row['Dosage'] * days
            except:
                system_utils.show_message_box(
                    QMessageBox.Critical,
                    '資料錯誤',
                    '<font size="4" color="red"><b>{0}的處方內容有誤, 請確認處方名稱或劑量是否空白.</b></font>'.format(
                        string_utils.xstr(medical_record['Name'])
                    ),
                    '請進入病歷內查看並更正此錯誤後再上傳.'
                )
                return False
        else:
            frequency = ''
            days = 0
            dosage = 0

        pharmacy_type = '01'  # 自行調劑

        a71 = ET.SubElement(mb2, 'A71')
        a71.text = string_utils.xstr(registered_date)
        a72 = ET.SubElement(mb2, 'A72')
        a72.text = string_utils.xstr(prescript_type)
        a73 = ET.SubElement(mb2, 'A73')
        a73.text = string_utils.xstr(prescript_row['InsCode'])
        a75 = ET.SubElement(mb2, 'A75')
        a75.text = string_utils.xstr(frequency)
        a76 = ET.SubElement(mb2, 'A76')
        a76.text = string_utils.xstr('{0:0>2}'.format(days))
        a77 = ET.SubElement(mb2, 'A77')
        a77.text = string_utils.xstr('{0:07.1f}'.format(dosage))
        a78 = ET.SubElement(mb2, 'A78')
        a78.text = string_utils.xstr(pharmacy_type)

        if upload_type in ['1', '3']:
            prescript_sign = string_utils.xstr(prescript_row['PrescriptSign'])
            if prescript_sign != '':
                a79 = ET.SubElement(mb2, 'A79')
                a79.text = string_utils.xstr(prescript_sign)

        return True

    def _correct_errors(self):
        for row_no in range(self.ui.tableWidget_ic_record.rowCount()):
            case_key = self.ui.tableWidget_ic_record.item(row_no, 0).text()
            card_item = self.ui.tableWidget_ic_record.item(row_no, 13)
            if card_item is None:
                continue

            card = card_item.text()

            if card not in nhi_utils.ABNORMAL_CARD:  # 正常卡序不調整
                continue

            upload_type = '2'
            treat_after_check = '1'

            case_utils.update_xml(
                self.database, 'cases', 'Security', 'upload_type',
                upload_type, 'CaseKey', case_key,
            )  # 更新健保寫卡資料
            case_utils.update_xml(
                self.database, 'cases', 'Security', 'treat_after_check',
                treat_after_check, 'CaseKey', case_key,
            )  # 更新健保寫卡資料

        self.table_widget_medical_record.set_db_data(self.sql, self._set_table_data)
