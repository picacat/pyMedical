#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime
from libs import ui_settings
from libs import system
from libs import nhi_utils


# 主視窗
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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_MEDICAL_RECORD_LIST, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())
        self._set_combo_box()
        self.setFixedSize(self.size()) # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定comboBox
    def _set_combo_box(self):
        script = 'select * from person where Position = "醫師"'
        rows = self.database.select_record(script)
        doctor_list = []
        for row in rows:
            doctor_list.append(row['Name'])

        ui_settings.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD, '全部')
        ui_settings.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE, '全部')
        ui_settings.set_combo_box(self.ui.comboBox_treat_type, nhi_utils.TREAT_TYPE, '全部')
        ui_settings.set_combo_box(self.ui.comboBox_share_type, nhi_utils.SHARE_TYPE, '全部')
        ui_settings.set_combo_box(self.ui.comboBox_apply_type, nhi_utils.APPLY_TYPE, '全部')
        ui_settings.set_combo_box(self.ui.comboBox_doctor, doctor_list, '全部')
        ui_settings.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM, '全部')

    # 設定 mysql script
    def get_sql(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        script = ("SELECT CaseKey, DATE_FORMAT(CaseDate, '%Y-%m-%d %H:%i') AS CaseDate, "
                  "cases.PatientKey, cases.Name, Period, cases.InsType, "
                  "Share, RegistNo, Card, Continuance, TreatType, "
                  "PresDays1, PresDays2, DiseaseCode1, DiseaseName1, "
                  "Doctor, Massager, Room, RegistFee, SDiagShareFee, SDrugShareFee, "
                  "TotalFee, patient.Gender, patient.Birthday "
                  "FROM cases "
                  "LEFT JOIN patient ON patient.PatientKey = cases.PatientKey "
                  "WHERE "
                  "CaseDate BETWEEN '{0}' AND '{1}'").format(start_date, end_date)

        ins_type = self.ui.comboBox_ins_type.currentText()
        if ins_type != '全部':
            script = script + " and cases.InsType = '{0}'".format(ins_type)

        apply_type = self.ui.comboBox_apply_type.currentText()
        if apply_type != '全部':
            script = script + " and ApplyType = '{0}'".format(apply_type)

        share_type = self.ui.comboBox_share_type.currentText()
        if share_type != '全部':
            script = script + " and Share = '{0}'".format(share_type)

        period = self.ui.comboBox_period.currentText()
        if period != '全部':
            script = script + " and Period = '{0}'".format(period)

        room = self.ui.comboBox_room.currentText()
        if room != '全部':
            script = script + " and Room = {0}".format(room)

        patient_key = self.ui.lineEdit_patient_key.text()

        if patient_key != '':
            script = script + " and cases.PatientKey = {0}".format(patient_key)

        doctor = self.ui.comboBox_doctor.currentText()
        if doctor != '全部':
            script = script + " and Doctor = '{0}'".format(doctor)

        script = script + " order by CaseDate, cases.Room, RegistNo"

        return script

    def accepted_button_clicked(self):
        pass
