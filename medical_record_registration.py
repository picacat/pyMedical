#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import personnel_utils
from libs import case_utils
from libs import system_utils
from libs import cshis_utils
from libs import number_utils


# 病歷資料 2018.01.31
class MedicalRecordRegistration(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecordRegistration, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.call_from = args[3]
        self.medical_record = None
        self.patient_data = None
        self.ui = None
        self.data_changed = False
        self.cshis_data_changed = False

        self._set_ui()
        self._read_case_registration()
        self._set_signal()  # 先讀完資料才設定信號

        if self.call_from == '新增自費病歷':
            self._set_new_self_medical_record()
            self.case_key = -1

        self.user_name = self.system_settings.field('使用者')
        self._set_permission()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MEDICAL_RECORD_REGISTRATION, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.table_widget_prescript_sign = table_widget.TableWidget(
            self.ui.tableWidget_prescript_sign, self.database)
        self._set_combo_box()
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.lineEdit_case_date.textChanged.connect(self._set_data_changed)
        self.ui.comboBox_period.currentTextChanged.connect(self._set_data_changed)
        self.ui.lineEdit_completion_time.textChanged.connect(self._set_data_changed)
        self.ui.lineEdit_charge_time.textChanged.connect(self._set_data_changed)
        self.ui.comboBox_charge_period.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_visit.currentTextChanged.connect(self._set_data_changed)
        self.ui.lineEdit_patient_key.textChanged.connect(self._set_data_changed)
        self.ui.lineEdit_name.textChanged.connect(self._set_data_changed)
        self.ui.comboBox_ins_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_reg_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_room.currentTextChanged.connect(self._set_data_changed)
        self.ui.lineEdit_regist_no.textChanged.connect(self._set_data_changed)

        self.ui.comboBox_registrar.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_cashier.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_doctor.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_pharmacist.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_massager.currentTextChanged.connect(self._set_data_changed)

        self.ui.comboBox_apply_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_pharmacy_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_share_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_treat_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_injury_type.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_xcard.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_card.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_course.currentTextChanged.connect(self._set_data_changed)
        self.ui.comboBox_tour_area.currentTextChanged.connect(self._set_data_changed)

        self.ui.comboBox_upload_type.currentTextChanged.connect(self._cshis_data_changed)
        self.ui.comboBox_treat_after_check.currentTextChanged.connect(self._cshis_data_changed)

        self.ui.lineEdit_special_code.textChanged.connect(self.set_special_code)
        self.ui.checkBox_designated_doctor.clicked.connect(self._set_data_changed)
        self.ui.checkBox_designated_massager.clicked.connect(self._set_data_changed)

    def _set_permission(self):
        if self.call_from == '醫師看診作業':
            return

        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '病歷資料', '病歷修正', self.user_name) == 'Y':
            return

        self.ui.groupBox_registration.setEnabled(False)
        self.ui.groupBox_ins_apply.setEnabled(False)
        self.ui.groupBox_ic_card.setEnabled(False)

    def _set_table_width(self):
        width = [200, 90, 430]
        self.table_widget_prescript_sign.set_table_heading_width(width)

    # 檢查資料是否異動
    def _set_data_changed(self):
        self.data_changed = True
        sender_name = self.sender().objectName()

        if sender_name == 'comboBox_share_type':
            if self.ui.comboBox_share_type.currentText() == '職業傷害':
                if self.ui.comboBox_injury_type.currentText() not in ['職業傷害', '職業病']:
                    self.ui.comboBox_injury_type.setCurrentText('職業傷害')
                card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
                if card != 'IC06':
                    self.ui.comboBox_card.setCurrentText(nhi_utils.INJURY_CARD_DICT['IC06'])
            else:
                if self.ui.comboBox_injury_type.currentText() != '普通疾病':
                    self.ui.comboBox_injury_type.setCurrentText('普通疾病')

        elif sender_name == 'comboBox_injury_type':
            if self.ui.comboBox_injury_type.currentText() in ['職業傷害', '職業病']:
                if self.ui.comboBox_share_type.currentText() != '職業傷害':
                    self.ui.comboBox_share_type.setCurrentText('職業傷害')
                card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
                if card != 'IC06':
                    self.ui.comboBox_card.setCurrentText(nhi_utils.INJURY_CARD_DICT['IC06'])
        elif sender_name == 'comboBox_card':
            card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
            if card == 'IC06':
                if self.ui.comboBox_injury_type.currentText() not in ['職業傷害', '職業病']:
                    self.ui.comboBox_injury_type.setCurrentText('職業傷害')
        elif sender_name == 'comboBox_pharmacy_type':
            ins_prescript = self.parent.tab_list[0]
            if ins_prescript is None:
                return

            pharmacy_type = self.ui.comboBox_pharmacy_type.currentText()
            combo_box_pharmacy = ins_prescript.checkBox_pharmacy
            if pharmacy_type == '申報' and not combo_box_pharmacy.isChecked():
                combo_box_pharmacy.setChecked(True)
            elif pharmacy_type == '不申報' and combo_box_pharmacy.isChecked():
                combo_box_pharmacy.setChecked(False)

            self.parent.calculate_ins_fees()

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD, None)
        ui_utils.set_combo_box(self.ui.comboBox_charge_period, nhi_utils.PERIOD, None)
        ui_utils.set_combo_box(self.ui.comboBox_visit, nhi_utils.VISIT, None)
        ui_utils.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_reg_type, nhi_utils.REG_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)
        ui_utils.set_combo_box(
            self.ui.comboBox_tour_area,
            list(nhi_utils.TOUR_AREA_DICT.keys()),
            None
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_registrar,
            personnel_utils.get_personnel(self.database, '全部'), None,
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_cashier,
            personnel_utils.get_personnel(self.database, '全部'), None,
        )

        ui_utils.set_combo_box(
            self.ui.comboBox_doctor,
            personnel_utils.get_personnel(self.database, '全部醫師'), None,
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_pharmacist,
            personnel_utils.get_personnel(self.database, '藥師'), None,
        )
        ui_utils.set_combo_box(
            self.ui.comboBox_massager,
            personnel_utils.get_personnel(self.database, '推拿師父'), None,
        )
        ui_utils.set_combo_box(self.ui.comboBox_apply_type, nhi_utils.APPLY_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_pharmacy_type, nhi_utils.PHARMACY_APPLY_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_share_type, nhi_utils.SHARE_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_treat_type, nhi_utils.TREAT_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_injury_type, nhi_utils.INJURY_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_xcard, nhi_utils.ABNORMAL_CARD_WITH_HINT, None)
        ui_utils.set_combo_box(self.ui.comboBox_card, nhi_utils.CARD, None, '欠卡')
        ui_utils.set_combo_box(self.ui.comboBox_course, nhi_utils.COURSE, None)

        ui_utils.set_combo_box(self.ui.comboBox_upload_type, nhi_utils.UPLOAD_TYPE, None)
        ui_utils.set_combo_box(self.ui.comboBox_treat_after_check, nhi_utils.TREAT_AFTER_CHECK, None)

    def set_special_code(self):
        self.data_changed = True

        if self.ui.lineEdit_special_code.text() != '':
            self.parent.ui.lineEdit_disease_code1.setStyleSheet('color:red')
            self.parent.ui.lineEdit_disease_name1.setStyleSheet('color:red')
        else:
            self.parent.ui.lineEdit_disease_code1.setStyleSheet('color:black')
            self.parent.ui.lineEdit_disease_name1.setStyleSheet('color:black')

    def _read_case_registration(self):
        sql = '''
            SELECT * FROM cases WHERE 
            CaseKey = {0}
        '''.format(self.case_key)
        row = self.database.select_record(sql)[0]
        self._set_registration_data(row)
        self._set_personnel(row)
        self._set_ic_card_data(row)
        self._set_ins_data(row)
        self._set_prescript_sign(row)

    def _set_registration_data(self, row):
        self.ui.lineEdit_case_date.setText(string_utils.xstr(row['CaseDate']))
        self.ui.comboBox_period.setCurrentText(string_utils.xstr(row['Period']))
        self.ui.lineEdit_completion_time.setText(string_utils.xstr(row['DoctorDate']))
        self.ui.lineEdit_charge_time.setText(string_utils.xstr(row['ChargeDate']))
        self.ui.comboBox_charge_period.setCurrentText(string_utils.xstr(row['ChargePeriod']))
        self.ui.comboBox_visit.setCurrentText(string_utils.xstr(row['Visit']))
        self.ui.lineEdit_patient_key.setText(string_utils.xstr(row['PatientKey']))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.comboBox_ins_type.setCurrentText(string_utils.xstr(row['InsType']))
        self.ui.comboBox_reg_type.setCurrentText(string_utils.xstr(row['RegistType']))
        self.ui.comboBox_room.setCurrentText(string_utils.xstr(row['Room']))
        self.ui.lineEdit_regist_no.setText(string_utils.xstr(row['RegistNo']))
        self.ui.comboBox_tour_area.setCurrentText(string_utils.xstr(row['TourArea']))

    def _set_personnel(self, row):
        system_utils.set_combo_box_item(self.ui.comboBox_registrar, string_utils.xstr(row['Register']))
        system_utils.set_combo_box_item(self.ui.comboBox_cashier, string_utils.xstr(row['Cashier']))
        system_utils.set_combo_box_item(self.ui.comboBox_pharmacist, string_utils.xstr(row['Pharmacist']))
        system_utils.set_combo_box_item(self.ui.comboBox_massager, string_utils.xstr(row['Massager']))
        system_utils.set_combo_box_item(self.ui.comboBox_doctor, string_utils.xstr(row['Doctor']))

        if row['DesignatedDoctor'] == 'True':
            self.ui.checkBox_designated_doctor.setChecked(True)
        if row['DesignatedMassager'] == 'True':
            self.ui.checkBox_designated_massager.setChecked(True)

    def _set_ic_card_data(self, row):
        card_datetime = case_utils.extract_security_xml(row['Security'], '寫卡時間')
        seq_number = case_utils.extract_security_xml(row['Security'], '健保卡序')
        clinic_id = case_utils.extract_security_xml(row['Security'], '院所代號')
        sam_id = case_utils.extract_security_xml(row['Security'], '安全模組')
        signature = case_utils.extract_security_xml(row['Security'], '安全簽章')
        upload_time = case_utils.extract_security_xml(row['Security'], '上傳時間')
        upload_type = case_utils.extract_security_xml(row['Security'], '資料格式')
        treat_after_check = case_utils.extract_security_xml(row['Security'], '補卡註記')
        prescript_sign_time = case_utils.extract_security_xml(row['Security'], '醫令時間')

        self.ui.lineEdit_ic_registration.setText(card_datetime)
        self.ui.lineEdit_seq_number.setText(seq_number)
        self.ui.lineEdit_clinic_id.setText(clinic_id)
        self.ui.lineEdit_sam_id.setText(sam_id)
        self.ui.lineEdit_upload_time.setText(upload_time)

        self.ui.comboBox_upload_type.setCurrentText(cshis_utils.UPLOAD_TYPE_DICT[upload_type])
        self.ui.comboBox_treat_after_check.setCurrentText(cshis_utils.TREAT_AFTER_CHECK_DICT[treat_after_check])

        self.ui.lineEdit_prescript_sign_time.setText(prescript_sign_time)
        self.ui.textEdit_signature.setPlainText(signature)

    def _set_ins_data(self, row):
        self.ui.comboBox_apply_type.setCurrentText(string_utils.xstr(row['ApplyType']))
        self.ui.comboBox_pharmacy_type.setCurrentText(string_utils.xstr(row['PharmacyType']))
        self.ui.comboBox_share_type.setCurrentText(string_utils.xstr(row['Share']))
        self.ui.comboBox_treat_type.setCurrentText(string_utils.xstr(row['TreatType']))
        self.ui.comboBox_injury_type.setCurrentText(string_utils.xstr(row['Injury']))

        xcard = string_utils.xstr(row['XCard'])
        if xcard in nhi_utils.ABNORMAL_CARD:
            xcard = nhi_utils.ABNORMAL_CARD_DICT[xcard]

        self.ui.comboBox_xcard.setCurrentText(xcard)

        card =  string_utils.xstr(row['Card'])
        if card in nhi_utils.ABNORMAL_CARD:
            card = nhi_utils.ABNORMAL_CARD_DICT[card]

        if card not in nhi_utils.ABNORMAL_CARD_WITH_HINT + nhi_utils.CARD:
            self.ui.comboBox_card.insertItem(1, card)
        self.ui.comboBox_card.setCurrentText(card)

        self.ui.comboBox_course.setCurrentText(string_utils.xstr(row['Continuance']))
        self.ui.lineEdit_special_code.setText(string_utils.xstr(row['SpecialCode']))

        self.ui.lineEdit_ins_total_fee.setText(string_utils.xstr(number_utils.get_integer(row['InsTotalFee'])))
        # database.ui.lineEdit_share_fee.setText(
        #     string_utils.xstr(
        #         number_utils.get_integer(medical_row['DiagShareFee']) +
        #         number_utils.get_integer(medical_row['DrugShareFee'])
        #     )
        # )
        # database.ui.lineEdit_ins_apply_fee.setText(string_utils.xstr(number_utils.get_integer(medical_row['InsApplyFee'])))

    def _set_treat_sign(self):
        sql = '''
            SELECT * FROM presextend WHERE
            PrescriptKey = {0} AND ExtendType = "處置簽章"
        '''.format(self.case_key)
        self.table_widget_prescript_sign.set_db_data(sql, self._set_treat_sign_data)

    def _set_treat_sign_data(self, rec_no, rec):
        sql = '''
            SELECT Treatment FROM cases WHERE
            CaseKey = {0}
        '''.format(self.case_key)
        row = self.database.select_record(sql)[0]
        treatment = string_utils.xstr(row['Treatment'])
        ins_code = nhi_utils.get_treat_code(self.database, self.case_key)
        prescript_sign_rec = [
            treatment,
            ins_code,
            string_utils.xstr(rec['Content']),
        ]

        for column in range(len(prescript_sign_rec)):
            self.ui.tableWidget_prescript_sign.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(prescript_sign_rec[column])
            )

    def _set_prescript_sign(self, row):
        start_index = 0

        if string_utils.xstr(row['Treatment']) != '':
            self._set_treat_sign()
            start_index = 1

        sql = '''
            SELECT 
                prescript.PrescriptKey, prescript.MedicineName, prescript.InsCode, 
                presextend.Content FROM prescript
            LEFT JOIN presextend ON presextend.PrescriptKey = prescript.PrescriptKey 
            WHERE
            prescript.CaseKey = {0} AND
            prescript.MedicineSet = 1 AND prescript.InsCode IS NOT NULL AND
            presextend.Content IS NOT NULL
            ORDER BY prescript.PrescriptNo, prescript.PrescriptKey
        '''.format(self.case_key)
        self.table_widget_prescript_sign.set_db_data(sql, self._set_prescript_sign_data, None, start_index)

    def _set_prescript_sign_data(self, row_no, row):
        prescript_sign_rec = [
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['Content']),
        ]

        for column in range(len(prescript_sign_rec)):
            self.ui.tableWidget_prescript_sign.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(prescript_sign_rec[column])
            )

    def save_record(self):
        if not self.data_changed:
            return

        fields = [
            'CaseDate', 'Period', 'DoctorDate', 'ChargeDate', 'ChargePeriod',
            'Visit', 'PatientKey', 'Name',
            'InsType', 'RegistType', 'TourArea', 'Room', 'RegistNo',
            'Register', 'Cashier', 'Doctor', 'Pharmacist', 'Massager',
            'ApplyType', 'PharmacyType', 'Share', 'TreatType', 'Injury',
            'XCard', 'Card', 'Continuance', 'SpecialCode',
            'DesignatedDoctor', 'DesignatedMassager',
        ]
        xcard = string_utils.xstr(self.ui.comboBox_xcard.currentText()).split(' ')[0]
        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]

        massager = self.ui.comboBox_massager.currentText()
        designated_doctor = 'False'
        designated_massager = 'False'

        if self.ui.checkBox_designated_doctor.isChecked():
            designated_doctor = 'True'
        if massager != '' and self.ui.checkBox_designated_massager.isChecked():
            designated_massager = 'True'


        data = [
            self.ui.lineEdit_case_date.text(),
            self.ui.comboBox_period.currentText(),
            self.ui.lineEdit_completion_time.text(),
            self.ui.lineEdit_charge_time.text(),
            self.ui.comboBox_charge_period.currentText(),
            self.ui.comboBox_visit.currentText(),
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_tour_area.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.lineEdit_regist_no.text(),

            self.ui.comboBox_registrar.currentText(),
            self.ui.comboBox_cashier.currentText(),
            self.ui.comboBox_doctor.currentText(),
            self.ui.comboBox_pharmacist.currentText(),
            massager,

            self.ui.comboBox_apply_type.currentText(),
            self.ui.comboBox_pharmacy_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_injury_type.currentText(),
            xcard,
            card,
            self.ui.comboBox_course.currentText(),
            self.ui.lineEdit_special_code.text(),
            designated_doctor,
            designated_massager,
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

        if self.cshis_data_changed:
            upload_type = self.ui.comboBox_upload_type.currentText().split('-')[0]
            treat_after_check = self.ui.comboBox_treat_after_check.currentText().split('-')[0]

            case_utils.update_xml(
                self.database, 'cases', 'Security', 'upload_type', upload_type, 'CaseKey', self.case_key,
            )  # 更新健保寫卡資料
            case_utils.update_xml(
                self.database, 'cases', 'Security', 'treat_after_check', treat_after_check, 'CaseKey', self.case_key,
            )  # 更新健保寫卡資料

    def _cshis_data_changed(self):
        self.cshis_data_changed = True

    def _set_new_self_medical_record(self):
        user_name = self.system_settings.field('使用者')

        self.ui.comboBox_ins_type.setCurrentText('自費')
        self.ui.lineEdit_completion_time.setText('')
        self.ui.lineEdit_charge_time.setText('')

        self.ui.comboBox_registrar.setCurrentText(user_name)
        self.ui.comboBox_doctor.setCurrentText(user_name)
        self.ui.comboBox_cashier.setCurrentText(user_name)
        self.ui.comboBox_charge_period.setCurrentText(None)

        self.ui.comboBox_upload_type.setCurrentText('1-正常上傳')
        self.ui.comboBox_treat_after_check.setCurrentText('1-正常')
        self.ui.lineEdit_clinic_id.setText('')
        self.ui.lineEdit_sam_id.setText('')
        self.ui.lineEdit_ic_registration.setText('')
        self.ui.lineEdit_seq_number.setText('')
        self.ui.lineEdit_prescript_sign_time.setText('')
        self.ui.lineEdit_upload_time.setText('')
        self.ui.textEdit_signature.setPlainText('')

        self.ui.comboBox_reg_type.setCurrentText(self.system_settings.field('掛號類別'))
        self.ui.comboBox_treat_type.setCurrentText('內科')
        self.ui.comboBox_card.setCurrentText('不需取得')
        self.ui.comboBox_course.setCurrentText(None)
        self.ui.comboBox_xcard.setCurrentText(None)
        self.ui.lineEdit_special_code.setText('')
        self.ui.lineEdit_ins_total_fee.setText('')

        self.ui.tableWidget_prescript_sign.setRowCount(0)
