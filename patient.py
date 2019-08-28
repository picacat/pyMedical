#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import date_utils
from libs import validator_utils
from libs import patient_utils
from dialog import dialog_address
from dialog import dialog_select_remote_patient


# 病患基本資料 2018.01.31
class Patient(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Patient, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_key = args[2]
        self.call_from = args[3]
        self.ic_card = args[4]
        self.patient = None
        self.ui = None
        self.name_warning = False
        self.quit_save = False

        self._set_ui()
        self._set_validator()
        self._set_signal()

        if self.ic_card:
            self._set_patient_by_ic_card()
        elif self.patient_key is not None:
            self._read_patient()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_PATIENT, self)
        system_utils.set_css(self, self.system_settings)
        self._set_combobox()
        self.ui.lineEdit_patient_key.setText(string_utils.xstr(self.database.get_last_auto_increment_key('patient')))
        self.ui.lineEdit_init_date.setText(date_utils.now_to_str())

    def _set_validator(self):
        self.ui.lineEdit_birthday.setValidator(validator_utils.set_validator('日期格式'))
        self.ui.lineEdit_id.setValidator(validator_utils.set_validator('身分證格式'))

    # 設定信號
    def _set_signal(self):
        self.ui.action_save.triggered.connect(self._save_patient)
        self.ui.action_close.triggered.connect(self.close_patient)
        self.ui.action_copy_remote_patient.triggered.connect(self._copy_remote_patient)
        self.ui.toolButton_address.clicked.connect(self._open_address_dict)
        self.ui.lineEdit_birthday.editingFinished.connect(self._validate_birthday)
        self.ui.lineEdit_name.editingFinished.connect(self._validate_name)
        self.ui.lineEdit_id.editingFinished.connect(self._validate_id)
        self.ui.lineEdit_telephone.editingFinished.connect(self._phone_editing_finished)
        self.ui.lineEdit_cellphone.editingFinished.connect(self._phone_editing_finished)

    def _set_combobox(self):
        ui_utils.set_combo_box(self.ui.comboBox_gender, nhi_utils.GENDER, None)
        ui_utils.set_combo_box(self.ui.comboBox_nationality, nhi_utils.NATIONALITY, None)
        ui_utils.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INSURED_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_marriage, nhi_utils.MARRIAGE, None)
        ui_utils.set_combo_box(self.ui.comboBox_education, nhi_utils.EDUCATION, None)
        ui_utils.set_combo_box(self.ui.comboBox_occupation, nhi_utils.OCCUPATION, None)
        ui_utils.set_combo_box(self.ui.comboBox_discount, '掛號優待', self.database)

    def _validate_birthday(self):
        if self.ic_card:
            return

        west_date = date_utils.date_to_west_date(self.ui.lineEdit_birthday.text())
        self.ui.lineEdit_birthday.setText(west_date)

    def _validate_name(self):
        if self.ic_card:
            return

        if self.patient_key is not None:  # 此人已存在
            return

        name = self.ui.lineEdit_name.text()
        if name == '':
            return

        sql = 'SELECT * FROM patient WHERE Name = "{0}"'.format(name)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        if self.name_warning:
            return

        self.name_warning = True
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('相同姓名病患已存在')
        msg_box.setText(
            '''
            <font size='4' color='red'>
            <b>相同姓名的病患已存在！以下是相同病患的資料:'<br>
            </font>
            <font size='4' color='blue'>
               病歷號碼: {0}<br>
               病患姓名: {1}<br>
               出生日期: {2}<br>
               身分證號: {3}
            </b>
            </font>
            ''' .format(rows[0]['PatientKey'], rows[0]['Name'], rows[0]['Birthday'], rows[0]['ID']))
        msg_box.setInformativeText("如果確定不同人，請繼續編輯病患資料.")
        msg_box.addButton(QPushButton("不同病患, 繼續編輯"), QMessageBox.NoRole)  # 0
        msg_box.addButton(QPushButton("此人為相同病患, 確定離開編輯"), QMessageBox.AcceptRole)  # 1
        quit_patient = msg_box.exec_()
        if quit_patient:
            self.quit_save = True
            self.close_patient()
        else:
            self.ui.lineEdit_birthday.setFocus()

    def _validate_id(self):
        if self.ic_card:
            return

        if not validator_utils.verify_id(self.ui.lineEdit_id.text()):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('身分證檢查錯誤')
            msg_box.setText("<font size='4' color='red'><b>身分證可能有誤，請確認身分證號碼是否輸入正確!</b></font>")
            msg_box.setInformativeText("如果確定輸入正確，可以忽略此項警告.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
        self._set_gender()
        self._set_nationality()

    def _set_gender(self):
        patient_id = self.ui.lineEdit_id.text()
        self.ui.comboBox_gender.setCurrentText(patient_utils.get_gender(patient_id[1]))

    def _set_nationality(self):
        patient_id = self.ui.lineEdit_id.text()
        self.ui.comboBox_nationality.setCurrentText(patient_utils.get_nationality(patient_id[1]))

    def _read_patient(self):
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.patient_key)
        self.patient = self.database.select_record(sql)[0]
        self._set_patient()

    def _set_patient_by_ic_card(self):
        self.ui.lineEdit_card_no.setText(self.ic_card.basic_data['card_no'])
        self.ui.lineEdit_name.setText(self.ic_card.basic_data['name'])
        self.ui.lineEdit_id.setText(self.ic_card.basic_data['patient_id'])
        self.ui.lineEdit_birthday.setText(self.ic_card.basic_data['birthday'])
        self.ui.comboBox_ins_type.setCurrentText(self.ic_card.basic_data['insured_mark'])
        self.ui.comboBox_gender.setCurrentText(self.ic_card.basic_data['gender'])
        self._set_nationality()

    def _set_patient(self):
        self.ui.lineEdit_patient_key.setText(string_utils.xstr(self.patient['PatientKey']))
        self.ui.lineEdit_card_no.setText(string_utils.xstr(self.patient['CardNo']))
        self.ui.lineEdit_name.setText(string_utils.xstr(self.patient['Name']))
        self.ui.lineEdit_id.setText(string_utils.xstr(self.patient['ID']))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(self.patient['Birthday']))
        self.ui.lineEdit_init_date.setText(string_utils.xstr(self.patient['InitDate']))
        self.ui.lineEdit_telephone.setText(string_utils.xstr(self.patient['Telephone']))
        self.ui.lineEdit_cellphone.setText(string_utils.xstr(self.patient['Cellphone']))
        self.ui.lineEdit_email.setText(string_utils.xstr(self.patient['Email']))
        self.ui.lineEdit_address.setText(string_utils.xstr(self.patient['Address']))
        self.ui.lineEdit_family.setText(string_utils.xstr(self.patient['FamilyPatientKey']))
        self.ui.lineEdit_family_telephone.setText(string_utils.xstr(self.patient['Reference']))
        self.ui.comboBox_gender.setCurrentText(self.patient['Gender'])
        self.ui.comboBox_ins_type.setCurrentText(self.patient['InsType'])
        self.ui.comboBox_nationality.setCurrentText(self.patient['Nationality'])
        self.ui.comboBox_marriage.setCurrentText(self.patient['Marriage'])
        self.ui.comboBox_education.setCurrentText(self.patient['Education'])
        self.ui.comboBox_occupation.setCurrentText(self.patient['Occupation'])
        self.ui.comboBox_discount.setCurrentText(self.patient['DiscountType'])
        self._set_patient_text_fields()

    def _set_patient_text_fields(self):
        try:
            self.ui.textEdit_allergy.setText(string_utils.get_str(self.patient['Allergy'], 'utf8'))
        except TypeError:
            pass

        try:
            self.ui.textEdit_history.setText(string_utils.get_str(self.patient['History'], 'utf8'))
        except TypeError:
            pass

        try:
            self.ui.textEdit_remark.setText(string_utils.get_str(self.patient['Remark'], 'utf8'))
        except TypeError:
            pass

        try:
            self.ui.textEdit_description.setText(string_utils.get_str(self.patient['Description'], 'utf8'))
        except TypeError:
            pass

    def _save_patient(self):
        self.ui.lineEdit_patient_key.setFocus(True)

        if self.quit_save:
            return

        fields = ['CardNo', 'Name', 'ID', 'Birthday', 'InitDate', 'Telephone', 'Cellphone', 'Email',
                  'Address', 'FamilyPatientKey', 'Reference', 'Gender', 'InsType', 'Nationality', 'Marriage',
                  'Education', 'Occupation', 'DiscountType', 'Allergy', 'History', 'Remark', 'Description']
        data = [
            self.ui.lineEdit_card_no.text(),
            self.ui.lineEdit_name.text(),
            self.ui.lineEdit_id.text(),
            self.ui.lineEdit_birthday.text(),
            self.ui.lineEdit_init_date.text(),
            self.ui.lineEdit_telephone.text(),
            self.ui.lineEdit_cellphone.text(),
            self.ui.lineEdit_email.text(),
            self.ui.lineEdit_address.text(),
            self.ui.lineEdit_family.text(),
            self.ui.lineEdit_family_telephone.text(),
            self.ui.comboBox_gender.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_nationality.currentText(),
            self.ui.comboBox_marriage.currentText(),
            self.ui.comboBox_education.currentText(),
            self.ui.comboBox_occupation.currentText(),
            self.ui.comboBox_discount.currentText(),
            self.ui.textEdit_allergy.toPlainText(),
            self.ui.textEdit_history.toPlainText(),
            self.ui.textEdit_remark.toPlainText(),
            self.ui.textEdit_description.toPlainText(),
        ]
        if self.patient is None:
            last_row_id = self.database.insert_record('patient', fields, data)
            self.parent.set_new_patient(last_row_id)
        else:
            self.database.update_record('patient', fields, 'PatientKey', self.patient_key, data)

        self.close_patient()

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_patient(self):
        self.close_all()
        self.close_tab()

    def _open_address_dict(self):
        dialog = dialog_address.DialogAddress(
            self, self.database, self.system_settings,
            self.ui.lineEdit_address,
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

    def _phone_editing_finished(self):
        if self.ui.lineEdit_address.text().strip() != '':  # 已經輸入過就不要自動帶入
            return

        sender_name = self.sender().objectName()
        if sender_name == 'lineEdit_telephone':
            line_edit_phone = self.ui.lineEdit_telephone
            field = 'Telephone'
        else:
            line_edit_phone = self.ui.lineEdit_cellphone
            field = 'Cellphone'

        phone_no = line_edit_phone.text().strip()

        sql = '''
            SELECT Address FROM patient
            WHERE
                {field} = "{phone_no}"
            LIMIT 1
        '''.format(
            field=field,
            phone_no=phone_no,
        )
        try:
            rows = self.database.select_record(sql)
        except:
            return

        if len(rows) > 0:
            self.ui.lineEdit_address.setText(string_utils.xstr(rows[0]['Address']))

    # 拷貝分院病患基本資料
    def _copy_remote_patient(self):
        dialog = dialog_select_remote_patient.DialogSelectRemotePatient(
            self, self.database, self.system_settings,
        )
        if dialog.exec_():
            remote_patient = dialog.get_remote_patient()
            self.ui.lineEdit_name.setText(remote_patient['Name'])
            self.ui.lineEdit_birthday.setText(remote_patient['Birthday'])
            self.ui.comboBox_gender.setCurrentText(remote_patient['Gender'])
            self.ui.lineEdit_id.setText(remote_patient['ID'])
            self.ui.comboBox_ins_type.setCurrentText(remote_patient['InsType'])
            self.ui.lineEdit_telephone.setText(remote_patient['Telephone'])
            self.ui.lineEdit_cellphone.setText(remote_patient['Cellphone'])
            self.ui.lineEdit_address.setText(remote_patient['Address'])
            self._set_nationality()

        del dialog
