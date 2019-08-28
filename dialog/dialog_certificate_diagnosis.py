#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QInputDialog

import datetime

from classes import table_widget
from dialog import dialog_select_patient
from dialog import dialog_medical_record_past_history

from libs import ui_utils
from libs import system_utils
from libs import nhi_utils
from libs import string_utils
from libs import registration_utils


# 診斷證明
class DialogCertificateDiagnosis(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogCertificateDiagnosis, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.dialog_past_history = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        if self.dialog_past_history is not None:
            self.dialog_past_history.deleteLater()
            self.dialog_past_history = None

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_CERTIFICATE_DIAGNOSIS, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())
        self._set_combo_box()
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self._set_group_box(False)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self.table_widget_medical_record.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.toolButton_select_patient.clicked.connect(self._select_patient)
        self.ui.lineEdit_patient_key.textChanged.connect(self._patient_key_changed)
        self.ui.dateEdit_start_date.dateChanged.connect(self._start_date_changed)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_medical_record)
        self.ui.comboBox_ins_type.currentTextChanged.connect(self._read_medical_record)
        self.ui.comboBox_treat_type.currentTextChanged.connect(self._read_medical_record)
        self.ui.comboBox_doctor.currentTextChanged.connect(self._read_medical_record)
        self.ui.toolButton_import_diagnosis.clicked.connect(self._import_diagnosis)
        self.ui.toolButton_doctor_comment.clicked.connect(self._import_doctor_comment)
        self.ui.textEdit_diagnosis.textChanged.connect(self._check_diagnosis_completed)
        self.ui.textEdit_doctor_comment.textChanged.connect(self._check_diagnosis_completed)
        self.ui.toolButton_open_past_history.clicked.connect(self._open_past_history)

    def _set_table_width(self):
        width = [100, 10, 110, 50, 400, 90]
        self.table_widget_medical_record.set_table_heading_width(width)

    def _set_group_box(self, enabled):
        self.ui.lineEdit_name.setEnabled(enabled)
        self.ui.lineEdit_id.setEnabled(enabled)
        self.ui.lineEdit_birthday.setEnabled(enabled)
        self.ui.lineEdit_gender.setEnabled(enabled)
        self.ui.lineEdit_telephone.setEnabled(enabled)
        self.ui.lineEdit_address.setEnabled(enabled)

        self.ui.label_name.setEnabled(enabled)
        self.ui.label_id.setEnabled(enabled)
        self.ui.label_birthday.setEnabled(enabled)
        self.ui.label_gender.setEnabled(enabled)
        self.ui.label_telephone.setEnabled(enabled)
        self.ui.label_address.setEnabled(enabled)

        self.ui.groupBox_medical_record.setEnabled(enabled)
        self.ui.groupBox_diagnosis.setEnabled(enabled)

    # 設定comboBox
    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_treat_type, ['針傷科', '針灸科', '傷骨科', '內科'], '全部')
        self._set_doctor()

    def _set_doctor(self):
        script = 'select * from person where Position IN("醫師", "支援醫師") '
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, '全部')

    def accepted_button_clicked(self):
        self._save_files()

    def _save_files(self):
        case_key = self._write_medical_record()
        self._write_prescript(case_key)
        self._write_wait(case_key)

        certificate_key = self._write_certificate(case_key)
        self._write_certificate_items(certificate_key)

    def _select_patient(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        dialog = dialog_select_patient.DialogSelectPatient(
            self, self.database, self.system_settings, ''
        )
        if dialog.exec_():
            patient_key = dialog.get_patient_key()

        self.ui.lineEdit_patient_key.setText(patient_key)

        dialog.deleteLater()

    def _patient_key_changed(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        if patient_key.strip() == '':
            self._clear_patient_data()
            self._set_group_box(False)
            return

        sql = '''
            SELECT * FROM patient
            WHERE
                PatientKey = {0}
        '''.format(patient_key)

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        self._set_patient_data(row)
        self._set_group_box(True)
        self._read_medical_record()

    def _clear_patient_data(self):
        self.ui.lineEdit_name.setText('')
        self.ui.lineEdit_id.setText('')
        self.ui.lineEdit_birthday.setText('')
        self.ui.lineEdit_gender.setText('')
        self.ui.lineEdit_telephone.setText('')
        self.ui.lineEdit_address.setText('')

    def _set_patient_data(self, row):
        telephone = string_utils.xstr(row['Telephone'])
        if telephone == '':
            telephone = string_utils.xstr(row['Cellphone'])

        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']))
        self.ui.lineEdit_gender.setText(string_utils.xstr(row['Gender']))
        self.ui.lineEdit_telephone.setText(telephone)
        self.ui.lineEdit_address.setText(string_utils.xstr(row['Address']))

    def _start_date_changed(self):
        self._read_medical_record()

    def _read_medical_record(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')
        patient_key = self.ui.lineEdit_patient_key.text()

        treat_type_dict = {
            '針傷科': nhi_utils.INS_TREAT,
            '針灸科': nhi_utils.ACUPUNCTURE_TREAT,
            '傷骨科': nhi_utils.MASSAGE_TREAT,
        }

        condition = ''
        ins_type = self.ui.comboBox_ins_type.currentText()
        treat_type = self.ui.comboBox_treat_type.currentText()
        doctor = self.ui.comboBox_doctor.currentText()

        if ins_type in ['健保', '自費']:
            condition = ' AND InsType = "{0}" '.format(ins_type)

        if treat_type == '內科':
            condition += ' AND TreatType = "內科" '
        elif treat_type != '全部':
            condition += ' AND TreatType IN {0} '.format(tuple(treat_type_dict[treat_type]))

        if doctor not in ['全部', '']:
            condition += ' AND Doctor = "{0}" '.format(doctor)

        sql = '''
            SELECT CaseKey, CaseDate, InsType, Doctor, DiseaseName1, DiseaseName2 FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                PatientKey = {patient_key} AND
                TreatType != "自購"
                {condition}
            GROUP BY DATE(CaseDate)
            ORDER BY CaseDate
        '''.format(
            start_date=start_date,
            end_date=end_date,
            patient_key=patient_key,
            condition=condition,
        )
        self.table_widget_medical_record.set_db_data(sql, self._set_table_data, set_focus=False)
        self.ui.label_record_count.setText('門診次數: {0}次'.format(self.table_widget_medical_record.row_count()))
        self._check_diagnosis_completed()

    def _set_table_data(self, row_no, row):
        disease_list = [
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['DiseaseName2']),
        ]
        medical_record = [
            string_utils.xstr(row['CaseKey']),
            None,
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['InsType']),
            ', '.join(disease_list),
            string_utils.xstr(row['Doctor']),
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_medical_record.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )

            if column in [3]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        check_box = QtWidgets.QCheckBox(self.ui.tableWidget_medical_record)
        check_box.setChecked(True)
        self.ui.tableWidget_medical_record.setCellWidget(row_no, 1, check_box)

    def _import_diagnosis(self):
        case_key = self.table_widget_medical_record.field_value(0)
        sql = '''
            SELECT cases.Symptom, cases.DiseaseCode1, cases.DiseaseName1, icd10.EnglishName FROM cases 
                LEFT JOIN icd10 ON cases.DiseaseCode1 = icd10.ICDCode
            WHERE 
                CaseKey = "{0}"
        '''.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        diagnosis = '{0} {1} {2}'.format(row['DiseaseCode1'], row['DiseaseName1'], row['EnglishName'])

        if self.ui.checkBox_import_symptom.isChecked():
           diagnosis += '\n{0}'.format(string_utils.get_str(row['Symptom'], 'utf8'))

        diagnosis += '\n(以下空白)'

        self.ui.textEdit_diagnosis.setText(diagnosis)

    def _import_doctor_comment(self):
        items = (
            "宜休息  日",
            "患者因上述情形，宜多休養",
            "患者因上述情形，宜在家休養，並持續回診治療",
            "患者因上述情形，宜門診持續追蹤治療",
        )
        item, ok = QInputDialog.getItem(
            self, "醫師囑言詞庫", "請選擇醫師囑言詞庫", items, 0, False
        )

        if ok and item:
            item += '\n(以下空白)'
            self.ui.textEdit_doctor_comment.setText(item)

    def _check_diagnosis_completed(self):
        diagnosis = self.ui.textEdit_diagnosis.toPlainText()
        doctor_comment = self.ui.textEdit_doctor_comment.toPlainText()

        if (diagnosis != '' and doctor_comment != '' and
                self.ui.tableWidget_medical_record.rowCount() > 0):
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

    def _write_certificate(self, case_key):
        fields = [
            'CaseKey', 'PatientKey', 'Name', 'CertificateDate', 'CertificateType',
            'InsType', 'TreatType', 'StartDate', 'EndDate', 'Doctor',
            'Diagnosis', 'DoctorComment', 'CertificateFee',
        ]

        start_date = self.ui.tableWidget_medical_record.item(0, 2).text()
        end_date = self.ui.tableWidget_medical_record.item(
            self.ui.tableWidget_medical_record.rowCount()-1, 2).text()

        data = [
            case_key,
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            datetime.datetime.now().strftime('%Y-%m-%d'),
            '診斷證明',
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            start_date,
            end_date,
            self.ui.comboBox_doctor.currentText(),
            self.ui.textEdit_diagnosis.toPlainText(),
            self.ui.textEdit_doctor_comment.toPlainText(),
            self.ui.spinBox_certificate_fee.value(),
        ]

        certificate_key = self.database.insert_record('certificate', fields, data)

        return certificate_key

    def _write_certificate_items(self, certificate_key):
        fields = [
            'CertificateKey', 'CaseKey', 'CaseDate', 'InsType',
        ]

        row_count = self.ui.tableWidget_medical_record.rowCount()
        for row_no in range(row_count):
            check_box = self.ui.tableWidget_medical_record.cellWidget(row_no, 1)
            if not check_box.isChecked():
                continue

            case_key = self.ui.tableWidget_medical_record.item(row_no, 0).text()
            case_date = self.ui.tableWidget_medical_record.item(row_no, 2).text()
            ins_type = self.ui.tableWidget_medical_record.item(row_no, 3).text()
            data = [
                certificate_key,
                case_key,
                case_date,
                ins_type,
            ]

            self.database.insert_record('certificate_items', fields, data)

    def _write_medical_record(self):
        certificate_fee = self.ui.spinBox_certificate_fee.value()

        fields = [
            'PatientKey', 'Name', 'CaseDate', 'DoctorDate',
            'Period', 'InsType', 'TreatType', 'Register',
            'SMaterialFee', 'SelfTotalFee', 'TotalFee',
            'DoctorDone',
        ]
        data = [
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            registration_utils.get_period(self.system_settings),
            '自費',
            '自購',
            self.system_settings.field('使用者'),
            certificate_fee,
            certificate_fee,
            certificate_fee,
            'True',
        ]

        case_key = self.database.insert_record('cases', fields, data)

        return case_key

    def _write_prescript(self, case_key):
        certificate_fee = self.ui.spinBox_certificate_fee.value()

        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey',
            'MedicineName', 'Dosage', 'Unit',
            'Price', 'Amount',
        ]

        data = [
            1,
            case_key,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            2,
            '器材',
            0,
            '診斷證明書',
            1,
            '份',
            certificate_fee,
            certificate_fee,
        ]

        self.database.insert_record('prescript', fields, data)

    def _write_wait(self, case_key):
        fields = ['CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
                  'TreatType', 'InsType', 'Period',
                  'Room', 'RegistNo', 'DoctorDone']

        data = [
            case_key,
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            '複診',
            '一般門診',
            '自購',
            '自費',
            registration_utils.get_period(self.system_settings),
            1,
            0,
            'True',
        ]

        self.database.insert_record('wait', fields, data)

    def _open_past_history(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        # self.dialog_past_history = dialog_past_history.DialogPastHistory(self, self.database, self.system_settings)
        # self.dialog_past_history.show_past_history(patient_key, None)
        dialog = dialog_medical_record_past_history.DialogMedicalRecordPastHistory(
            self, self.database, self.system_settings, None, patient_key, '病歷查詢'
        )

        dialog.exec_()
        dialog.deleteLater()
