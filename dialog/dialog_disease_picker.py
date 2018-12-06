#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils


# 主視窗
class DialogDiseasePicker(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogDiseasePicker, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.sql = args[2]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_DISEASE_PICKER, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_disease = table_widget.TableWidget(
            self.ui.tableWidget_disease, self.database)
        self._set_table_width()
        self.table_widget_disease.set_column_hidden([0])
        self.ui.tableWidget_disease.setFocus()

    def _set_table_width(self):
        width = [100, 100, 80, 400, 340]
        self.table_widget_disease.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_disease.doubleClicked.connect(self._table_double_clicked)

    def _table_double_clicked(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def accepted_button_clicked(self):
        self.icd_code = self.table_widget_disease.field_value(1)
        self.special_code = self.table_widget_disease.field_value(2)
        self.chinese_name = self.table_widget_disease.field_value(3)
        self.close()

    def _read_data(self):
        self.table_widget_disease.set_db_data(self.sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        icd_code_row = [
            string_utils.xstr(row['ICD10Key']),
            string_utils.xstr(row['ICDCode']),
            string_utils.xstr(row['SpecialCode']),
            string_utils.xstr(row['ChineseName']),
            string_utils.xstr(row['EnglishName']),
        ]

        for column in range(len(icd_code_row)):
            self.ui.tableWidget_disease.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(icd_code_row[column])
            )
