#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from libs import ui_settings
from libs import system
from libs import strings
from classes import table_widget


# 主視窗
class DialogSymptom(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogSymptom, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.groups = args[2]
        self.text_edit = args[3]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_groups_name()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_SYMPTOM, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self.table_widget_groups = table_widget.TableWidget(self.ui.tableWidget_groups, self.database)
        self.table_widget_symptom = table_widget.TableWidget(self.ui.tableWidget_symptom, self.database)
        self.table_widget_groups.set_column_hidden([0])
        self.table_widget_symptom.set_column_hidden([0])
        self._set_table_width()

    # 設定欄位寬度
    def _set_table_width(self):
        groups_width = [100, 200]
        symptom_width = [100, 430]
        self.table_widget_groups.set_table_heading_width(groups_width)
        self.table_widget_symptom.set_table_heading_width(symptom_width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_groups.itemSelectionChanged.connect(self.groups_name_changed)
        self.ui.tableWidget_symptom.clicked.connect(self.add_symptom)

    def _read_groups_name(self):
        sql = '''
            SELECT * FROM dict_groups WHERE DictGroupsType = "主訴" and DictGroupsTopLevel = "{0}" 
            ORDER BY DictGroupsName
        '''.format(self.groups)
        self.table_widget_groups.set_db_data(sql, self._set_groups_name_data)

    def _set_groups_name_data(self, rec_no, rec):
        groups_name_rec = [
            strings.xstr(rec['DictGroupsKey']),
            strings.xstr(rec['DictGroupsName']),
        ]

        for column in range(0, self.ui.tableWidget_groups.columnCount()):
            self.ui.tableWidget_groups.setItem(rec_no, column, QtWidgets.QTableWidgetItem(groups_name_rec[column]))

    def groups_name_changed(self):
        groups_name = self.table_widget_groups.field_value(1)
        self._read_symptom(groups_name)

    def _read_symptom(self, groups_name):
        sql = '''
            SELECT * FROM clinic WHERE ClinicType = "主訴" and Groups = "{0}" 
            ORDER BY ClinicCode, ClinicName
        '''.format(groups_name)
        self.table_widget_symptom.set_db_data(sql, self._set_symptom_data)

    def _set_symptom_data(self, rec_no, rec):
        symptom_rec = [
            strings.xstr(rec['ClinicKey']),
            strings.xstr(rec['ClinicName']),
        ]

        for column in range(0, self.ui.tableWidget_symptom.columnCount()):
            self.ui.tableWidget_symptom.setItem(rec_no, column, QtWidgets.QTableWidgetItem(symptom_rec[column]))

    def add_symptom(self):
        selected_symptom = self.table_widget_symptom.field_value(1)
        symptom = self.text_edit.toPlainText()
        symptom += '，' + selected_symptom if str(symptom[-1:]).strip() != '，' and len(str(symptom).strip()) > 0 \
            else selected_symptom
        self.text_edit.setText(strings.get_str(symptom, 'utf8'))
