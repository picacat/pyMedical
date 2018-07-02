#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from libs import ui_settings
from libs import system
from libs import strings
from libs import nhi_utils


# 主視窗
class DialogReturnCard(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogReturnCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.patient_key = args[3]
        self.ui = None

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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_RETURN_CARD, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self._set_combo_box()
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('還卡')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定comboBox
    def _set_combo_box(self):
        ui_settings.set_combo_box(self.ui.comboBox_continuance, nhi_utils.COURSE)
        ui_settings.set_combo_box(self.ui.comboBox_case_share, nhi_utils.SHARE_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_card, nhi_utils.ABNORMAL_CARD_WITH_HINT, '自動產生')

    def accepted_button_clicked(self):
        pass

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
        patient_share = strings.xstr(row['InsType'])
        if patient_share == '健保':
            patient_share = '基層醫療'

        self.ui.lineEdit_patient_key.setText(strings.xstr(row['PatientKey']))
        self.ui.lineEdit_name.setText(strings.xstr(row['Name']))
        self.ui.lineEdit_birthday.setText(strings.xstr(row['Birthday']))
        self.ui.lineEdit_id.setText(strings.xstr(row['ID']))
        self.ui.lineEdit_patient_share.setText(patient_share)
        self.ui.lineEdit_card_no.setText(strings.xstr(row['CardNo']))

        self.ui.lineEdit_deposit_date.setText(strings.xstr(row['DepositDate']))
        self.ui.lineEdit_deposit_fee.setText(strings.xstr(row['Fee']))
        self.ui.comboBox_case_share.setCurrentText(row['Share'])
        self.ui.lineEdit_share_fee.setText(strings.xstr(row['DiagShareFee']))
        self.ui.comboBox_card.setCurrentText('自動產生')
        self.ui.comboBox_continuance.setCurrentText(row['Continuance'])
