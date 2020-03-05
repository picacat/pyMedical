#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
import datetime
from libs import ui_utils
from libs import system_utils
from libs import nhi_utils


# 主視窗
class DialogICRecordUpload(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogICRecordUpload, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_IC_RECORD_UPLOAD, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())
        self._set_combo_box()
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

        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD, '全部')
        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, '全部')

    # 設定 mysql script
    def get_sql(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')

        script = '''
            SELECT 
                *, DATE_FORMAT(CaseDate, "%Y-%m-%d %H:%i") AS CaseDate, 
                cases.InsType as CaseInsType,
                patient.Gender, patient.Birthday
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                ((CaseDate BETWEEN "{0}" AND "{1}") OR 
                 (ExtractValue(Security, "//registered_date") BETWEEN "{0}" AND "{1}")) AND
                (cases.InsType = "健保") AND
                (Card NOT IN ("欠卡") AND Card IS NOT NULL)
        '''.format(start_date, end_date)

        '''
                ExtractValue(Security, "//registered_date") AS RegisteredDate,
                ExtractValue(Security, "//sam_id") AS SAMID,
                ExtractValue(Security, "//clinic_id") AS ClinicID,
                ExtractValue(Security, "//upload_type") AS UploadType,
                ExtractValue(Security, "//treat_after_check") AS TreatAfterCheck,
                ExtractValue(Security, "//security_signature") AS SecuritySignature,
        '''

        period = self.ui.comboBox_period.currentText()
        if period != '全部':
            script += " AND Period = '{0}'".format(period)

        doctor = self.ui.comboBox_doctor.currentText()
        if doctor != '全部':
            script += " AND Doctor = '{0}'".format(doctor)

        if self.ui.radioButton_normal.isChecked():
            script += 'AND (ExtractValue(Security, "//upload_time") = "")'
        else:
            script += 'AND (ExtractValue(Security, "//upload_time") != "")'

        script += ' ORDER BY CaseDate, cases.Room, cases.RegistNo'

        return script

    def accepted_button_clicked(self):
        pass
