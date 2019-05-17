#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
import datetime
import re

from libs import ui_utils
from libs import system_utils
from libs import nhi_utils
from libs import patient_utils
from dialog import dialog_select_patient


# 病歷查詢視窗
class DialogMedicalRecordList(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICAL_RECORD_LIST, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())
        self._set_combo_box()
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.label_patient_key.setEnabled(False)
        self.ui.lineEdit_patient_key.setEnabled(False)
        self.ui.toolButton_select_patient.setEnabled(False)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.toolButton_select_patient.clicked.connect(lambda: self._select_patient(None))

        self.ui.radioButton_range_date.clicked.connect(self._set_date)
        self.ui.radioButton_all_date.clicked.connect(self._set_date)

        self.ui.radioButton_all_patient.clicked.connect(self._set_patient)
        self.ui.radioButton_assigned_patient.clicked.connect(self._set_patient)

    # 設定comboBox
    def _set_combo_box(self):
        script = 'select * from person where Position IN("醫師", "支援醫師") '
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_treat_type, nhi_utils.TREAT_TYPE, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_share_type, nhi_utils.SHARE_TYPE, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_apply_type, nhi_utils.APPLY_TYPE, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM, '全部')

    def _set_patient(self):
        if self.ui.radioButton_all_patient.isChecked():
            self.ui.lineEdit_patient_key.setText('')
            enabled = False
        else:
            enabled = True

        self.ui.label_patient_key.setEnabled(enabled)
        self.ui.lineEdit_patient_key.setEnabled(enabled)
        self.ui.toolButton_select_patient.setEnabled(enabled)

    def _set_date(self):
        if self.ui.radioButton_all_date.isChecked():
            enabled = False
            self.ui.radioButton_assigned_patient.setChecked(True)
            self._set_patient()
            self.ui.lineEdit_patient_key.setFocus()
        else:
            enabled = True
            self.ui.radioButton_all_patient.setChecked(True)
            self._set_patient()

        self.ui.label_date.setEnabled(enabled)
        self.ui.label_between.setEnabled(enabled)
        self.ui.label_period.setEnabled(enabled)
        self.ui.dateEdit_start_date.setEnabled(enabled)
        self.ui.dateEdit_end_date.setEnabled(enabled)
        self.ui.comboBox_period.setEnabled(enabled)

    # 設定 mysql script
    def get_sql(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        condition = []
        script = '''
            SELECT 
                CaseKey, DATE_FORMAT(CaseDate, '%Y-%m-%d %H:%i') AS CaseDate, DoctorDate, ChargeDate, 
                cases.PatientKey, cases.Name, Period, ChargePeriod, cases.InsType, 
                Share, cases.RegistNo, Card, Continuance, TreatType, 
                PresDays1, PresDays2, DiseaseCode1, DiseaseName1,
                Doctor, Massager, Room, RegistFee, SDiagShareFee, SDrugShareFee,
                DoctorDone, ChargeDone,
                TotalFee, patient.Gender, patient.Birthday
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
        '''

        if self.ui.radioButton_range_date.isChecked():
            condition.append('(CaseDate BETWEEN "{0}" AND "{1}")'.format(start_date, end_date))

        ins_type = self.ui.comboBox_ins_type.currentText()
        if ins_type != '全部':
            condition.append('cases.InsType = "{0}"'.format(ins_type))

        apply_type = self.ui.comboBox_apply_type.currentText()
        if apply_type != '全部':
            condition.append('ApplyType = "{0}"'.format(apply_type))

        treat_type = self.ui.comboBox_treat_type.currentText()
        if treat_type != '全部':
            condition.append('TreatType = "{0}"'.format(treat_type))

        share_type = self.ui.comboBox_share_type.currentText()
        if share_type != '全部':
            condition.append('Share = "{0}"'.format(share_type))

        period = self.ui.comboBox_period.currentText()
        if period != '全部':
            condition.append('Period = "{0}"'.format(period))

        room = self.ui.comboBox_room.currentText()
        if room != '全部':
            condition.append('Room = {0}'.format(room))

        doctor = self.ui.comboBox_doctor.currentText()
        if doctor != '全部':
            condition.append('Doctor = "{0}"'.format(doctor))

        keyword = self.ui.lineEdit_patient_key.text()
        if keyword == '':
            pass
        elif keyword.isdigit() and len(keyword) < 7:
            condition.append('cases.PatientKey = {0}'.format(keyword))
        else:
            rows = patient_utils.get_patient_by_keyword(self.database, keyword)
            if len(rows) == 1:
                patient_key = rows[0]['PatientKey']
            else:
                self._select_patient(keyword)
                patient_key = self.ui.lineEdit_patient_key.text()

            if patient_key != '':
                condition.append('cases.PatientKey = {0}'.format(patient_key))

        if len(condition) > 0:
            script += 'WHERE {condition}'.format(
                condition=' AND '.join(condition),
            )

        script += " ORDER BY CaseDate, cases.Room, cases.RegistNo"

        if self.ui.radioButton_all_date.isChecked() and self.ui.lineEdit_patient_key.text() == '':
            script = ''

        return script

    def accepted_button_clicked(self):
        pass

    def _select_patient(self, keyword=None):
        patient_key = ''

        dialog = dialog_select_patient.DialogSelectPatient(
            self, self.database, self.system_settings, keyword
        )
        if dialog.exec_():
            patient_key = dialog.get_patient_key()

        self.ui.lineEdit_patient_key.setText(patient_key)

        dialog.deleteLater()

