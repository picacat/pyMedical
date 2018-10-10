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


# 主視窗
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
        system_utils.set_css(self)
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
        ui_utils.set_combo_box(self.ui.comboBox_case_share, nhi_utils.SHARE_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_card, nhi_utils.ABNORMAL_CARD_WITH_HINT, '自動產生')

    # 讀取資料
    def _read_data(self):
        sql = '''
            SELECT 
                deposit.*, 
                cases.Card, cases.Continuance, cases.Share, cases.DiagShareFee,
                patient.Birthday, patient.ID, patient.CardNo, patient.InsType
            FROM deposit 
            LEFT JOIN cases ON cases.CaseKey = deposit.CaseKey
            LEFT JOIN patient ON patient.PatientKey = deposit.PatientKey
            WHERE deposit.CaseKey = "{0}"
            ORDER BY DepositDate DESC
        '''.format(self.case_key)
        row = self.database.select_record(sql)[0]
        patient_share = string_utils.xstr(row['InsType'])
        if patient_share == '健保':
            patient_share = '基層醫療'

        self.ui.lineEdit_patient_key.setText(string_utils.xstr(row['PatientKey']))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']))
        self.ui.lineEdit_patient_share.setText(patient_share)
        self.ui.lineEdit_card_no.setText(string_utils.xstr(row['CardNo']))

        return_date = date_utils.now_to_str()
        period = registration_utils.get_period(self.system_settings)
        self.ui.lineEdit_return_date.setText(return_date)
        self.ui.comboBox_return_period.setCurrentText(period)
        self.ui.lineEdit_return_fee.setText(string_utils.xstr(row['Fee']))
        self.ui.comboBox_case_share.setCurrentText(row['Share'])
        self.ui.lineEdit_share_fee.setText(string_utils.xstr(row['DiagShareFee']))
        self.ui.comboBox_card.setCurrentText('自動產生')
        self.ui.comboBox_continuance.setCurrentText(string_utils.xstr(row['Continuance']))

    # 還卡
    def accepted_button_clicked(self):
        ic_card = None
        if self.ui.comboBox_card.currentText() == '自動產生':
            ic_card = self._write_ic_card(cshis_utils.RETURN_CARD)
            self.update_cases_by_ic_card(ic_card)
            self._write_ic_treatments(cshis_utils.RETURN_CARD)
            self._write_prescript_signature()
            self.update_wait_by_ic_card(ic_card)
        else:
            self.update_cases_by_abnormal_card()
            self.update_wait_by_abnormal_card()

        self.update_return_card()
        self.update_medical_record()

    def _write_ic_card(self, treat_after_check):
        ic_card = cshis_utils.write_ic_card(
            '掛號寫卡',
            self.database,
            self.system_settings, self.ui.lineEdit_patient_key.text(),
            self.ui.comboBox_continuance.currentText(),
            treat_after_check
        )
        if not ic_card:
            return None

        return ic_card

    # 寫入病名, 費用
    def _write_ic_treatments(self, treat_after_check):
        cshis_utils.write_ic_treatment(
            self.database, self.system_settings, self.case_key, treat_after_check)

    # 寫入醫令簽章
    def _write_prescript_signature(self):
        cshis_utils.write_prescript_signature(
            self.database, self.system_settings, self.case_key)

    def update_cases_by_ic_card(self, ic_card):
        if ic_card is None:
            return

        fields = [
            'Card', 'Security',
        ]

        security = ic_card.treat_data_to_xml(ic_card.treat_data)
        treat_after_check = '2'
        security = case_utils.update_xml_doc(
            self.database, security, 'treat_after_check', treat_after_check)
        security = case_utils.update_xml_doc(
            self.database, security, 'prescript_sign_time', date_utils.now_to_str())
        security = case_utils.update_xml_doc(
            self.database, security, 'upload_type', '1')
        data = [
            ic_card.treat_data['seq_number'],
            security,
        ]
        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    def update_cases_by_abnormal_card(self):
        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
        self.database.exec_sql('UPDATE cases SET Card = "{0}" WHERE CaseKey = {1}'.format(
            card,
            self.case_key
        ))

    def update_wait_by_ic_card(self, ic_card):
        if ic_card is None:
            return

        sql = '''
            UPDATE wait SET Card = "{0}" WHERE CaseKey = {1}
        '''.format(ic_card.treat_data['seq_number'], self.case_key)
        self.database.exec_sql(sql)

    def update_wait_by_abnormal_card(self):
        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
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
        data = [self.ui.lineEdit_return_fee.text(),]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

