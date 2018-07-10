#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import date_utils
import ins_prescript_record
from dialog import dialog_inquiry
from dialog import dialog_diagnosis


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
        self.MAX_MEDICINE_SET = 100

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
        self.ui.toolButton_copy.clicked.connect(self.on_copy_button_clicked)

    def _read_data(self):
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
        self.medical_record = self.database.select_record(sql)[0]
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.medical_record['PatientKey'])
        self.patient_data = self.database.select_record(sql)[0]

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
        self._set_record_summary(rec)

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

    # 顯示最近病歷內容
    def _set_record_summary(self, rec):
        if rec['InsType'] == '健保':
            card = str(rec['Card'])
            if number_utils.get_integer(rec['Continuance']) >= 1:
                card += '-' + str(rec['Continuance'])
            card = '<b>健保</b>: {0}'.format(card)
        else:
            card = '<b>自費</b>'

        summary = '<b>日期</b>: {0} {1}<br>'.format(str(rec['CaseDate']), card)
        summary += '<b>醫師</b>: {0}<hr>'.format(str(rec['Doctor']), card)
        if rec['Symptom'] is not None:
            summary += '<b>主訴</b>: {0}<hr>'.format(string_utils.get_str(rec['Symptom'], 'utf8'))
        if rec['Tongue'] is not None:
            summary += '<b>舌診</b>: {0}<hr>'.format(string_utils.get_str(rec['Tongue'], 'utf8'))
        if rec['Pulse'] is not None:
            summary += '<b>脈象</b>: {0}<hr>'.format(string_utils.get_str(rec['Pulse'], 'utf8'))
        if rec['Remark'] is not None:
            summary += '<b>備註</b>: {0}<hr>'.format(string_utils.get_str(rec['Remark'], 'utf8'))
        if rec['DiseaseCode1'] is not None and len(str(rec['DiseaseCode1']).strip()) > 0:
            summary += '<b>主診斷</b>: {0} {1}<br>'.format(str(rec['DiseaseCode1']), str(rec['DiseaseName1']))
        if rec['DiseaseCode2'] is not None and len(str(rec['DiseaseCode2']).strip()) > 0:
            summary += '<b>次診斷1</b>: {0} {1}<br>'.format(str(rec['DiseaseCode2']), str(rec['DiseaseName2']))
        if rec['DiseaseCode3'] is not None and len(str(rec['DiseaseCode3']).strip()) > 0:
            summary += '<b>次診斷2</b>: {0} {1}<br>'.format(str(rec['DiseaseCode3']), str(rec['DiseaseName3']))

        summary += self.get_prescript_record()
        self.ui.textEdit_past.setHtml(summary)

    def get_prescript_record(self):
        case_key = self.ui.textEdit_past.property('case_key')
        sql = 'SELECT * FROM prescript WHERE CaseKey = {0}'.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return '<br><center>未開藥</center><br>'

        all_prescript = ''
        for i in range(1, self.MAX_MEDICINE_SET):
            sql = '''
                SELECT * FROM prescript WHERE CaseKey = {0} AND
                MedicineSet = {1}
                ORDER BY PrescriptNo
            '''.format(case_key, i)
            rows = self.database.select_record(sql)

            if len(rows) <= 0:
                if i == 1:
                    continue
                else:
                    break

            prescript_data = ''
            for row in rows:
                if row['MedicineName'] is None:
                    continue

                prescript_data += '''
                    <tr>
                        <td>{0}</td>
                        <td align="right">{1}{2}</td>
                    </tr>
                '''.format(row['MedicineName'], row['Dosage'], row['Unit'])

            if i == 1:
                medicine_title = '健保處方'
            else:
                medicine_title = '自費處方{0}'.format(i-1)

            prescript_data = '''
                <table border="1" bgcolor="#F2F2F2">
                    <tr>
                        <th width="250" align="left">{0}</th>
                        <th width="90">劑量</th>
                    </tr>
                    {1}
                </table><br>
            '''.format(medicine_title, prescript_data)
            all_prescript += prescript_data

        return all_prescript

    # 拷貝病歷
    def on_copy_button_clicked(self):
        case_key = self.ui.textEdit_past.property('case_key')
        if case_key == '':
            return
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
        row = self.database.select_record(sql)[0]
        if self.ui.checkBox_diagnostic.isChecked():
            self.parent.ui.textEdit_symptom.setText(string_utils.get_str(row['Symptom'], 'utf8'))
            self.parent.ui.textEdit_tongue.setText(string_utils.get_str(row['Tongue'], 'utf8'))
            self.parent.ui.textEdit_pulse.setText(string_utils.get_str(row['Pulse'], 'utf8'))
        if self.ui.checkBox_remark.isChecked():
            self.parent.ui.textEdit_remark.setText(string_utils.get_str(row['Remark'], 'utf8'))
        if self.ui.checkBox_disease.isChecked():
            self.parent.ui.lineEdit_disease_code1.setText(string_utils.get_str(row['DiseaseCode1'], 'utf8'))
            self.parent.ui.lineEdit_disease_name1.setText(string_utils.get_str(row['DiseaseName1'], 'utf8'))
            self.parent.ui.lineEdit_disease_code2.setText(string_utils.get_str(row['DiseaseCode2'], 'utf8'))
            self.parent.ui.lineEdit_disease_name2.setText(string_utils.get_str(row['DiseaseName2'], 'utf8'))
            self.parent.ui.lineEdit_disease_code3.setText(string_utils.get_str(row['DiseaseCode3'], 'utf8'))
            self.parent.ui.lineEdit_disease_name3.setText(string_utils.get_str(row['DiseaseName3'], 'utf8'))
        if self.ui.checkBox_prescript.isChecked():
            self.copy_past_prescript(case_key)

    # 設定核取方塊
    def set_check_box(self):
        self.ui.checkBox_diagnostic.setChecked(not self.ui.checkBox_diagnostic.isChecked())
        self.ui.checkBox_disease.setChecked(not self.ui.checkBox_disease.isChecked())
        self.ui.checkBox_remark.setChecked(not self.ui.checkBox_remark.isChecked())
        self.ui.checkBox_prescript.setChecked(not self.ui.checkBox_prescript.isChecked())

    def copy_past_prescript(self, case_key):
        if self.parent.tab_ins_prescript is not None:
            self.parent.tab_ins_prescript.copy_past_prescript(case_key)
