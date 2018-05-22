#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from libs import ui_settings
from libs import strings
from libs import number
from libs import date_utils
import ins_prescript_record
from dialog import dialog_diagnostic


# 病歷資料 2018.01.31
class MedicalRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0][0]
        self.system_settings = args[0][1]
        self.case_key = args[0][2]
        self.call_from = args[0][3]
        self.medical_record = None
        self.patient_data = None
        self.record_saved = False
        self.first_record = None
        self.last_record = None
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_data()
        self._read_prescript()
        self._display_past_record()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_MEDICAL_RECORD, self)
        self.ui.groupBox_symptom.setContentsMargins(0, 0, 0, 0)

    # 設定信號
    def _set_signal(self):
        self.ui.action_save.triggered.connect(self.save_medical_record)
        self.ui.action_dictionary.triggered.connect(self.open_dictionary)
        self.ui.action_close.triggered.connect(self.close_medical_record)
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
        self._set_patient_data()
        self._set_medical_record()

    def _set_patient_data(self):
        name = self.patient_data['Name']
        gender = self.patient_data['Gender']
        if gender in ['男', '女']:
            name += ' ({0})'.format(gender)
        card = self.medical_record['Card']
        if number.get_integer(self.medical_record['Continuance']) >= 1:
            card += '-' + str(self.medical_record['Continuance'])

        age_year, age_month = date_utils.get_age(self.patient_data['Birthday'], self.medical_record['CaseDate'])
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)

        self.ui.label_case_date.setText(str(self.medical_record['CaseDate']))
        self.ui.label_ins_type.setText(self.medical_record['InsType'])
        self.ui.label_patient_name.setText(name)
        self.ui.label_age.setText(age)
        self.ui.label_share_type.setText(self.medical_record['Share'])
        if card is not None:
            self.ui.label_card.setText(card)

    # 顯示病歷
    def _set_medical_record(self):
        self.ui.textEdit_symptom.setText(strings.get_str(self.medical_record['Symptom'], 'utf8'))
        self.ui.textEdit_tongue.setText(strings.get_str(self.medical_record['Tongue'], 'utf8'))
        self.ui.textEdit_pulse.setText(strings.get_str(self.medical_record['Pulse'], 'utf8'))
        self.ui.textEdit_remark.setText(strings.get_str(self.medical_record['Remark'], 'utf8'))
        self.ui.lineEdit_disease_code1.setText(strings.get_str(self.medical_record['DiseaseCode1'], 'utf8'))
        self.ui.lineEdit_disease_name1.setText(strings.get_str(self.medical_record['DiseaseName1'], 'utf8'))
        self.ui.lineEdit_disease_code2.setText(strings.get_str(self.medical_record['DiseaseCode2'], 'utf8'))
        self.ui.lineEdit_disease_name2.setText(strings.get_str(self.medical_record['DiseaseName2'], 'utf8'))
        self.ui.lineEdit_disease_code3.setText(strings.get_str(self.medical_record['DiseaseCode3'], 'utf8'))
        self.ui.lineEdit_disease_name3.setText(strings.get_str(self.medical_record['DiseaseName3'], 'utf8'))
        self.ui.lineEdit_distinct.setText(strings.get_str(self.medical_record['Distincts'], 'utf8'))
        self.ui.lineEdit_cure.setText(strings.get_str(self.medical_record['Cure'], 'utf8'))

    # 病歷存檔
    def save_medical_record(self):
        self.record_saved = True
        fields = ['Symptom', 'Tongue', 'Pulse', 'Remark']
        data = (
            self.ui.textEdit_symptom.toPlainText(),
            self.ui.textEdit_tongue.toPlainText(),
            self.ui.textEdit_pulse.toPlainText(),
            self.ui.textEdit_remark.toPlainText(),
        )
        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)
        self.close_all()
        self.close_tab()

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def record_modified(self):
        modified = False
        if self.ui.textEdit_symptom.document().isModified():
            modified = True

        return modified

    def open_dictionary(self):
        dialog_type = None
        if self.ui.textEdit_symptom.hasFocus():
            dialog_type = '主訴'
        elif self.ui.textEdit_tongue.hasFocus():
            dialog_type = '舌診'
        elif self.ui.textEdit_pulse.hasFocus():
            dialog_type = '脈象'
        elif self.ui.textEdit_remark.hasFocus():
            dialog_type = '備註'

        if dialog_type is None:
            return

        text_edit = {
            '主訴': self.ui.textEdit_symptom,
            '舌診': self.ui.textEdit_tongue,
            '脈象': self.ui.textEdit_pulse,
            '備註': self.ui.textEdit_remark,
        }
        if dialog_type in ['主訴', '舌診', '脈象', '備註']:
            dialog = dialog_diagnostic.DialogDiagnostic(
                self, self.database, self.system_settings, dialog_type, text_edit[dialog_type])

        dialog.exec_()
        del dialog

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
            .format(self.medical_record['PatientKey'],
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
            if number.get_integer(rec['Continuance']) >= 1:
                card += '-' + str(rec['Continuance'])
        else:
            card = ''

        summary = '<b>日期</b>: {0} <b>卡序</b>: {1}<br>'.format(str(rec['CaseDate']), card)
        if rec['Symptom'] is not None:
            summary += '<b>主訴</b>: {0}<br>'.format(strings.get_str(rec['Symptom'], 'utf8'))
        if rec['Tongue'] is not None:
            summary += '<b>舌診</b>: {0}<br>'.format(strings.get_str(rec['Tongue'], 'utf8'))
        if rec['Pulse'] is not None:
            summary += '<b>脈象</b>: {0}<br>'.format(strings.get_str(rec['Pulse'], 'utf8'))
        if rec['Remark'] is not None:
            summary += '<b>備註</b>: {0}<br>'.format(strings.get_str(rec['Remark'], 'utf8'))
        if rec['DiseaseCode1'] is not None and len(str(rec['DiseaseCode1']).strip()) > 0:
            summary += '<b>主診斷</b>: {0} {1}<br>'.format(str(rec['DiseaseCode1']), str(rec['DiseaseName1']))
        if rec['DiseaseCode2'] is not None and len(str(rec['DiseaseCode2']).strip()) > 0:
            summary += '<b>次診斷1</b>: {0} {1}<br>'.format(str(rec['DiseaseCode2']), str(rec['DiseaseName2']))
        if rec['DiseaseCode3'] is not None and len(str(rec['DiseaseCode3']).strip()) > 0:
            summary += '<b>次診斷2</b>: {0} {1}<br>'.format(str(rec['DiseaseCode3']), str(rec['DiseaseName3']))

        self.ui.textEdit_past.setHtml(summary)

    # 拷貝病歷
    def on_copy_button_clicked(self):
        case_key = self.ui.textEdit_past.property('case_key')
        if case_key == '':
            return

        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
        row = self.database.select_record(sql)[0]
        if self.ui.checkBox_symptom.isChecked():
            self.ui.textEdit_symptom.setText(strings.get_str(row['Symptom'], 'utf8'))
        if self.ui.checkBox_tongue.isChecked():
            self.ui.textEdit_tongue.setText(strings.get_str(row['Tongue'], 'utf8'))
        if self.ui.checkBox_pulse.isChecked():
            self.ui.textEdit_pulse.setText(strings.get_str(row['Pulse'], 'utf8'))
        if self.ui.checkBox_remark.isChecked():
            self.ui.textEdit_remark.setText(strings.get_str(row['Remark'], 'utf8'))

    # 設定核取方塊
    def set_check_box(self):
        self.ui.checkBox_symptom.setChecked(not self.ui.checkBox_symptom.isChecked())
        self.ui.checkBox_tongue.setChecked(not self.ui.checkBox_tongue.isChecked())
        self.ui.checkBox_pulse.setChecked(not self.ui.checkBox_pulse.isChecked())
        self.ui.checkBox_remark.setChecked(not self.ui.checkBox_remark.isChecked())
        self.ui.checkBox_disease.setChecked(not self.ui.checkBox_disease.isChecked())
        self.ui.checkBox_distinct.setChecked(not self.ui.checkBox_distinct.isChecked())
        self.ui.checkBox_cure.setChecked(not self.ui.checkBox_cure.isChecked())
        self.ui.checkBox_prescript.setChecked(not self.ui.checkBox_prescript.isChecked())

    def _read_prescript(self):
        if self.medical_record['InsType'] == '健保':
            self.ui.tabWidget_prescript.addTab(
                ins_prescript_record.InsPrescriptRecord(
                    self, self.database, self.system_settings, self.case_key), '健保處方')

    def close_medical_record(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = MedicalRecord()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
