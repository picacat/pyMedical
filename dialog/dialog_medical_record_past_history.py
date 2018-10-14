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


# 主視窗
class DialogMedicalRecordPastHistory(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordPastHistory, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_key = args[2]
        self.ui = None

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
        system_utils.set_css(self)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('拷貝病歷')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_past_history = table_widget.TableWidget(self.ui.tableWidget_past_history, self.database)
        self.table_widget_past_history.set_column_hidden([0])
        self._set_table_width()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 120, 50, 80, 60, 50, 180, 80, 80]
        self.table_widget_past_history.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_past_history.itemSelectionChanged.connect(self._past_history_changed)

    def accepted_button_clicked(self):
        case_key = self.table_widget_past_history.field_value(0)

        case_utils.copy_past_medical_record(
            self.database, self.parent, case_key,
            self.ui.checkBox_diagnostic.isChecked(),
            self.ui.checkBox_remark.isChecked(),
            self.ui.checkBox_disease.isChecked(),
            self.ui.checkBox_prescript.isChecked(),
        )

    def get_past_case_key(self):
        case_key = self.table_widget_past_history.field_value(0)

        return case_key

    def _read_past_history(self):
        sql = '''
            SELECT cases.*, patient.Gender, patient.Birthday FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                cases.PatientKey = {0}
            ORDER BY CaseDate DESC
        '''.format(self.patient_key)

        rows = self.database.select_record(sql)
        if len(rows) > 0:
            self._set_group_box_title(rows[0])

        self.table_widget_past_history.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row_data):
        medical_record_data = [
            string_utils.xstr(row_data['CaseKey']),
            string_utils.xstr(row_data['CaseDate'].date()),
            string_utils.xstr(row_data['InsType']),
            string_utils.xstr(row_data['TreatType']),
            string_utils.xstr(row_data['Card']),
            string_utils.xstr(row_data['Continuance']),
            string_utils.xstr(row_data['DiseaseName1']),
            string_utils.xstr(row_data['Doctor']),
            string_utils.xstr('{0:,}'.format(number_utils.get_integer(row_data['TotalFee']))),
        ]

        for column in range(len(medical_record_data)):
            self.ui.tableWidget_past_history.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record_data[column])
            )
            if column in [0, 8]:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5]:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row_data['InsType'] == '自費' or number_utils.get_integer(row_data['TotalFee']) > 0:
                self.ui.tableWidget_past_history.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
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
        html = case_utils.get_medical_record_html(self.database, case_key)
        self.ui.textEdit_medical_record.setHtml(html)

