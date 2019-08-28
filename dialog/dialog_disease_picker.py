#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui

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
        self.icd_code = args[2]

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
        system_utils.set_css(self, self.system_settings)
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
        self.ui.radioButton_all.clicked.connect(self._read_data)
        self.ui.radioButton_chronic.clicked.connect(self._read_data)

    def _table_double_clicked(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def accepted_button_clicked(self):
        self.icd10_key = self.table_widget_disease.field_value(0)
        self.icd_code = self.table_widget_disease.field_value(1)
        self.special_code = self.table_widget_disease.field_value(2)
        self.chinese_name = self.table_widget_disease.field_value(3)
        self.close()

    def _get_sql_script(self):
        chronic_script = ''
        if self.ui.radioButton_chronic.isChecked():
            chronic_script = ' AND SpecialCode IS NOT NULL '

        if self.icd_code.isdigit():
            sql = '''
                SELECT
                    icd10.ICD10Key,
                    icd10.ICDCode,
                    icd10.ChineseName,
                    icd10.EnglishName,
                    icd10.SpecialCode
                FROM icdmap
                    LEFT JOIN icd10 ON icdmap.ICD10Code = icd10.ICDCode
                WHERE
                    ICD9Code LIKE "{0}%"
                    {1}
                ORDER BY icd10.ICDCode
            '''.format(self.icd_code, chronic_script)
        else:
            order_type = 'ORDER BY ICDCode'
            if self.system_settings.field('詞庫排序') == '點擊率':
                order_type = 'ORDER BY HitRate DESC, ICDCode'

            keyword_list = self.icd_code.split()
            chinese_name_script = []
            for keyword in keyword_list:
                chinese_name_script.append('ChineseName LIKE "%{0}%"'.format(keyword))

            if len(chinese_name_script) > 0:
                chinese_name_script = ' AND '.join(chinese_name_script)
                chinese_name_script = 'OR ({0})'.format(chinese_name_script)

            sql = '''
                SELECT * FROM icd10
                WHERE
                    ICDCode LIKE "{icd_code}%" OR
                    InputCode LIKE "%{icd_code}%"
                    {chinese_name_script}
                    {chronic_script}
            '''.format(
                icd_code=self.icd_code,
                chinese_name_script=chinese_name_script,
                chronic_script=chronic_script,
            )

            sql += order_type + ' LIMIT 300'

        return sql

    def _read_data(self):
        sql = self._get_sql_script()
        self.table_widget_disease.set_db_data(sql, self._set_table_data)
        for row_no in range(self.ui.tableWidget_disease.rowCount()-1, -1, -1):
            icd_code = self.ui.tableWidget_disease.item(row_no, 1).text()
            sql = 'SELECT ICDCode FROM icd10 WHERE ICDCode LIKE "{0}%" LIMIT 2'.format(icd_code)
            temp_rows = self.database.select_record(sql)
            if len(temp_rows) >= 2:
                self.ui.tableWidget_disease.removeRow(row_no)

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
            if icd_code_row[2] != '':
                self.ui.tableWidget_disease.item(
                    row_no, column).setForeground(
                    QtGui.QColor('red')
                )
