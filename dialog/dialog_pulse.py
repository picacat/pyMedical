#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from classes import table_widget


# 主視窗
class DialogPulse(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogPulse, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.groups = args[2]
        self.text_edit = args[3]

        self.ui = None
        self.diagnostic_type = '脈象'

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_PULSE, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.table_widget_groups = table_widget.TableWidget(self.ui.tableWidget_groups, self.database)
        self.table_widget_pulse = table_widget.TableWidget(self.ui.tableWidget_pulse, self.database)
        self.table_widget_groups.set_column_hidden([0])
        self.table_widget_pulse.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_groups.itemSelectionChanged.connect(self.groups_name_changed)
        self.ui.tableWidget_pulse.clicked.connect(self.add_pulse)
        self.ui.tableWidget_pulse.keyPressEvent = self._table_widget_key_press

    def _table_widget_key_press(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.parent.close()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_pulse, event)

    # 設定欄位寬度
    def _set_table_width(self):
        groups_width = [100, 200]
        pulse_width = [100, 800]
        self.table_widget_groups.set_table_heading_width(groups_width)
        self.table_widget_pulse.set_table_heading_width(pulse_width)

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

        for column in range(0, self.ui.tableWidget_groups.columnCount()):
            self.ui.tableWidget_groups.setItem(rec_no, column, QtWidgets.QTableWidgetItem(groups_name_rec[column]))

    def groups_name_changed(self):
        groups_name = self.table_widget_groups.field_value(1)
        self._read_pulse(groups_name)
        self.ui.tableWidget_groups.setFocus(True)

    def _read_pulse(self, groups_name):
        sql = '''
            SELECT * FROM clinic WHERE ClinicType = "{0}" and Groups = "{1}" 
            ORDER BY ClinicCode, ClinicName
        '''.format(self.diagnostic_type, groups_name)
        self.table_widget_pulse.set_db_data(sql, self._set_pulse_data)

    def _set_pulse_data(self, rec_no, rec):
        pulse_rec = [
            string_utils.xstr(rec['ClinicKey']),
            string_utils.xstr(rec['ClinicName']),
        ]

        for column in range(0, self.ui.tableWidget_pulse.columnCount()):
            self.ui.tableWidget_pulse.setItem(rec_no, column, QtWidgets.QTableWidgetItem(pulse_rec[column]))

    def add_pulse(self):
        selected_pulse = self.table_widget_pulse.field_value(1)
        pulse = self.text_edit.toPlainText()
        pulse += '，' + selected_pulse \
            if str(pulse).strip()[-1:] not in ['，', ',', ':', '='] and len(str(pulse).strip()) > 0 \
            else selected_pulse
        self.text_edit.setText(string_utils.get_str(pulse, 'utf8'))
        self.text_edit.document().setModified(True)
