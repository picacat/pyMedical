#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
import datetime

from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import nhi_utils
from libs import personnel_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils


# 過去病歷視窗
class DialogMedicalRecordPastHistory(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordPastHistory, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.patient_key = args[3]
        self.call_from = args[4]

        self.ui = None
        self.copy_medical_record = True

        self._set_ui()
        self._set_signal()
        self._read_past_history()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICAL_RECORD_PAST_HISTORY, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('拷貝病歷')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_past_history = table_widget.TableWidget(self.ui.tableWidget_past_history, self.database)
        self.table_widget_past_history.set_column_hidden([0])
        self._set_table_width()
        if self.call_from == '病歷查詢':
            self.ui.groupBox_copy_option.setVisible(False)
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setVisible(False)
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('關閉')

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 120, 50, 80, 60, 50, 180, 45, 80, 80]
        self.table_widget_past_history.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_past_history.itemSelectionChanged.connect(self._past_history_changed)
        self.ui.tableWidget_past_history.doubleClicked.connect(self._edit_past_history)

    def accepted_button_clicked(self):
        if not self.copy_medical_record:
            return

        case_key = self.table_widget_past_history.field_value(0)

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

    def get_past_case_key(self):
        case_key = self.table_widget_past_history.field_value(0)

        return case_key

    def _read_past_history(self):
        case_key_exclude = ''
        if self.call_from == '病歷登錄' and self.case_key is not None:
            case_key_exclude = 'AND CaseKey != {case_key}'.format(case_key=self.case_key)

        sql = '''
            SELECT cases.*, patient.Gender, patient.Birthday FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                cases.PatientKey = {patient_key}
                {case_key_exclude}
            ORDER BY CaseDate DESC, FIELD(cases.InsType, {ins_type})
        '''.format(
            patient_key=self.patient_key,
            case_key_exclude=case_key_exclude,
            ins_type=string_utils.xstr(nhi_utils.INS_TYPE)[1:-1],
        )

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            html = '''
                {br} 
                <center><b>無過去病歷</b></center>
            '''.format(
                br='<br>' * 12,
            )
            self.ui.textEdit_medical_record.setHtml(html)
            self.ui.groupBox_copy_option.setEnabled(False)
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

            return

        self._set_group_box_title(rows[0])
        self.table_widget_past_history.set_db_data(sql, self._set_table_data)

        if self.call_from == '病歷查詢' and self.case_key is not None:
            self._locate_medical_record()

    def _set_table_data(self, row_no, row):
        if row['InsType'] == '健保':
            medicine_set = 1
        else:
            medicine_set = 2

        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = {1}
        '''.format(row['CaseKey'], medicine_set)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            pres_days = rows[0]['Days']
        else:
            pres_days = None

        medical_record_data = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(pres_days),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr('{0:,}'.format(number_utils.get_integer(row['TotalFee']))),
        ]

        for column in range(len(medical_record_data)):
            self.ui.tableWidget_past_history.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record_data[column])
            )
            if column in [0, 7, 9]:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5]:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費' or number_utils.get_integer(row['TotalFee']) > 0:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

            if row['Continuance'] == 1:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setBackground(
                    QtGui.QColor('lightgray')
                )

    def _set_group_box_title(self, row):
        self.ui.groupBox_history_list.setTitle(
            '{0} 過去病歷一覽表'.format(string_utils.xstr(row['Name'])),
        )
        self.ui.groupBox_medical_record.setTitle(
            '病歷號: {0} {1}({2}) 出生日期: {3}  病歷內容'.format(
                string_utils.xstr(row['PatientKey']),
                string_utils.xstr(row['Name']),
                string_utils.xstr(row['Gender']),
                string_utils.xstr(row['Birthday']),
            )
        )

    def _past_history_changed(self):
        case_key = self.table_widget_past_history.field_value(0)

        self._set_copy_prescript_check_box()
        html = case_utils.get_medical_record_html(self.database, self.system_settings, case_key)
        self.ui.textEdit_medical_record.setHtml(html)

    def _set_copy_prescript_check_box(self):
        case_key = self.table_widget_past_history.field_value(0)
        ins_type = self.table_widget_past_history.field_value(2)

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
            if self.system_settings.field('預設拷貝自費處方') == 'Y':
                self.ui.checkBox_self_prescript.setChecked(True)
            else:
                self.ui.checkBox_self_prescript.setChecked(False)

    def _edit_past_history(self):
        case_key = self.table_widget_past_history.field_value(0)
        self.parent.parent.open_medical_record(case_key, '過去病歷')
        self.copy_medical_record = False

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def _locate_medical_record(self):
        for row_no in range(self.ui.tableWidget_past_history.rowCount()):
            item = self.ui.tableWidget_past_history.item(row_no, 0)
            self.ui.tableWidget_past_history.scrollToItem(item, QtWidgets.QAbstractItemView.PositionAtCenter)
            self.ui.tableWidget_past_history.selectRow(row_no)

            if item.text() == string_utils.xstr(self.case_key):
                break
