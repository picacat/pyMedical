#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import db_utils
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
        self.diagnostic_type = '主訴'

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_SYMPTOM, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.table_widget_groups = table_widget.TableWidget(self.ui.tableWidget_groups, self.database)
        self.table_widget_symptom = table_widget.TableWidget(self.ui.tableWidget_symptom, self.database)
        self.table_widget_groups.set_column_hidden([0])
        self.table_widget_symptom.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_groups.itemSelectionChanged.connect(self.groups_name_changed)
        self.ui.tableWidget_symptom.clicked.connect(self.add_symptom)
        self.ui.tableWidget_groups.keyPressEvent = self._table_widget_key_press
        self.ui.tableWidget_symptom.keyPressEvent = self._table_widget_key_press

    # 設定欄位寬度
    def _set_table_width(self):
        groups_width = [100, 200]
        symptom_width = [100, 800]
        self.table_widget_groups.set_table_heading_width(groups_width)
        self.table_widget_symptom.set_table_heading_width(symptom_width)

    def _table_widget_key_press(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.parent.close()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_symptom, event)

    def _read_groups_name(self):
        sql = '''
            SELECT * FROM dict_groups WHERE DictGroupsType = "{0}" and DictGroupsTopLevel = "{1}" 
            ORDER BY DictGroupsName
        '''.format(self.diagnostic_type, self.groups)
        self.table_widget_groups.set_db_data(sql, self._set_groups_name_data)

    def _set_groups_name_data(self, rec_no, rec):
        groups_name_rec = [
            string_utils.xstr(rec['DictGroupsKey']),
            string_utils.xstr(rec['DictGroupsName']),
        ]

        for column in range(len(groups_name_rec)):
            self.ui.tableWidget_groups.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(groups_name_rec[column])
            )

    def groups_name_changed(self):
        groups_name = self.table_widget_groups.field_value(1)
        self._read_symptom(groups_name)
        self.ui.tableWidget_groups.setFocus(True)

    def _read_symptom(self, groups_name):
        sql = '''
            SELECT * FROM clinic WHERE ClinicType = "{0}" and Groups = "{1}" 
            ORDER BY ClinicCode, ClinicName
        '''.format(self.diagnostic_type, groups_name)
        self.table_widget_symptom.set_db_data(sql, self._set_symptom_data)

    def _set_symptom_data(self, rec_no, rec):
        symptom_rec = [
            string_utils.xstr(rec['ClinicKey']),
            string_utils.xstr(rec['ClinicName']),
        ]

        for column in range(len(symptom_rec)):
            self.ui.tableWidget_symptom.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(symptom_rec[column])
            )

    def add_symptom(self):
        # selected_symptom = self.table_widget_symptom.field_value(1)
        # self.text_edit.insertPlainText(selected_symptom)
        # self.text_edit.document().setModified(True)

        clinic_key = self.table_widget_symptom.field_value(0)
        selected_symptom = self.table_widget_symptom.field_value(1)
        symptom = self.text_edit.toPlainText()
        symptom += '，' + selected_symptom \
            if str(symptom).strip()[-1:] not in ['，', ',', ', ', ':', '='] and len(str(symptom).strip()) > 0 \
            else selected_symptom
        self.text_edit.setText(string_utils.get_str(symptom, 'utf8'))
        db_utils.increment_hit_rate(self.database, 'clinic', 'ClinicKey', clinic_key)


        self.text_edit.document().setModified(True)

        self.parent.reset_query()
