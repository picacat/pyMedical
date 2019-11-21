#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import dialog_utils
from libs import case_utils


# 主視窗
class DialogMedicalRecordReference(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordReference, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.ui = None
        self.copy_medical_record = True

        self._set_ui()
        self._set_signal()
        self._read_medical_record_reference()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICAL_RECORD_REFERENCE, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('拷貝病歷')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_reference_list = table_widget.TableWidget(
            self.ui.tableWidget_reference_list, self.database
        )
        self.table_widget_reference_symptom = table_widget.TableWidget(
            self.ui.tableWidget_reference_symptom, self.database
        )
        self.table_widget_reference_symptom.set_column_hidden([0, 1, 2, 3, 4, 5])
        self._set_table_width()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 280]
        self.table_widget_reference_list.set_table_heading_width(width)
        width = [100, 100, 100, 100, 100, 100, 480]
        self.table_widget_reference_symptom.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_reference_list.itemSelectionChanged.connect(self._reference_list_changed)
        self.ui.tableWidget_reference_symptom.itemSelectionChanged.connect(self._reference_symptom_changed)
        self.ui.tableWidget_reference_symptom.doubleClicked.connect(self._edit_past_history)
        self.ui.lineEdit_disease_name.textChanged.connect(self._disease_name_changed)
        self.ui.toolButton_cancel_reference.clicked.connect(self._cancel_reference)

    def accepted_button_clicked(self):
        if not self.copy_medical_record:
            return

        case_key = self.table_widget_reference_symptom.field_value(0)

        if self.ui.radioButton_ins_prescript.isChecked():
            copy_ins_prescript_to = '健保處方'
        else:
            copy_ins_prescript_to = '自費處方'

        case_utils.copy_past_medical_record(
            self.database, self.parent, case_key,
            self.ui.checkBox_diagnostic.isChecked(),
            self.ui.checkBox_remark.isChecked(),
            self.ui.checkBox_disease.isChecked(),
            self.ui.checkBox_ins_prescript.isChecked(),
            copy_ins_prescript_to,
            self.ui.checkBox_ins_treat.isChecked(),
            self.ui.checkBox_self_prescript.isChecked(),
        )

    def _disease_name_changed(self):
        disease_name = self.ui.lineEdit_disease_name.text()
        self._read_medical_record_reference(disease_name.strip())
        self.ui.lineEdit_disease_name.setFocus(True)
        self.ui.lineEdit_disease_name.setCursorPosition(len(disease_name))

    def _read_medical_record_reference(self, disease_name=''):
        if disease_name is None:
            return

        if disease_name != '':
            disease_name_script = 'AND DiseaseName1 LIKE "%{disease_name}%"'.format(
                disease_name=disease_name,
            )
        else:
            disease_name_script = ''

        sql = '''
            SELECT DiseaseCode1, DiseaseName1 FROM cases
            WHERE
                CaseKey != {case_key} AND
                DiseaseName1 IS NOT NULL AND
                cases.Reference = "True"
                {disease_name_script}
            GROUP BY DiseaseCode1
            ORDER BY DiseaseCode1
        '''.format(
            case_key=self.case_key,
            disease_name_script=disease_name_script,
        )

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        self.table_widget_reference_list.set_db_data(sql, self._set_reference_list_data)

    def _set_reference_list_data(self, row_no, row):
        medical_record_data = [
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
        ]

        for column in range(len(medical_record_data)):
            self.ui.tableWidget_reference_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record_data[column])
            )

    def _reference_list_changed(self):
        disease_code1 = self.table_widget_reference_list.field_value(0)

        sql = '''
            SELECT 
                cases.CaseKey, cases.CaseDate, cases.PatientKey, 
                cases.Name, cases.InsType, cases.Symptom, 
                patient.Gender, patient.Birthday
            FROM cases
            LEFT JOIN patient
                ON patient.PatientKey = cases.PatientKey
            WHERE
                DiseaseCode1 = "{disease_code1}" AND
                cases.Reference = "True"
            ORDER BY cases.PatientKey, CaseDate
        '''.format(
            disease_code1=disease_code1,
        )

        self.table_widget_reference_symptom.set_db_data(sql, self._set_reference_symptom_data)
        self._reference_symptom_changed()
        self.ui.tableWidget_reference_list.setFocus()

    def _set_reference_symptom_data(self, row_no, row):
        medical_record_summary = '''日期: {case_date} 病歷號: {patient_key} 姓名: {name}\n{symptom} '''.format(
            case_date=string_utils.xstr(row['CaseDate'].date()),
            patient_key=string_utils.xstr(row['PatientKey']),
            name=string_utils.xstr(row['Name']),
            symptom=string_utils.get_str(row['Symptom'], 'utf8'),
        )
        medical_record_symptom = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['Birthday']),
            string_utils.xstr(row['InsType']),
            medical_record_summary,
        ]

        for column in range(len(medical_record_symptom)):
            self.ui.tableWidget_reference_symptom.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record_symptom[column])
            )

    def _reference_symptom_changed(self):
        case_key = self.table_widget_reference_symptom.field_value(0)
        if case_key is None:
            return

        patient_key = self.table_widget_reference_symptom.field_value(1)
        name = self.table_widget_reference_symptom.field_value(2)
        gender = self.table_widget_reference_symptom.field_value(3)
        birthday = self.table_widget_reference_symptom.field_value(4)

        self._set_copy_prescript_check_box()
        html = case_utils.get_medical_record_html(self.database, self.system_settings, case_key)
        self.ui.textEdit_medical_record.setHtml(html)

        self.ui.groupBox_medical_record.setTitle(
            '病歷號: {patient_key} {name}({gender}) 出生日期: {birthday}  病歷內容'.format(
                patient_key=patient_key,
                name=name,
                gender=gender,
                birthday=birthday,
            )
        )

    def _set_copy_prescript_check_box(self):
        case_key = self.table_widget_reference_symptom.field_value(0)
        ins_type = self.table_widget_reference_symptom.field_value(5)

        self.ui.checkBox_ins_prescript.setChecked(False)  # 健保療程2-6次預設不拷貝藥品
        self.ui.checkBox_ins_prescript.setEnabled(False)  # 健保療程2-6次預設不拷貝藥品

        self.ui.radioButton_ins_prescript.setEnabled(False)
        self.ui.radioButton_self_prescript.setEnabled(False)

        self.ui.checkBox_ins_treat.setChecked(False)
        self.ui.checkBox_ins_treat.setEnabled(False)

        if ins_type == '健保':
            sql = 'SELECT Treatment FROM cases WHERE CaseKey = {0}'.format(case_key)
            rows = self.database.select_record(sql)
            treatment = string_utils.xstr(rows[0]['Treatment'])

            if treatment != '':
                self.ui.checkBox_ins_treat.setEnabled(True)
                self.ui.checkBox_ins_treat.setChecked(True)

            sql = '''
                SELECT PrescriptKey FROM prescript 
                WHERE 
                    CaseKey = {case_key} AND 
                    MedicineSet = 1 
            '''.format(
                case_key=case_key,
            )
            rows = self.database.select_record(sql)
            if len(rows) > 0:
                self.ui.checkBox_ins_prescript.setEnabled(True)
                self.ui.radioButton_ins_prescript.setEnabled(True)
                self.ui.radioButton_self_prescript.setEnabled(True)
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

    def _edit_past_history(self):
        case_key = self.table_widget_reference_symptom.field_value(0)
        self.parent.parent.open_medical_record(case_key, '過去病歷')
        self.copy_medical_record = False

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def _cancel_reference(self):
        name = self.table_widget_reference_symptom.field_value(2)
        msg_box = dialog_utils.get_message_box(
            '解除參考病歷', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定解除{0}的參考病歷?</b></font>'.format(name),
            '提示！參考病歷解除後, 病歷並不會被刪除!'
        )

        cancel_reference = msg_box.exec_()
        if not cancel_reference:
            return

        case_key = self.table_widget_reference_symptom.field_value(0)
        self.database.exec_sql('UPDATE cases SET Reference = "False" WHERE CaseKey = {0}'.format(case_key))

        self._read_medical_record_reference()
        self._reference_list_changed()
        self._reference_symptom_changed()

