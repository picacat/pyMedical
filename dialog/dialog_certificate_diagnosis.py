#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QInputDialog, QMessageBox

import datetime

from classes import table_widget
from dialog import dialog_medical_record_past_history

from libs import ui_utils
from libs import system_utils
from libs import nhi_utils
from libs import string_utils
from libs import number_utils
from libs import registration_utils
from libs import patient_utils


# 診斷證明
class DialogCertificateDiagnosis(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogCertificateDiagnosis, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.certificate_key = args[2]
        self.ui = None
        self.dialog_past_history = None

        self._set_ui()
        self._set_signal()

        if self.certificate_key is not None:
            self._read_certificate()

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
        self.ui.lineEdit_patient_key.returnPressed.connect(self._get_patient)
        self.ui.lineEdit_patient_key.textChanged.connect(self._patient_key_changed)
        self.ui.toolButton_select_patient.clicked.connect(self._select_patient)
        self.ui.toolButton_modify_patient.clicked.connect(self._modify_patient)

        self.ui.dateEdit_start_date.dateChanged.connect(self._start_date_changed)
        self.ui.dateEdit_end_date.dateChanged.connect(self._read_medical_record)
        self.ui.comboBox_ins_type.currentTextChanged.connect(self._read_medical_record)
        self.ui.comboBox_treat_type.currentTextChanged.connect(self._read_medical_record)
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

        self.ui.toolButton_modify_patient.setEnabled(enabled)

    # 設定comboBox
    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_treat_type, ['針傷科', '針灸科', '傷骨科', '內科'], '全部')
        self._set_doctor()

    def _set_doctor(self):
        script = 'select * from person where Position IN ("醫師", "支援醫師") '
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list)

    def accepted_button_clicked(self):
        if self.certificate_key is None:
            self._insert_certificate()
        else:
            self._modify_certificate()

    def _insert_certificate(self):
        if self.ui.checkBox_create_medical_record.isChecked():
            case_key = self._write_medical_record()
            self._write_prescript(case_key)
            self._write_wait(case_key)
        else:
            case_key = 0

        certificate_key = self._write_certificate(case_key)
        self._write_certificate_items(certificate_key)

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
        if ins_type in ['健保', '自費']:
            condition = ' AND InsType = "{0}" '.format(ins_type)

        treat_type = self.ui.comboBox_treat_type.currentText()
        if treat_type == '內科':
            condition += ' AND TreatType IN ("內科", "一般") '
        elif treat_type != '全部':
            condition += ' AND TreatType IN {0} '.format(tuple(treat_type_dict[treat_type]))

        sql = '''
            SELECT CaseKey, CaseDate, InsType, Doctor, DiseaseName1, DiseaseName2, DiseaseName3 FROM cases
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
        self.ui.tableWidget_medical_record.setRowCount(0)
        self.table_widget_medical_record.set_db_data(sql, self._set_table_data, set_focus=False)
        record_count = self.ui.tableWidget_medical_record.rowCount()
        self.ui.label_record_count.setText('門診次數: {0}次'.format(record_count))
        self.ui.label_checked_count.setText('選取次數: {0}次'.format(record_count))
        self._check_diagnosis_completed()
        self._set_doctor_field()

        if self.ui.tableWidget_medical_record.rowCount() <= 0:
            self.ui.tableWidget_medical_record.setRowCount(1)
            self.ui.tableWidget_medical_record.setItem(0, 4, QtWidgets.QTableWidgetItem('查無病歷'))

    def _set_table_data(self, row_no, row):
        disease_list = []
        disease_name1 = string_utils.xstr(row['DiseaseName1'])
        disease_name2 = string_utils.xstr(row['DiseaseName2'])
        disease_name3 = string_utils.xstr(row['DiseaseName3'])
        if disease_name1 != '':
            disease_list.append(disease_name1)
        if disease_name2 != '':
            disease_list.append(disease_name2)
        if disease_name3 != '':
            disease_list.append(disease_name3)

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
        check_box.clicked.connect(self._check_box_medical_record_clicked)
        self.ui.tableWidget_medical_record.setCellWidget(row_no, 1, check_box)

    def _check_box_medical_record_clicked(self):
        checked_count = 0
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            check_box = self.ui.tableWidget_medical_record.cellWidget(row_no, 1)
            if check_box.isChecked():
                checked_count += 1

        self.ui.label_checked_count.setText('選取次數: {0}次'.format(checked_count))

    def _import_diagnosis(self):
        case_key = self.table_widget_medical_record.field_value(0)
        sql = '''
            SELECT 
                cases.Symptom, 
                cases.DiseaseCode1, cases.DiseaseName1, icd10.EnglishName,
                cases.DiseaseCode2, cases.DiseaseName2, 
                cases.DiseaseCode3, cases.DiseaseName3 
            FROM cases 
                LEFT JOIN icd10 ON cases.DiseaseCode1 = icd10.ICDCode
            WHERE 
                CaseKey = "{0}"
        '''.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        diagnosis = '{0} {1} {2}'.format(row['DiseaseCode1'], row['DiseaseName1'], row['EnglishName'])
        if string_utils.xstr(row['DiseaseCode2']) != '':
            diagnosis += '\n{0} {1}'.format(row['DiseaseCode2'], row['DiseaseName2'])
        if string_utils.xstr(row['DiseaseCode3']) != '':
            diagnosis += '\n{0} {1}'.format(row['DiseaseCode3'], row['DiseaseName3'])

        if self.ui.checkBox_import_symptom.isChecked():
           diagnosis += '\n{0}'.format(string_utils.get_str(row['Symptom'], 'utf8'))

        diagnosis += '\n(以下空白)'

        self.ui.textEdit_diagnosis.setText(diagnosis)

    def _import_doctor_comment(self):
        sql = '''
            SELECT * FROM clinic 
            WHERE 
                ClinicType = "{clinic_type}" 
            ORDER BY LENGTH(ClinicName), CAST(CONVERT(`ClinicName` using big5) AS BINARY)
        '''.format(
            clinic_type='醫囑',
        )
        rows = self.database.select_record(sql)
        items = []

        for row in rows:
            items.append(string_utils.xstr(row['ClinicName']))

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

    def _set_doctor_field(self):
        if self.ui.tableWidget_medical_record.rowCount() <= 0:
            return

        doctor_field = self.ui.tableWidget_medical_record.item(0, 5)
        if doctor_field is None:
            return

        doctor = doctor_field.text()
        self.ui.comboBox_doctor.setCurrentText(doctor)

    def _get_start_date(self):
        start_date = None
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            check_box = self.ui.tableWidget_medical_record.cellWidget(row_no, 1)
            if check_box.isChecked():
                start_date = self.ui.tableWidget_medical_record.item(row_no, 2).text()
                break

        return start_date

    def _get_end_date(self):
        end_date = None
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()-1, -1, -1):
            check_box = self.ui.tableWidget_medical_record.cellWidget(row_no, 1)
            if check_box.isChecked():
                end_date = self.ui.tableWidget_medical_record.item(row_no, 2).text()
                break

        return end_date

    def _write_certificate(self, case_key, insert_date=None):
        if self.ui.checkBox_create_medical_record.isChecked():
            certificate_fee = self.ui.spinBox_certificate_fee.value()
        else:
            certificate_fee = None

        fields = [
            'CaseKey', 'PatientKey', 'Name', 'CertificateDate', 'CertificateType',
            'InsType', 'TreatType', 'StartDate', 'EndDate', 'Doctor',
            'Diagnosis', 'DoctorComment', 'CertificateFee',
        ]

        start_date = self._get_start_date()
        end_date = self._get_end_date()
        if insert_date is None:
            certificate_date = datetime.datetime.now().strftime('%Y-%m-%d')
        else:
            certificate_date = insert_date

        data = [
            case_key,
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            certificate_date,
            '診斷證明',
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            start_date,
            end_date,
            self.ui.comboBox_doctor.currentText(),
            self.ui.textEdit_diagnosis.toPlainText(),
            self.ui.textEdit_doctor_comment.toPlainText(),
            certificate_fee,
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

        case_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        period = registration_utils.get_current_period(self.system_settings)
        charge_date = None
        charge_period = None
        charge_done = 'False'

        if self.system_settings.field('自動完成批價作業') == 'Y':
            charge_date = case_date
            charge_period = period
            charge_done = 'True'

        fields = [
            'PatientKey', 'Name', 'CaseDate', 'DoctorDate',
            'Period', 'InsType', 'TreatType', 'Register',
            'SMaterialFee', 'SelfTotalFee', 'TotalFee',
            'DoctorDone',
            'ChargeDate', 'ChargePeriod', 'ChargeDone',
        ]
        data = [
            self.ui.lineEdit_patient_key.text(), self.ui.lineEdit_name.text(), case_date, case_date,
            period, '自費', '自購', self.system_settings.field('使用者'),
            certificate_fee,
            certificate_fee,
            certificate_fee,
            'True',
            charge_date, charge_period, charge_done,
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
        case_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        period = registration_utils.get_current_period(self.system_settings)
        charge_done = 'False'

        if self.system_settings.field('自動完成批價作業') == 'Y':
            charge_done = 'True'

        fields = [
            'CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
            'TreatType', 'InsType', 'Period',
            'Room', 'RegistNo', 'DoctorDone',
            'ChargeDone',
        ]

        data = [
            case_key, case_date, self.ui.lineEdit_patient_key.text(), self.ui.lineEdit_name.text(), '複診', '一般門診',
            '自購', '自費', period,
            1, 0, 'True',
            charge_done,
        ]

        self.database.insert_record('wait', fields, data)

    def _open_past_history(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        # database.dialog_past_history = dialog_past_history.DialogPastHistory(database, database.database, database.system_settings)
        # database.dialog_past_history.show_past_history(primary_key, None)
        dialog = dialog_medical_record_past_history.DialogMedicalRecordPastHistory(
            self, self.database, self.system_settings, None, patient_key, '診斷證明'
        )

        dialog.exec_()
        dialog.deleteLater()

    def _get_certificate_row(self, certificate_key):
        sql = '''
            SELECT * FROM certificate
            WHERE
                CertificateKey = {certificate_key} AND
                CertificateType = "診斷證明"
        '''.format(
            certificate_key=certificate_key
        )
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return None

        row = rows[0]

        return row

    def _read_certificate(self):
        row = self._get_certificate_row(self.certificate_key)
        if row is None:
            return

        self.ui.lineEdit_patient_key.setText(string_utils.xstr(row['PatientKey']))
        self.ui.dateEdit_start_date.setDate(row['StartDate'])
        self.ui.dateEdit_end_date.setDate(row['EndDate'])
        self.ui.comboBox_ins_type.setCurrentText(string_utils.xstr(row['InsType']))
        self.ui.comboBox_treat_type.setCurrentText(string_utils.xstr(row['TreatType']))
        self.ui.comboBox_doctor.setCurrentText(string_utils.xstr(row['Doctor']))
        self.ui.spinBox_certificate_fee.setValue(number_utils.get_integer(row['CertificateFee']))
        self.ui.textEdit_diagnosis.setText(string_utils.xstr(row['Diagnosis']))
        self.ui.textEdit_doctor_comment.setText(string_utils.xstr(row['DoctorComment']))

        if self.ui.spinBox_certificate_fee.value() > 0:
            self.ui.checkBox_create_medical_record.setChecked(True)

        self._set_medical_record_check_box(self.certificate_key)
        self._check_box_medical_record_clicked()

    def _set_medical_record_check_box(self, certificate_key):
        sql = '''
            SELECT * FROM certificate_items
            WHERE
                CertificateKey = {certificate_key}
        '''.format(
            certificate_key=certificate_key,
        )

        rows = self.database.select_record(sql)

        case_key_list = []
        for row in rows:
            case_key_list.append(row['CaseKey'])

        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            case_key = number_utils.get_integer(self.ui.tableWidget_medical_record.item(row_no, 0).text())
            check_box = self.ui.tableWidget_medical_record.cellWidget(row_no, 1)
            if case_key not in case_key_list:
                check_box.setChecked(False)

    def _modify_certificate(self):
        row = self._get_certificate_row(self.certificate_key)
        if row is None:
            return

        case_key = row['CaseKey']
        certificate_date = row['CertificateDate']

        certificate_key = self._write_certificate(case_key, certificate_date)
        self._write_certificate_items(certificate_key)

        self.database.exec_sql('DELETE FROM certificate WHERE CertificateKey = {0}'.format(self.certificate_key))
        self.database.exec_sql('DELETE FROM certificate_items WHERE CertificateKey = {0}'.format(self.certificate_key))

    def _patient_key_changed(self):
        patient_key = self.ui.lineEdit_patient_key.text()

        if patient_key == '':
            self._clear_patient_data()
            self._set_group_box(False)
            return

        if patient_key.isdigit() and len(patient_key) <= 6:
            self._set_line_edit_patient_data(patient_key)
        else:
            self._clear_patient_data()

    def _modify_patient(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        fields = ['Telephone', 'Address']
        data = [
            self.ui.lineEdit_telephone.text(),
            self.ui.lineEdit_address.text(),
        ]
        self.database.update_record('patient', fields, 'PatientKey', patient_key, data)
        system_utils.show_message_box(
            QMessageBox.Information,
            '資料存檔完成',
            '<h3>病患電話及地址存檔完成.</h3>',
            '只開放修改電話及地址'
        )

    def _select_patient(self):
        patient_key = patient_utils.select_patient(
            self, self.database, self.system_settings, 'patient', 'PatientKey', ''
        )
        if patient_key in ['', None]:
            return

        self._set_line_edit_patient_data(patient_key)

    def _get_patient(self):
        keyword = self.ui.lineEdit_patient_key.text()

        patient_key = patient_utils.get_patient_by_keyword(
            self, self.database, self.system_settings,
            'patient', 'PatientKey', keyword
        )
        if patient_key in ['', None]:
            return

        self._set_line_edit_patient_data(patient_key)

    def _set_line_edit_patient_data(self, patient_key):
        self.ui.lineEdit_patient_key.setText(string_utils.xstr(patient_key))

        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        self._set_patient_data(row)
        self._set_group_box(True)
        self._read_medical_record()
