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

        self.past_history = {
            'index': 0,
            'row_count': 0,
            'data': None,
        }
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

        patient_key = self.medical_record['PatientKey']
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        try:
            self.patient_data = self.database.select_record(sql)[0]
        except IndexError:
            pass

        self._read_past_history(patient_key)

    # 讀取過去病歷名單
    def _read_past_history(self, patient_key):
        sql = '''
            SELECT CaseKey FROM cases
            WHERE
                PatientKey = {0} AND
                CaseKey != {1}
            ORDER BY CaseKey DESC
        '''.format(patient_key, self.case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        history_list = []
        for row in rows:
            history_list.append(row['CaseKey'])

        self.past_history = {
            'index': 0,
            'row_count': len(history_list),
            'data': history_list
        }

    # 顯示最近病歷
    def _display_past_record(self):
        self.first_past_record()

    # 設定最近病歷參數 (目前沒用到, 留作範例)
    def _set_past_values(self, row):
        self.ui.textEdit_past.setProperty('medical_record', row['CaseKey'])
        self.ui.textEdit_past.setProperty('patient_key', row['PatientKey'])
        self.ui.textEdit_past.setProperty('case_date', row['CaseDate'])

    def _get_past_history_case_key(self):
        if self.past_history['data'] is None:
            case_key = None
        else:
            index = self.past_history['index']
            case_key = self.past_history['data'][index]

        return case_key

    # 最近一筆
    def first_past_record(self):
        if self.past_history['data'] is None:
            self.ui.toolButton_first.setEnabled(False)
            self.ui.toolButton_previous.setEnabled(False)
            self.ui.toolButton_next.setEnabled(False)
            self.ui.toolButton_last.setEnabled(False)
            html = '<br><br><br><br><br><center>無過去病歷</center><br>'
            self.ui.textEdit_past.setHtml(html)
            return

        self.past_history['index'] = 0
        case_key = self._get_past_history_case_key()

        self._set_past_record(case_key)
        self.ui.toolButton_first.setEnabled(False)
        self.ui.toolButton_previous.setEnabled(False)
        self.ui.toolButton_next.setEnabled(True)
        self.ui.toolButton_last.setEnabled(True)

    # 上一筆
    def prev_past_record(self):
        self.past_history['index'] -= 1
        if self.past_history['index'] <= 0:  # 到頂
            self.past_history['index'] = 0
            self.ui.toolButton_first.setEnabled(False)
            self.ui.toolButton_previous.setEnabled(False)

        self.ui.toolButton_next.setEnabled(True)
        self.ui.toolButton_last.setEnabled(True)
        case_key = self._get_past_history_case_key()
        self._set_past_record(case_key)

    # 下一筆
    def next_past_record(self):
        self.past_history['index'] += 1
        if self.past_history['index'] >= self.past_history['row_count'] - 1:  # 到底
            self.past_history['index'] = self.past_history['row_count'] - 1
            self.ui.toolButton_next.setEnabled(False)
            self.ui.toolButton_last.setEnabled(False)

        self.ui.toolButton_first.setEnabled(True)
        self.ui.toolButton_previous.setEnabled(True)
        case_key = self._get_past_history_case_key()
        self._set_past_record(case_key)

    # 最後一筆
    def last_past_record(self):
        self.past_history['index'] = self.past_history['row_count'] - 1
        case_key = self._get_past_history_case_key()

        self._set_past_record(case_key)
        self.ui.toolButton_first.setEnabled(True)
        self.ui.toolButton_previous.setEnabled(True)
        self.ui.toolButton_next.setEnabled(False)
        self.ui.toolButton_last.setEnabled(False)

    # 讀取最近病歷
    def _set_past_record(self, case_key):
        sql = '''
            SELECT CaseKey, InsType, Treatment FROM cases
            WHERE
                CaseKey = {0}
        '''.format(case_key)
        row = self.database.select_record(sql)[0]
        ins_type = string_utils.xstr(row['InsType'])
        treatment = string_utils.xstr(row['Treatment'])

        html = case_utils.get_medical_record_html(self.database, self.system_settings, case_key)
        self.ui.textEdit_past.setHtml(html)

        self.ui.checkBox_ins_prescript.setChecked(False)  # 健保療程2-6次預設不拷貝藥品
        self.ui.checkBox_ins_prescript.setEnabled(False)  # 健保療程2-6次預設不拷貝藥品

        self.ui.checkBox_copy_to_self.setEnabled(False)

        self.ui.checkBox_ins_treat.setChecked(False)
        self.ui.checkBox_ins_treat.setEnabled(False)

        if ins_type == '健保':
            if treatment != '':
                self.ui.checkBox_ins_treat.setEnabled(True)
                self.ui.checkBox_ins_treat.setChecked(True)
            sql = '''
                SELECT PrescriptKey FROM prescript 
                WHERE 
                    CaseKey = {case_key} AND 
                    MedicineSet = 1 AND
                    MedicineType IN ("單方", "複方") 
            '''.format(
                case_key=case_key,
            )
            rows = self.database.select_record(sql)
            if len(rows) > 0:
                self.ui.checkBox_ins_prescript.setEnabled(True)
                self.ui.checkBox_copy_to_self.setEnabled(True)
                if treatment == '':
                    self.ui.checkBox_ins_prescript.setChecked(True)  # 預設非療程才拷貝藥品

        sql = 'SELECT MedicineSet FROM prescript WHERE CaseKey = {0} AND MedicineSet >= 2'.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            copy_self_prescript = True
        else:
            copy_self_prescript = False

        self.ui.checkBox_self_prescript.setEnabled(copy_self_prescript)
        self.ui.checkBox_self_prescript.setChecked(copy_self_prescript)
        if copy_self_prescript:
            self.ui.checkBox_self_prescript.setChecked(False)  # 預設不要拷貝


    # 拷貝病歷
    def copy_past_medical_record_button_clicked(self):
        if self.ui.checkBox_copy_to_self.isChecked():
            copy_to = '自費處方'
        else:
            copy_to = '健保處方'

        case_key = self._get_past_history_case_key()

        case_utils.copy_past_medical_record(
            self.database, self.parent, case_key,
            self.ui.checkBox_diagnostic.isChecked(),
            self.ui.checkBox_remark.isChecked(),
            self.ui.checkBox_disease.isChecked(),
            self.ui.checkBox_ins_prescript.isChecked(),
            copy_to,
            self.ui.checkBox_ins_treat.isChecked(),
            self.ui.checkBox_self_prescript.isChecked(),
        )

    # 設定核取方塊
    def set_check_box(self):
        enabled = not self.ui.checkBox_diagnostic.isChecked()

        self.ui.checkBox_diagnostic.setChecked(enabled)
        self.ui.checkBox_disease.setChecked(enabled)
        self.ui.checkBox_remark.setChecked(enabled)
        if self.ui.checkBox_ins_prescript.isEnabled():
            self.ui.checkBox_ins_prescript.setChecked(enabled)
        if self.ui.checkBox_ins_treat.isEnabled():
            self.ui.checkBox_ins_treat.setChecked(enabled)
        if self.ui.checkBox_self_prescript.isEnabled():
            self.ui.checkBox_self_prescript.setChecked(enabled)

