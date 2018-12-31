#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime
from libs import ui_utils
from libs import system_utils
from libs import nhi_utils
from dialog import dialog_select_patient


# 病歷查詢視窗
class DialogCertificateQuery(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogCertificateQuery, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.certificate_type = args[2]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_CERTIFICATE_QUERY, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

        self.ui.label_year.setEnabled(False)
        self.ui.spinBox_year.setEnabled(False)

        current_year = datetime.datetime.now().year
        self.ui.spinBox_year.setMaximum(current_year)
        self.ui.spinBox_year.setValue(current_year)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.radioButton_patient.clicked.connect(self._set_patient)
        self.ui.radioButton_year.clicked.connect(self._set_patient)
        self.ui.toolButton_select_patient.clicked.connect(self._select_patient)

    def _set_patient(self):
        if self.ui.radioButton_patient.isChecked():
            enabled = True
        else:
            self.ui.lineEdit_patient_key.setText('')
            enabled = False

        self.ui.label_patient_key.setEnabled(enabled)
        self.ui.lineEdit_patient_key.setEnabled(enabled)
        self.ui.toolButton_select_patient.setEnabled(enabled)

        self.ui.label_year.setEnabled(not enabled)
        self.ui.spinBox_year.setEnabled(not enabled)

    def accepted_button_clicked(self):
        self.sql = '''
            SELECT certificate.*, cases.ChargeDone FROM certificate
                LEFT JOIN cases ON cases.CaseKey = certificate.CaseKey
            WHERE
                CertificateType = "{0}"
        '''.format(self.certificate_type)

        if self.ui.radioButton_patient.isChecked():
            self.sql += ' AND certificate.PatientKey = {0}'.format(self.ui.lineEdit_patient_key.text())
        else:
            start_date = '{0}-01-01 00:00:00'.format(self.ui.spinBox_year.value())
            end_date = '{0}-12-31 23:59:59'.format(self.ui.spinBox_year.value())

            self.sql += ' AND CertificateDate BETWEEN "{0}" AND "{1}"'.format(
                start_date, end_date,
            )

        self.sql += ' ORDER BY CertificateKey DESC'

    def _select_patient(self):
        patient_key = ''
        dialog = dialog_select_patient.DialogSelectPatient(self, self.database, self.system_settings)
        if dialog.exec_():
            patient_key = dialog.get_patient_key()

        self.ui.lineEdit_patient_key.setText(patient_key)

        dialog.deleteLater()
