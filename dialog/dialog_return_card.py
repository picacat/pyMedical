#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import cshis_utils
from libs import registration_utils
from libs import date_utils
from libs import case_utils
from libs import number_utils

import sys
if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 還卡對話框
class DialogReturnCard(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogReturnCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.deposit_key = args[2]
        self.case_key = args[3]
        self.patient_key = args[4]
        self.ui = None
        self.ic_card = None
        self.doctor_done = False

        self._set_ui()
        self._set_signal()
        self._read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_RETURN_CARD, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self._set_combo_box()
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('還卡')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定comboBox
    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_return_period, nhi_utils.PERIOD)
        ui_utils.set_combo_box(self.ui.comboBox_continuance, nhi_utils.COURSE, None)
        ui_utils.set_combo_box(self.ui.comboBox_card, nhi_utils.ABNORMAL_CARD_WITH_HINT, '自動產生')

    # 讀取資料
    def _read_data(self):
        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.Share, cases.DiagShareFee, cases.DoctorDone,
                patient.Birthday, patient.ID, patient.CardNo, patient.InsType
            FROM deposit 
                LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
                LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE 
                deposit.CaseKey = "{0}"
            ORDER BY DepositDate DESC
        '''.format(self.case_key)
        row = self.database.select_record(sql)[0]

        patient_key = row['PatientKey']
        patient_share = string_utils.xstr(row['InsType'])

        if patient_share == '健保':
            patient_share = '基層醫療'

        if string_utils.xstr(row['DoctorDone']) == 'True':
            self.doctor_done = True

        self.ui.lineEdit_patient_key.setText(string_utils.xstr(patient_key))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']))
        self.ui.lineEdit_patient_share.setText(patient_share)
        self.ui.lineEdit_card_no.setText(string_utils.xstr(row['CardNo']))

        return_date = date_utils.now_to_str()
        period = registration_utils.get_current_period(self.system_settings)
        self.ui.lineEdit_return_date.setText(return_date)
        self.ui.comboBox_return_period.setCurrentText(period)
        self.ui.spinBox_return_fee.setValue(number_utils.get_integer(row['Fee']))

        course = number_utils.get_integer(row['Continuance'])
        self.ui.comboBox_continuance.setCurrentText(string_utils.xstr(course))
        if course <= 1:
            card = '自動產生'
        else:
            card = self._get_card(patient_key)

        self.ui.comboBox_card.setCurrentText(card)

    def _get_card(self, patient_key):
        card = ''

        sql = '''
            SELECT Card FROM cases
            WHERE
                PatientKey = {patient_key} AND
                InsType = "健保" AND
                Continuance = 1
            ORDER BY CaseDate DESC LIMIT 1 
        '''.format(
            patient_key=patient_key,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return card

        card = string_utils.xstr(rows[0]['Card'])

        return card

    # 還卡
    def accepted_button_clicked(self):
        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
        card_no = string_utils.xstr(self.ui.lineEdit_card_no.text())

        if card in nhi_utils.ABNORMAL_CARD:
            self.update_cases_by_manual_card(card)
            self.update_wait_by_manual_card(card)
        else:
            if card_no == '':
                self._write_patient()

            ic_card = self._write_ic_card(cshis_utils.RETURN_CARD)
            if ic_card is None:
                return

            if card == '自動產生':
                card = None

            self.update_cases_by_ic_card(ic_card, card)
            self.update_wait_by_ic_card(ic_card, card)

            if self.doctor_done:
                ic_card.write_ic_medical_record(self.case_key, cshis_utils.RETURN_CARD)

        self.update_return_card()
        self.update_medical_record()

    def _write_patient(self):
        ic_card = cshis.CSHIS(self.database, self.system_settings)
        if not ic_card.read_basic_data():
            return

        patient_key = self.ui.lineEdit_patient_key.text()
        card_no = ic_card.basic_data['card_no']

        sql = '''
            UPDATE patient 
            SET
                CardNo = "{card_no}"
            WHERE
                PatientKey = {patient_key}
        '''.format(
            card_no=card_no,
            patient_key=patient_key,
        )
        self.database.exec_sql(sql)

    def _write_ic_card(self, treat_after_check):
        ic_card = cshis.CSHIS(self.database, self.system_settings)
        ic_card_ok = ic_card.write_ic_card(
            '掛號寫卡',
            self.ui.lineEdit_patient_key.text(),
            self.ui.comboBox_continuance.currentText(),
            treat_after_check
        )

        if not ic_card_ok:
            return None

        return ic_card

    def update_cases_by_ic_card(self, ic_card, card=None):
        if ic_card is None:
            return

        fields = [
            'Card', 'Security',
        ]

        security = ic_card.treat_data_to_xml(ic_card.treat_data)
        treat_after_check = '2'
        security = case_utils.update_xml_doc(
            security, 'treat_after_check', treat_after_check)
        security = case_utils.update_xml_doc(
            security, 'prescript_sign_time', date_utils.now_to_str())
        security = case_utils.update_xml_doc(
            security, 'upload_type', '1')

        if card is None:
            card = ic_card.treat_data['seq_number']

        data = [
            card,
            security,
        ]
        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    def update_cases_by_manual_card(self, card):
        self.database.exec_sql('UPDATE cases SET Card = "{0}" WHERE CaseKey = {1}'.format(
            card,
            self.case_key
        ))

    def update_wait_by_ic_card(self, ic_card, card=None):
        if ic_card is None:
            return

        if card is None:
            card = ic_card.treat_data['seq_number']

        sql = '''
            UPDATE wait SET Card = "{card}" WHERE CaseKey = {case_key}
        '''.format(
            card=card,
            case_key=self.case_key,
        )
        self.database.exec_sql(sql)

    def update_wait_by_manual_card(self, card):
        self.database.exec_sql('UPDATE wait SET Card = "{0}" WHERE CaseKey = {1}'.format(
            card,
            self.case_key
        ))

    def update_return_card(self):
        fields = [
            'ReturnDate', 'Period', 'Refunder'
        ]
        data = [
            self.ui.lineEdit_return_date.text(),
            self.ui.comboBox_return_period.currentText(),
            self.system_settings.field('使用者')
        ]
        self.database.update_record('deposit', fields, 'DepositKey', self.deposit_key, data)

    def update_medical_record(self):
        fields = ['RefundFee']
        data = [self.ui.spinBox_return_fee.value(),]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

