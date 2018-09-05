#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from libs import dialog_utils
from classes import table_widget
from dialog import dialog_input_diagnostic


# 收費設定 2018.04.14
class DictPulse(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictPulse, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.dict_type = '脈象'

        self._set_ui()
        self._set_signal()
        self._read_pulse()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_PULSE, self)
        self.table_widget_dict_groups = table_widget.TableWidget(self.ui.tableWidget_dict_groups, self.database)
        self.table_widget_dict_groups.set_column_hidden([0])
        self.table_widget_dict_groups_name = table_widget.TableWidget(self.ui.tableWidget_dict_groups_name, self.database)
        self.table_widget_dict_groups_name.set_column_hidden([0])
        self.table_widget_dict_pulse = table_widget.TableWidget(self.ui.tableWidget_dict_pulse, self.database)
        self.table_widget_dict_pulse.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_groups.itemSelectionChanged.connect(self.dict_groups_changed)
        self.ui.tableWidget_dict_groups_name.itemSelectionChanged.connect(self.dict_groups_name_changed)
        self.ui.toolButton_add_dict_groups.clicked.connect(self._add_dict_groups)
        self.ui.toolButton_remove_dict_groups.clicked.connect(self._remove_dict_groups)
        self.ui.toolButton_edit_dict_groups.clicked.connect(self._edit_dict_groups)
        self.ui.tableWidget_dict_groups.doubleClicked.connect(self._edit_dict_groups)
        self.ui.toolButton_add_groups_name.clicked.connect(self._add_groups_name)
        self.ui.toolButton_remove_groups_name.clicked.connect(self._remove_groups_name)
        self.ui.toolButton_edit_groups_name.clicked.connect(self._edit_groups_name)
        self.ui.tableWidget_dict_groups_name.doubleClicked.connect(self._edit_groups_name)
        self.ui.toolButton_add_pulse.clicked.connect(self._add_pulse)
        self.ui.toolButton_remove_pulse.clicked.connect(self._remove_pulse)
        self.ui.toolButton_edit_pulse.clicked.connect(self._edit_pulse)
        self.ui.tableWidget_dict_pulse.doubleClicked.connect(self._edit_pulse)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_groups_width = [100, 180]
        dict_pulse_width = [100, 180, 180, 750]
        self.table_widget_dict_groups.set_table_heading_width(dict_groups_width)
        self.table_widget_dict_groups_name.set_table_heading_width(dict_groups_width)
        self.table_widget_dict_pulse.set_table_heading_width(dict_pulse_width)

    def _read_pulse(self):
        self._read_dict_groups()

    def _read_dict_groups(self):
        sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "{0}類別" ORDER BY DictGroupsKey'.format(self.dict_type)
        self.table_widget_dict_groups.set_db_data(sql, self._set_dict_groups_data)

    def _set_dict_groups_data(self, rec_no, rec):
        dict_groups_rec = [
            string_utils.xstr(rec['DictGroupsKey']),
            string_utils.xstr(rec['DictGroupsName']),
        ]

        for column in range(len(dict_groups_rec)):
            self.ui.tableWidget_dict_groups.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_groups_rec[column])
            )

    def dict_groups_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        self.ui.groupBox_dict_groups_name.setTitle(string_utils.xstr(dict_groups_type) + '類別')
        self._read_dict_groups_name(dict_groups_type)
        self.ui.tableWidget_dict_groups.setFocus(True)

    def _read_dict_groups_name(self, dict_groups_type):
        sql = '''
            SELECT * FROM dict_groups WHERE DictGroupsType = "{0}" and DictGroupsTopLevel = "{1}" 
            ORDER BY DictGroupsName
        '''.format(self.dict_type, dict_groups_type)
        self.table_widget_dict_groups_name.set_db_data(sql, self._set_dict_groups_name_data)
        self.dict_groups_name_changed()

    def _set_dict_groups_name_data(self, rec_no, rec):
        dict_groups_name_rec = [
            string_utils.xstr(rec['DictGroupsKey']),
            string_utils.xstr(rec['DictGroupsName']),
        ]

        for column in range(len(dict_groups_name_rec)):
            self.ui.tableWidget_dict_groups_name.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_groups_name_rec[column])
            )

    def dict_groups_name_changed(self):
        dict_groups_name = self.table_widget_dict_groups_name.field_value(1)
        self.ui.groupBox_dict_pulse.setTitle('{0}資料 - ['.format(self.dict_type) +
                                             string_utils.xstr(dict_groups_name) +
                                               ']')
        self._read_dict_pulse(dict_groups_name)
        self.ui.tableWidget_dict_groups_name.setFocus(True)

    def _read_dict_pulse(self, dict_groups_name):
        sql = '''
            SELECT * FROM clinic WHERE ClinicType = "{0}" and Groups = "{1}" ORDER BY ClinicCode, ClinicName
        '''.format(self.dict_type, dict_groups_name)
        self.table_widget_dict_pulse.set_db_data(sql, self._set_dict_pulse_data)

    def _set_dict_pulse_data(self, rec_no, rec):
        dict_pulse_rec = [
            string_utils.xstr(rec['ClinicKey']),
            string_utils.xstr(rec['ClinicCode']),
            string_utils.xstr(rec['InputCode']),
            string_utils.xstr(rec['ClinicName']),
        ]

        for column in range(len(dict_pulse_rec)):
            self.ui.tableWidget_dict_pulse.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_pulse_rec[column])
            )

    # 新增主訴類別
    def _add_dict_groups(self):
        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入{0}類別'.format(self.dict_type),
            None, QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_groups = input_dialog.textValue()
        field = ['DictGroupsType', 'DictGroupsName']
        data = [
            '{0}類別'.format(self.dict_type), dict_groups,
        ]
        self.database.insert_record('dict_groups', field, data)
        self._read_dict_groups()

    # 移除主訴類別
    def _remove_dict_groups(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}類別資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除 [{0}] {1}類別?</b></font>'.format(
                self.table_widget_dict_groups.field_value(1), self.dict_type),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_groups.field_value(0)
        self.database.delete_record('dict_groups', 'DictGroupsKey', key)
        self.ui.tableWidget_dict_groups.removeRow(self.ui.tableWidget_dict_groups.currentRow())

    # 更改主訴類別
    def _edit_dict_groups(self):
        old_groups = self.table_widget_dict_groups.field_value(1)
        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入{0}類別'.format(self.dict_type),
            old_groups,
            QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_groups_name = input_dialog.textValue()
        data = [
            dict_groups_name,
        ]

        sql = '''
            UPDATE dict_groups set DictGroupsTopLevel = "{0}" WHERE 
            DictGroupsType = "{1}" and DictGroupsTopLevel = "{2}"
        '''.format(dict_groups_name, self.dict_type, old_groups)
        self.database.exec_sql(sql)

        fields = ['DictGroupsName']
        self.database.update_record('dict_groups', fields, 'DictGroupsKey',
                                    self.table_widget_dict_groups.field_value(0), data)
        self.ui.tableWidget_dict_groups.item(self.ui.tableWidget_dict_groups.currentRow(), 1).setText(dict_groups_name)

    # 新增主訴類別
    def _add_groups_name(self):
        dict_groups = self.table_widget_dict_groups.field_value(1)
        input_dialog = dialog_utils.get_dialog(
            '{0}分類'.format(self.dict_type), '請輸入{0}分類名稱'.format(self.dict_type),
            None, QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        groups_name = input_dialog.textValue()
        field = ['DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName']
        data = [
            '{0}'.format(self.dict_type), dict_groups, groups_name
        ]
        self.database.insert_record('dict_groups', field, data)
        self._read_dict_groups_name(dict_groups)

    # 移除主訴類別
    def _remove_groups_name(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}分類資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除 [{0}] {1}分類?</b></font>'.format(
                self.table_widget_dict_groups_name.field_value(1), self.dict_type),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_groups_name.field_value(0)
        self.database.delete_record('dict_groups', 'DictGroupsKey', key)
        self.ui.tableWidget_dict_groups_name.removeRow(self.ui.tableWidget_dict_groups_name.currentRow())

    # 修改主訴類別
    def _edit_groups_name(self):
        old_groups_name = self.table_widget_dict_groups_name.field_value(1)
        input_dialog = dialog_utils.get_dialog(
            '{0}分類'.format(self.dict_type), '請輸入{0}分類'.format(self.dict_type),
            old_groups_name,
            QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_groups_name = input_dialog.textValue()
        data = [
            dict_groups_name,
        ]

        sql = '''
            UPDATE clinic set Groups = "{0}" WHERE 
            ClinicType = "{1}" and Groups = "{2}"
        '''.format(dict_groups_name, self.dict_type, old_groups_name)
        self.database.exec_sql(sql)

        fields = ['DictGroupsName']
        self.database.update_record('dict_groups', fields, 'DictGroupsKey',
                                    self.table_widget_dict_groups_name.field_value(0), data)
        self.ui.tableWidget_dict_groups_name.item(
            self.ui.tableWidget_dict_groups_name.currentRow(), 1).setText(dict_groups_name)

    # 新增主訴
    def _add_pulse(self):
        dialog = dialog_input_diagnostic.DialogInputDiagnostic(self, self.database, self.system_settings)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_dict_pulse.rowCount()
            self.ui.tableWidget_dict_pulse.insertRow(current_row)
            dict_groups_name = self.table_widget_dict_groups_name.field_value(1)
            fields = ['ClinicType', 'ClinicCode', 'InputCode', 'ClinicName', 'Groups']
            data = [
                '{0}'.format(self.dict_type),
                dialog.ui.lineEdit_diagnostic_code.text(),
                dialog.ui.lineEdit_input_code.text(),
                dialog.ui.lineEdit_diagnostic_name.text(),
                dict_groups_name,
            ]
            self.database.insert_record('clinic', fields, data)
            self._read_dict_pulse(dict_groups_name)

        dialog.close_all()

    # 移除主訴
    def _remove_pulse(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}: "{1}"?</b></font>'.format(
                self.dict_type, self.table_widget_dict_pulse.field_value(3)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_pulse.field_value(0)
        self.database.delete_record('clinic', 'ClinicKey', key)
        self.ui.tableWidget_dict_pulse.removeRow(self.ui.tableWidget_dict_pulse.currentRow())

    # 更改主訴
    def _edit_pulse(self):
        key = self.table_widget_dict_pulse.field_value(0)
        dialog = dialog_input_diagnostic.DialogInputDiagnostic(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM clinic WHERE ClinicKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_dict_pulse_data(self.ui.tableWidget_dict_pulse.currentRow(), row_data)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = DictPulse()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
