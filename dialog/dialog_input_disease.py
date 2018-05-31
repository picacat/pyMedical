#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from classes import table_widget
from libs import ui_settings
from libs import system
from libs import strings


# 主視窗
class DialogInputDisease(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputDisease, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.groups_name = args[2]

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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_INPUT_DISEASE, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_disease = table_widget.TableWidget(self.ui.tableWidget_disease, self.database)
        self.table_widget_disease.set_column_hidden([0])
        self.ui.label_groups_name.setText(self.groups_name)
        self._set_table_width()
        self.ui.lineEdit_icd10.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.lineEdit_icd10.textChanged.connect(self.icd10_text_changed)
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def accepted_button_clicked(self):
        selected = self.ui.tableWidget_disease.selectedRanges()
        icd10_list = []
        for item in selected:
            for r in range(item.topRow(), item.bottomRow() + 1):
               icd10_list.append(self.ui.tableWidget_disease.item(r, 0).text())

        for icd10 in icd10_list:
            sql = 'UPDATE icd10 set Groups = "{0}" WHERE ICD10Key = {1}'.format(self.groups_name, icd10)
            self.database.exec_sql(sql)

        self.parent.read_dict_disease(self.groups_name)

    # 設定欄位寬度
    def _set_table_width(self):
        disease_width = [100, 120, 800]
        self.table_widget_disease.set_table_heading_width(disease_width)

    def icd10_text_changed(self):
        icd10 = str(self.ui.lineEdit_icd10.text()).strip()
        if icd10 == '':
            self.ui.tableWidget_disease.setRowCount(0)
            return

        self._read_icd10(icd10)
        self.ui.lineEdit_icd10.setFocus(True)
        self.ui.lineEdit_icd10.setCursorPosition(len(icd10))

    def _read_icd10(self, icd10):
        sql = 'SELECT * FROM icd10 WHERE ICDCode like "{0}%"'.format(icd10)
        rows = self.database.select_record(sql)
        self.table_widget_disease.set_db_data(sql, self._set_disease)

    def _set_disease(self, rec_no, rec):
        disease_rec = [
            strings.xstr(rec['ICD10Key']),
            strings.xstr(rec['ICDCode']),
            strings.xstr(rec['ChineseName']),
        ]

        for column in range(0, self.ui.tableWidget_disease.columnCount()):
            self.ui.tableWidget_disease.setItem(rec_no, column, QtWidgets.QTableWidgetItem(disease_rec[column]))
