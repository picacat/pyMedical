#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils


# 病歷資料 2018.01.31
class MedicalRecordRecentlyHistory(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecordRecentlyHistory, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.call_from = args[3]
        self.medical_record = None
        self.patient_data = None
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_data()
        self._display_past_record()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MEDICAL_RECORD_RECENTLY_HISTORY, self)

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_check.clicked.connect(self.set_check_box)
        self.ui.toolButton_first.clicked.connect(self.first_past_record)
        self.ui.toolButton_previous.clicked.connect(self.prev_past_record)
        self.ui.toolButton_next.clicked.connect(self.next_past_record)
        self.ui.toolButton_last.clicked.connect(self.last_past_record)
        self.ui.toolButton_copy.clicked.connect(self.copy_past_medical_record_button_clicked)

    def _read_data(self):
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
        self.medical_record = self.database.select_record(sql)[0]
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.medical_record['PatientKey'])
        try:
            self.patient_data = self.database.select_record(sql)[0]
        except IndexError:
            pass

    # 顯示最近病歷
    def _display_past_record(self):
        self.first_past_record()

    # 設定最近病歷參數
    def _set_past_values(self, rec):
        self.ui.textEdit_past.setProperty('case_key', rec['CaseKey'])
        self.ui.textEdit_past.setProperty('patient_key', rec['PatientKey'])
        self.ui.textEdit_past.setProperty('case_date', rec['CaseDate'])

    # 讀取最近病歷
    def _set_past_record(self, sql, direction):
        past_record = self.database.select_record(sql)

        if len(past_record) <= 0:
            self.ui.textEdit_past.setHtml('<br><br><br><br><br><br><br><center>無過去病歷</center>')
            self.ui.toolButton_copy.setEnabled(False)
            self.ui.toolButton_first.setEnabled(False)
            self.ui.toolButton_previous.setEnabled(False)
            self.ui.toolButton_next.setEnabled(False)
            self.ui.toolButton_last.setEnabled(False)
            if direction in ['prev']:
                self.ui.toolButton_next.setEnabled(True)
                self.ui.toolButton_last.setEnabled(True)
                self.ui.toolButton_copy.setEnabled(True)
            elif direction in ['next']:
                self.ui.toolButton_first.setEnabled(True)
                self.ui.toolButton_previous.setEnabled(True)
                self.ui.toolButton_copy.setEnabled(True)

            return

        rec = past_record[0]
        self.ui.toolButton_first.setEnabled(True)
        self.ui.toolButton_previous.setEnabled(True)
        self.ui.toolButton_next.setEnabled(True)
        self.ui.toolButton_last.setEnabled(True)
        self._set_past_values(rec)
        case_key = rec['CaseKey']
        html = case_utils.get_medical_record_html(self.database, self.system_settings, case_key)
        self.ui.textEdit_past.setHtml(html)

    # 最近一筆
    def first_past_record(self):
        sql = \
            'SELECT * FROM cases WHERE ' \
            'PatientKey = {0} AND CaseKey != {1} ORDER BY CaseDate DESC LIMIT 1'\
            .format(
                self.medical_record['PatientKey'],
                self.case_key,
                str(self.medical_record['CaseDate'])
            )
        self._set_past_record(sql, 'first')
        self.ui.toolButton_first.setEnabled(False)
        self.ui.toolButton_previous.setEnabled(False)

    # 上一筆
    def prev_past_record(self):
        sql = \
            'SELECT * FROM cases WHERE ' \
            'PatientKey = {0} AND CaseKey != {1} AND CaseDate > "{2}" ORDER BY CaseDate LIMIT 1'\
            .format(self.ui.textEdit_past.property('patient_key'),
                    self.case_key,
                    self.ui.textEdit_past.property('case_date')
                    )
        self._set_past_record(sql, 'prev')

    # 下一筆
    def next_past_record(self):
        sql = \
            'SELECT * FROM cases WHERE ' \
            'PatientKey = {0} AND CaseKey != {1} AND CaseDate < "{2}" ORDER BY CaseDate DESC LIMIT 1' \
            .format(self.ui.textEdit_past.property('patient_key'),
                    self.case_key,
                    self.ui.textEdit_past.property('case_date')
                    )
        self._set_past_record(sql, 'next')

    # 最後一筆
    def last_past_record(self):
        sql = \
            'SELECT * FROM cases WHERE ' \
            'PatientKey = {0} AND CaseKey != {1} AND CaseDate < "{2}" ORDER BY CaseDate LIMIT 1' \
            .format(self.medical_record['PatientKey'],
                    self.case_key,
                    str(self.medical_record['CaseDate'])
                    )
        self._set_past_record(sql, 'next')
        self.ui.toolButton_next.setEnabled(False)
        self.ui.toolButton_last.setEnabled(False)

    # 拷貝病歷
    def copy_past_medical_record_button_clicked(self):
        case_key = self.ui.textEdit_past.property('case_key')
        if case_key == '':
            return

        case_utils.copy_past_medical_record(
            self.database, self.parent, case_key,
            self.ui.checkBox_diagnostic.isChecked(),
            self.ui.checkBox_remark.isChecked(),
            self.ui.checkBox_disease.isChecked(),
            self.ui.checkBox_prescript.isChecked(),
        )

    # 設定核取方塊
    def set_check_box(self):
        self.ui.checkBox_diagnostic.setChecked(not self.ui.checkBox_diagnostic.isChecked())
        self.ui.checkBox_disease.setChecked(not self.ui.checkBox_disease.isChecked())
        self.ui.checkBox_remark.setChecked(not self.ui.checkBox_remark.isChecked())
        self.ui.checkBox_prescript.setChecked(not self.ui.checkBox_prescript.isChecked())

