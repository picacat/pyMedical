#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_settings
from libs import strings
from libs import nhi


# 樣板 2018.01.31
class Patient(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Patient, self).__init__(parent)
        self.parent = parent
        self.database = args[0][0]
        self.system_settings = args[0][1]
        self.patient_key = args[0][2]
        self.call_from = args[0][3]
        self.patient = None
        self.ui = None

        self._set_ui()
        self._set_signal()

        if self.patient_key is not None:
            self._read_patient()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_PATIENT, self)
        self._set_combobox()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_patient)

    def _set_combobox(self):
        ui_settings.set_combo_box(self.ui.comboBox_nationality, nhi.NATIONALITY)
        ui_settings.set_combo_box(self.ui.comboBox_ins_type, nhi.SHARE_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_marriage, nhi.MARRIAGE)
        ui_settings.set_combo_box(self.ui.comboBox_education, nhi.EDUCATION)
        ui_settings.set_combo_box(self.ui.comboBox_occupation, nhi.OCCUPATION)
        ui_settings.set_combo_box(self.ui.comboBox_discount, nhi.DISCOUNT)

    def _read_patient(self):
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.patient_key)
        self.patient = self.database.select_record(sql)[0]
        self._set_patient()

    def _set_patient(self):
        self.ui.lineEdit_patient_key.setText(strings.xstr(self.patient['PatientKey']))
        self.ui.lineEdit_card_no.setText(strings.xstr(self.patient['CardNo']))
        self.ui.lineEdit_name.setText(strings.xstr(self.patient['Name']))
        self.ui.lineEdit_id.setText(strings.xstr(self.patient['ID']))
        self.ui.lineEdit_birthday.setText(strings.xstr(self.patient['Birthday']))
        self.ui.lineEdit_init_date.setText(strings.xstr(self.patient['InitDate']))
        self.ui.lineEdit_telephone.setText(strings.xstr(self.patient['Telephone']))
        self.ui.lineEdit_cellphone.setText(strings.xstr(self.patient['Cellphone']))
        self.ui.lineEdit_email.setText(strings.xstr(self.patient['Email']))
        self.ui.lineEdit_address.setText(strings.xstr(self.patient['Address']))
        self.ui.lineEdit_family.setText(strings.xstr(self.patient['FamilyPatientKey']))
        self.ui.lineEdit_family_telephone.setText(strings.xstr(self.patient['Reference']))
        self.ui.comboBox_ins_type.setCurrentText(self.patient['InsType'])
        self.ui.comboBox_nationality.setCurrentText(self.patient['Nationality'])
        self.ui.comboBox_marriage.setCurrentText(self.patient['Marriage'])
        self.ui.comboBox_education.setCurrentText(self.patient['Education'])
        self.ui.comboBox_occupation.setCurrentText(self.patient['Occupation'])
        self.ui.comboBox_discount.setCurrentText(self.patient['DiscountType'])
        self.ui.textEdit_allergy.setText(strings.get_str(self.patient['Allergy'], 'utf8'))
        self.ui.textEdit_history.setText(strings.get_str(self.patient['History'], 'utf8'))
        self.ui.textEdit_remark.setText(strings.get_str(self.patient['Remark'], 'utf8'))
        self.ui.textEdit_description.setText(strings.get_str(self.patient['Description'], 'utf8'))

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_patient(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = Patient()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
