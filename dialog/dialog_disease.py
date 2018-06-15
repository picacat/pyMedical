#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui
from classes import table_widget
from libs import ui_settings
from libs import system
from libs import strings


# 主視窗
class DialogDisease(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogDisease, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.line_edit_icd_code = args[2]
        self.line_edit_disease_name = args[3]

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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_DISEASE, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setText('選取')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText('關閉')
        self.ui.tableWidget_disease.doubleClicked.connect(self.accepted_button_clicked)
        self.table_widget_groups_name = table_widget.TableWidget(self.ui.tableWidget_groups_name, self.database)
        self.table_widget_groups_name.set_column_hidden([0])
        self.table_widget_disease = table_widget.TableWidget(self.ui.tableWidget_disease, self.database)
        self.table_widget_disease.set_column_hidden([0])
        self._set_table_width()
        self._set_groups()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.buttonBox.rejected.connect(self.rejected_button_clicked)
        self.ui.tableWidget_groups.itemSelectionChanged.connect(self.groups_changed)
        self.ui.tableWidget_groups_name.itemSelectionChanged.connect(self.groups_name_changed)

    # 存檔
    def accepted_button_clicked(self):
        self.line_edit_icd_code.setText(self.table_widget_disease.field_value(1))
        self.line_edit_disease_name.setText(self.table_widget_disease.field_value(3))
        self.line_edit_icd_code.setModified(True)
        self.close()

    # 關閉
    def rejected_button_clicked(self):
        self.close()

    # 設定欄位寬度
    def _set_table_width(self):
        groups_name_width = [100, 450]
        disease_width = [100, 100, 70, 590]
        self.table_widget_disease.set_table_heading_width(disease_width)
        self.table_widget_groups_name.set_table_heading_width(groups_name_width)

    def _set_groups(self):
        for row in range(0, 5):
            sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "病名類別" limit {0}, 5'.format(row * 5)
            rows = self.database.select_record(sql)
            for col in range(0, len(rows)):
                self.ui.tableWidget_groups.setItem(row, col, QtWidgets.QTableWidgetItem(rows[col]['DictGroupsName']))

        self.ui.tableWidget_groups.setCurrentCell(0, 0)
        groups = self.ui.tableWidget_groups.selectedItems()[0].text()
        self._read_groups_name(groups)
        groups_name = self.table_widget_groups_name.field_value(1)
        self._read_disease(groups_name)
        self.ui.tableWidget_groups.setFocus(True)

    def groups_changed(self):
        groups = self.ui.tableWidget_groups.selectedItems()[0].text()
        self._read_groups_name(groups)
        groups_name = self.table_widget_groups_name.field_value(1)
        self._read_disease(groups_name)
        self.ui.tableWidget_groups.setFocus(True)

    def _read_groups_name(self, groups):
        sql = '''
            SELECT * FROM dict_groups WHERE DictGroupsType = "病名" and DictGroupsTopLevel = "{0}" 
            ORDER BY DictGroupsName
        '''.format(groups)
        self.table_widget_groups_name.set_db_data(sql, self._set_groups_name_data)

    def _set_groups_name_data(self, rec_no, rec):
        groups_name_rec = [
            strings.xstr(rec['DictGroupsKey']),
            strings.xstr(rec['DictGroupsName']),
        ]

        for column in range(0, self.ui.tableWidget_groups_name.columnCount()):
            self.ui.tableWidget_groups_name.setItem(rec_no, column, QtWidgets.QTableWidgetItem(groups_name_rec[column]))

    def groups_name_changed(self):
        groups_name = self.table_widget_groups_name.field_value(1)
        self._read_disease(groups_name)
        self.ui.tableWidget_groups_name.setFocus(True)

    def _read_disease(self, groups_name):
        sql = '''
            SELECT * FROM icd10 WHERE Groups = "{0}"
            ORDER BY ICDCode
        '''.format(groups_name)
        self.table_widget_disease.set_db_data(sql, self._set_disease_data)

    def _set_disease_data(self, rec_no, rec):
        disease_rec = [
            strings.xstr(rec['ICD10Key']),
            strings.xstr(rec['ICDCode']),
            strings.xstr(rec['SpecialCode']),
            strings.xstr(rec['ChineseName']),
        ]

        for column in range(0, self.ui.tableWidget_disease.columnCount()):
            self.ui.tableWidget_disease.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(disease_rec[column])
            )
            if strings.xstr(rec['SpecialCode']) != '':
                self.ui.tableWidget_disease.item(
                    rec_no, column
                ).setForeground(QtGui.QColor('red'))
