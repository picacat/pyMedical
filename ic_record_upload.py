#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from xml.dom.minidom import Document

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import date_utils
from libs import case_utils
from libs import personnel_utils
from libs import cshis_utils
from libs import nhi_utils
from libs import system_utils

from dialog import dialog_ic_record_upload
from classes import table_widget


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
        self.xml_out_path = './nhi_upload'

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

        sql = dialog.get_sql()
        dialog.close_all()
        dialog.deleteLater()

        if result == 0:
            return

        self.table_widget_medical_record.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, rec_no, rec):
        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = 1
        '''.format(rec['CaseKey'])
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            pres_days = rows[0]['Days']
        else:
            pres_days = None

        error_message = self._check_error(rec)
        if error_message != '':
            remark = ''
        else:
            remark = '*'

        medical_record = [
            string_utils.xstr(rec['CaseKey']),
            remark,
            cshis_utils.UPLOAD_TYPE_DICT[string_utils.get_str(rec['UploadType'], 'utf-8')],
            cshis_utils.TREAT_AFTER_CHECK_DICT[string_utils.get_str(rec['TreatAfterCheck'], 'utf-8')],
            string_utils.xstr(rec['CaseDate']),
            string_utils.xstr(rec['Period']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Gender']),
            string_utils.xstr(rec['Birthday']),
            string_utils.xstr(rec['CaseInsType']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['Card']),
            string_utils.int_to_str(rec['Continuance']).strip('0'),
            string_utils.int_to_str(pres_days),
            string_utils.xstr(rec['Doctor']),
            string_utils.xstr(rec['DiseaseName1']),
            error_message,
        ]

        for column in range(0, self.ui.tableWidget_ic_record.columnCount()):
            self.ui.tableWidget_ic_record.setItem(rec_no, column, QtWidgets.QTableWidgetItem(medical_record[column]))
            if column in [4, 5, 6, 14, 15, 19, 20, 21, 22]:
                self.ui.tableWidget_ic_record.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [1, 8]:
                self.ui.tableWidget_ic_record.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            if number_utils.get_integer(rec['TotalFee']) > 0 or rec['InsType'] == '自費':
                self.ui.tableWidget_ic_record.item(rec_no, column).setForeground(QtGui.QColor('blue'))

    def _check_error(self, medical_record):
        if string_utils.xstr(medical_record['DoctorDone']) == 'False':
            return '[尚未就診, 請登錄完成後再上傳]'

        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(medical_record['PatientKey'])
        patient_record = self.database.select_record(sql)[0]

        error_message = ''
        if string_utils.get_str(medical_record['UploadType'], 'utf-8') == '1':
            if string_utils.get_str(medical_record['RegisteredDate'], 'utf-8') == '':
                error_message += '[無IC卡掛號時間]'
            if string_utils.get_str(medical_record['SecuritySignature'], 'utf-8') == '':
                error_message += '[無安全簽章]'
            if string_utils.get_str(medical_record['SAMID'], 'utf-8') == '':
                error_message += '[無安全模組代碼]'
            if string_utils.get_str(medical_record['ClinicID'], 'utf-8') == '':
                error_message += '[無院所代碼]'
            if string_utils.xstr(patient_record['CardNo']) == '':
                error_message += '[病患資料無卡片號碼]'

        if string_utils.xstr(patient_record['ID']) == '':
            error_message += '[病患資料無身份證號碼]'
        if string_utils.xstr(patient_record['Birthday']) == '':
            error_message += '[病患資料無生日]'
        if string_utils.get_str(medical_record['UploadType'], 'utf-8') == '':
            error_message += '[無上傳格式]'
        if string_utils.get_str(medical_record['TreatAfterCheck'], 'utf-8') == '':
            error_message += '[無補卡註劑]'
        if string_utils.xstr(medical_record['Card']) == '':
            error_message += '[無卡序]'

        doctor_id = personnel_utils.get_personnel_id(
            self.database, string_utils.xstr(medical_record['Doctor']))
        position_list = personnel_utils.get_personnel(self.database, '醫師')

        if doctor_id == '':
            error_message += '[無醫師身份證號]'
        elif string_utils.xstr(medical_record['Doctor']) not in position_list:
            error_message += '[醫師欄位非醫師]'
        if string_utils.xstr(medical_record['DiseaseCode1']) == '':
            error_message += '[無主診斷碼]'
        if string_utils.xstr(medical_record['InsTotalFee']) == '':
            error_message += '[無申報費用]'

        return error_message

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
            self.xml_out_path,
            self.upload_type,
            date_utils.date_to_str()
        )
        self.create_xml_file(xml_file_name)
        record_count = self.get_upload_record_count()

        ic_card = cshis_utils.upload_data(self.system_settings, xml_file_name, record_count)
        if ic_card is not None:
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
                '上傳結果請於24小時後再查詢'
            )

    def create_xml_file(self, xml_file_name):
        doc = Document()
        doc.encoding='Big5'
        recs = doc.createElement('RECS')
        doc.appendChild(recs)

        for row in range(self.ui.tableWidget_ic_record.rowCount()):
            self.ui.tableWidget_ic_record.setCurrentCell(row, 0)
            remark = self.ui.tableWidget_ic_record.item(row, 1).text()
            if remark != '*':
                continue

            case_key = self.ui.tableWidget_ic_record.item(row, 0).text()
            upload_type = self.get_upload_type(case_key)
            medical_record = self.database.select_record(
                'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key))[0]
            self.add_rec(doc, recs, medical_record, upload_type)

        xml_file = open(xml_file_name, 'w', encoding='Big5')
        doc.writexml(xml_file, '', ' '*2, '\n', 'Big5')
        xml_file.close()

        return xml_file_name

    def get_upload_type(self, case_key):
        upload_type = case_utils.extract_xml(self.database, case_key, 'upload_type')
        if upload_type == '':
            upload_type = '1'
        if self.upload_type == '2':  # 補正上傳
            upload_type = str(int(upload_type) + 2)  # 轉換成補正上傳 1->3, 2->4

        return upload_type

    # 每一筆資料上傳內容
    def add_rec(self, doc, recs, medical_record, upload_type):
        rec = doc.createElement('REC')
        recs.appendChild(rec)

        self.add_msh(doc, rec, upload_type)  # 表頭
        self.add_mb(doc, rec, medical_record, upload_type)   # 資料本體

    # 表頭內容
    def add_msh(self, doc, rec, upload_type):
        msh = doc.createElement('MSH')
        rec.appendChild(msh)

        a00 = doc.createElement('A00')
        a00.appendChild(doc.createTextNode('1'))
        msh.appendChild(a00)

        a01 = doc.createElement('A01')
        a01.appendChild(doc.createTextNode(upload_type))
        msh.appendChild(a01)

        a02 = doc.createElement('A02')
        a02.appendChild(doc.createTextNode('1.0'))
        msh.appendChild(a02)

    # 每一筆資料本體
    def add_mb(self, doc, rec, medical_record, upload_type):
        mb = doc.createElement('MB')
        rec.appendChild(mb)

        self.add_mb1(doc, mb, medical_record, upload_type)
        self.add_mb2(doc, mb, medical_record, upload_type)

    # 健保資料段
    def add_mb1(self, doc, mb, medical_record, upload_type):
        case_key = string_utils.xstr(medical_record['CaseKey'])
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(
            string_utils.xstr(medical_record['PatientKey'])
        )
        patient_record = self.database.select_record(sql)[0]
        mb1 = doc.createElement('MB1')
        mb.appendChild(mb1)

        if upload_type == '1':
            a11 = doc.createElement('A11')
            a11.appendChild(doc.createTextNode(string_utils.xstr(patient_record['CardNo'])))
            mb1.appendChild(a11)

            clinic_id = case_utils.extract_xml(
                self.database, case_key, 'clinic_id'
            )
            a14 = doc.createElement('A14')
            a14.appendChild(doc.createTextNode(clinic_id))
            mb1.appendChild(a14)

            sam_id = case_utils.extract_xml(
                self.database, case_key, 'sam_id'
            )
            a16 = doc.createElement('A16')
            a16.appendChild(doc.createTextNode(sam_id))
            mb1.appendChild(a16)

            registered_date = case_utils.extract_xml(
                self.database, case_key, 'registered_date'
            )
            a17 = doc.createElement('A17')
            a17.appendChild(doc.createTextNode(date_utils.west_datetime_to_nhi_datetime(
                registered_date)))
            mb1.appendChild(a17)

            security_signature = case_utils.extract_xml(
                self.database, case_key, 'security_signature'
            )
            a22 = doc.createElement('A22')
            a22.appendChild(doc.createTextNode(security_signature))
            mb1.appendChild(a22)
        else:
            a14 = doc.createElement('A14')
            a14.appendChild(doc.createTextNode(self.system_settings.field('院所代號')))
            mb1.appendChild(a14)

            a17 = doc.createElement('A17')
            a17.appendChild(doc.createTextNode(date_utils.west_datetime_to_nhi_datetime(
                medical_record['CaseDate'])))
            mb1.appendChild(a17)


        a12 = doc.createElement('A12')
        a12.appendChild(doc.createTextNode(string_utils.xstr(patient_record['ID'])))
        mb1.appendChild(a12)

        a13 = doc.createElement('A13')
        a13.appendChild(doc.createTextNode(date_utils.west_date_to_nhi_date(patient_record['Birthday'])))
        mb1.appendChild(a13)


        a15 = doc.createElement('A15')
        a15.appendChild(doc.createTextNode(personnel_utils.get_personnel_id(
            self.database, string_utils.xstr(medical_record['Doctor'])
        )))
        mb1.appendChild(a15)

        card = case_utils.extract_xml(self.database, case_key, 'seq_number')
        xcard = string_utils.xstr(medical_record['XCard'])
        if xcard != '':
            card = xcard

        '''
        1. 當A01為(1、3正常卡序)且A23就醫類別為(01-08內科或首次)時，A18必須為數字欄位且不可空白，若大於1500退件。
        2. 當A01為(1、3)且A23非(01-08、AC療程)時，A18需為空值
        3. 當A01為(2、4)，A18必須符合左列的內容
        4. 當A23值非01 - 08，則A18可接受空值
        5. 當A23為AC且A01 = (1、3)，A18必須足4碼且為IC開頭ICxx
        6. 當A01為(1、3) 但A23不等於(01~08, AC)， 則A18可以等於"IC08"
        '''
        a18 = doc.createElement('A18')
        a18.appendChild(doc.createTextNode(card))
        mb1.appendChild(a18)

        treat_after_check = case_utils.extract_xml(
            self.database,
            case_key,
            'treat_after_check'
        )
        a19 = doc.createElement('A19')
        a19.appendChild(doc.createTextNode(treat_after_check))
        mb1.appendChild(a19)

        treat_item = cshis_utils.get_treat_item(medical_record['Continuance'])
        a23 = doc.createElement('A23')
        a23.appendChild(doc.createTextNode(treat_item))
        mb1.appendChild(a23)

        disease_code1 = string_utils.xstr(medical_record['DiseaseCode1'])
        a25 = doc.createElement('A25')
        a25.appendChild(doc.createTextNode(disease_code1))
        mb1.appendChild(a25)

        disease_code2 = string_utils.xstr(medical_record['DiseaseCode2'])
        if disease_code2 != '':
            a26 = doc.createElement('A26')
            a26.appendChild(doc.createTextNode(disease_code2))
            mb1.appendChild(a26)

        disease_code3 = string_utils.xstr(medical_record['DiseaseCode3'])
        if disease_code3 != '':
            a27 = doc.createElement('A27')
            a27.appendChild(doc.createTextNode(disease_code3))
            mb1.appendChild(a27)

        ins_total_fee = number_utils.get_integer(medical_record['InsTotalFee'])
        a31 = doc.createElement('A31')
        a31.appendChild(doc.createTextNode(str(ins_total_fee)))
        mb1.appendChild(a31)

        share_fee = (
                number_utils.get_integer(medical_record['DiagShareFee']) +
                number_utils.get_integer(medical_record['DrugShareFee'])
        )
        a32 = doc.createElement('A32')
        a32.appendChild(doc.createTextNode(str(share_fee)))
        mb1.appendChild(a32)

        a54 = doc.createElement('A54')
        a54.appendChild(doc.createTextNode(date_utils.west_datetime_to_nhi_datetime(
            medical_record['CaseDate'])))
        mb1.appendChild(a54)

    # 醫療專區
    def add_mb2(self, doc, mb, medical_record, upload_type):
        self.add_treat(doc, mb, medical_record, upload_type)
        self.add_medicine(doc, mb, medical_record, upload_type)

    def add_treat(self, doc, mb, medical_record, upload_type):
        treatment = string_utils.xstr(medical_record['Treatment'])
        if treatment == '':
            return

        case_key = medical_record['CaseKey']

        mb2 = doc.createElement('MB2')
        mb.appendChild(mb2)
        registered_date = case_utils.extract_xml(
            self.database, case_key, 'registered_date'
        )
        a71 = doc.createElement('A71')
        a71.appendChild(doc.createTextNode(date_utils.west_datetime_to_nhi_datetime(
            registered_date)))
        mb2.appendChild(a71)

        prescript_type = '3'  # 3-診療
        a72 = doc.createElement('A72')
        a72.appendChild(doc.createTextNode(prescript_type))
        mb2.appendChild(a72)

        a73 = doc.createElement('A73')
        a73.appendChild(doc.createTextNode(
            nhi_utils.TREAT_DICT[treatment]
        ))
        mb2.appendChild(a73)

        days = 0
        a76 = doc.createElement('A76')
        a76.appendChild(doc.createTextNode('{0:0>2}'.format(days)))
        mb2.appendChild(a76)

        dosage = 1
        a77 = doc.createElement('A77')
        a77.appendChild(doc.createTextNode('{0:07.1f}'.format(dosage)))
        mb2.appendChild(a77)

        pharmacy_type = '03'  # 物理治療
        a78 = doc.createElement('A78')
        a78.appendChild(doc.createTextNode(pharmacy_type))
        mb2.appendChild(a78)

        if upload_type == '1':
            sql = '''
            SELECT Content AS PrescriptSign FROM presextend WHERE 
                PrescriptKey = {0} AND
                ExtendType = "處置簽章"
            '''.format(case_key)
            rows = self.database.select_record(sql)
            if len(rows) > 0:
                prescript_sign = string_utils.xstr(rows[0]['PrescriptSign'])
                a79 = doc.createElement('A79')
                a79.appendChild(doc.createTextNode(prescript_sign))
                mb2.appendChild(a79)

    def add_medicine(self, doc, mb, medical_record, upload_type):
        case_key = string_utils.xstr(medical_record['CaseKey'])

        if upload_type == '1':
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
        else:
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
            self.add_medicine_rows(doc, mb, prescript_row, dosage_row, case_key, upload_type)

    def add_medicine_rows(self, doc, mb, prescript_row, dosage_row, case_key, upload_type):
        mb2 = doc.createElement('MB2')
        mb.appendChild(mb2)

        registered_date = case_utils.extract_xml(
            self.database, case_key, 'registered_date'
        )
        if registered_date == '':
            row = self.database.select_record(
                'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
            )[0]
            registered_date = row['CaseDate']
        a71 = doc.createElement('A71')
        a71.appendChild(doc.createTextNode(date_utils.west_datetime_to_nhi_datetime(
            registered_date)))
        mb2.appendChild(a71)

        prescript_type = '1'  # 1-長期藥品
        a72 = doc.createElement('A72')
        a72.appendChild(doc.createTextNode(prescript_type))
        mb2.appendChild(a72)

        a73 = doc.createElement('A73')
        a73.appendChild(doc.createTextNode(string_utils.xstr(prescript_row['InsCode'])))
        mb2.appendChild(a73)

        if len(dosage_row) > 0:
            frequency = nhi_utils.FREQUENCY[dosage_row[0]['Packages']]
            days = number_utils.get_integer(dosage_row[0]['Days'])
            dosage = prescript_row['Dosage'] * days
        else:
            frequency = ''
            days = 0
            dosage = 0

        a75 = doc.createElement('A75')
        a75.appendChild(doc.createTextNode(frequency))
        mb2.appendChild(a75)

        a76 = doc.createElement('A76')
        a76.appendChild(doc.createTextNode('{0:0>2}'.format(days)))
        mb2.appendChild(a76)

        a77 = doc.createElement('A77')
        a77.appendChild(doc.createTextNode('{0:07.1f}'.format(dosage)))
        mb2.appendChild(a77)

        pharmacy_type = '01'  # 自行調劑
        a78 = doc.createElement('A78')
        a78.appendChild(doc.createTextNode(pharmacy_type))
        mb2.appendChild(a78)

        if upload_type == '1':
            prescript_sign = string_utils.xstr(prescript_row['PrescriptSign'])
            if prescript_sign != '':
                a79 = doc.createElement('A79')
                a79.appendChild(doc.createTextNode(prescript_sign))
                mb2.appendChild(a79)
