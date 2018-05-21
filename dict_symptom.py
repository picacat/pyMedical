#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QPushButton
from libs import ui_settings
from libs import strings
from libs import dialog_utils
from classes import table_widget
from dialog import dialog_input_diagnostic


# 收費設定 2018.04.14
class DictSymptom(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictSymptom, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_symptom()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DICT_SYMPTOM, self)
        self.table_widget_dict_groups = table_widget.TableWidget(self.ui.tableWidget_dict_groups, self.database)
        self.table_widget_dict_groups.set_column_hidden([0])
        self.table_widget_dict_groups_name = table_widget.TableWidget(self.ui.tableWidget_dict_groups_name, self.database)
        self.table_widget_dict_groups_name.set_column_hidden([0])
        self.table_widget_dict_symptom = table_widget.TableWidget(self.ui.tableWidget_dict_symptom, self.database)
        self.table_widget_dict_symptom.set_column_hidden([0])
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
        self.ui.toolButton_add_symptom.clicked.connect(self._add_symptom)
        self.ui.toolButton_remove_symptom.clicked.connect(self._remove_symptom)
        self.ui.toolButton_edit_symptom.clicked.connect(self._edit_symptom)
        self.ui.tableWidget_dict_symptom.doubleClicked.connect(self._edit_symptom)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_groups_width = [100, 180]
        dict_symptom_width = [100, 180, 180, 750]
        self.table_widget_dict_groups.set_table_heading_width(dict_groups_width)
        self.table_widget_dict_groups_name.set_table_heading_width(dict_groups_width)
        self.table_widget_dict_symptom.set_table_heading_width(dict_symptom_width)

    def _read_symptom(self):
        self._read_dict_groups()

    def _read_dict_groups(self):
        sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "主訴類別" ORDER BY DictGroupsKey'
        self.table_widget_dict_groups.set_db_data(sql, self._set_dict_groups_data)

    def _set_dict_groups_data(self, rec_no, rec):
        dict_groups_rec = [
            strings.xstr(rec['DictGroupsKey']),
            strings.xstr(rec['DictGroupsName']),
        ]

        for column in range(0, self.ui.tableWidget_dict_groups.columnCount()):
            self.ui.tableWidget_dict_groups.setItem(rec_no, column, QtWidgets.QTableWidgetItem(dict_groups_rec[column]))

    def dict_groups_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        self.ui.groupBox_dict_groups_name.setTitle(strings.xstr(dict_groups_type) + '類別')
        self._read_dict_groups_name(dict_groups_type)

    def _read_dict_groups_name(self, dict_groups_type):
        sql = '''
            SELECT * FROM dict_groups WHERE DictGroupsType = "主訴" and DictGroupsTopLevel = "{0}" 
            ORDER BY DictGroupsName
        '''.format(dict_groups_type)
        self.table_widget_dict_groups_name.set_db_data(sql, self._set_dict_groups_name_data)
        self.dict_groups_name_changed()

    def _set_dict_groups_name_data(self, rec_no, rec):
        dict_groups_name_rec = [
            strings.xstr(rec['DictGroupsKey']),
            strings.xstr(rec['DictGroupsName']),
        ]

        for column in range(0, self.ui.tableWidget_dict_groups_name.columnCount()):
            self.ui.tableWidget_dict_groups_name.setItem(rec_no, column, QtWidgets.QTableWidgetItem(dict_groups_name_rec[column]))

    def dict_groups_name_changed(self):
        dict_groups_name = self.table_widget_dict_groups_name.field_value(1)
        self.ui.groupBox_dict_symptom.setTitle('主訴資料 - [' + strings.xstr(dict_groups_name) + ']')
        self._read_dict_symptom(dict_groups_name)

    def _read_dict_symptom(self, dict_groups_name):
        sql = '''
            SELECT * FROM clinic WHERE ClinicType = "主訴" and Groups = "{0}" ORDER BY ClinicCode, ClinicName
        '''.format(dict_groups_name)
        self.table_widget_dict_symptom.set_db_data(sql, self._set_dict_symptom_data)

    def _set_dict_symptom_data(self, rec_no, rec):
        dict_symptom_rec = [
            strings.xstr(rec['ClinicKey']),
            strings.xstr(rec['ClinicCode']),
            strings.xstr(rec['InputCode']),
            strings.xstr(rec['ClinicName']),
        ]

        for column in range(0, self.ui.tableWidget_dict_symptom.columnCount()):
            self.ui.tableWidget_dict_symptom.setItem(rec_no, column, QtWidgets.QTableWidgetItem(dict_symptom_rec[column]))

    # 新增主訴類別
    def _add_dict_groups(self):
        input_dialog = dialog_utils.get_dialog(
            '主訴類別', '請輸入主訴類別', None, QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_groups = input_dialog.textValue()
        field = ['DictGroupsType', 'DictGroupsName']
        data = ('主訴類別', dict_groups, )
        self.database.insert_record('dict_groups', field, data)
        self._read_dict_groups()

    # 移除主訴類別
    def _remove_dict_groups(self):
        msg_box = dialog_utils.get_message_box(
            '刪除主訴類別資料', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除 [{0}] 主訴類別?</b></font>'.format(self.table_widget_dict_groups.field_value(1)),
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
            '主訴類別', '請輸入主訴類別',
            old_groups,
            QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_groups_name = input_dialog.textValue()
        data = (dict_groups_name,)

        sql = '''
            UPDATE dict_groups set DictGroupsTopLevel = "{0}" WHERE 
            DictGroupsType = "主訴" and DictGroupsTopLevel = "{1}"
        '''.format(dict_groups_name, old_groups)
        self.database.exec_sql(sql)

        fields = ['DictGroupsName']
        self.database.update_record('dict_groups', fields, 'DictGroupsKey',
                                    self.table_widget_dict_groups.field_value(0), data)
        self.ui.tableWidget_dict_groups.item(self.ui.tableWidget_dict_groups.currentRow(), 1).setText(dict_groups_name)

    # 新增主訴類別
    def _add_groups_name(self):
        dict_groups = self.table_widget_dict_groups.field_value(1)
        input_dialog = dialog_utils.get_dialog(
            '主訴分類', '請輸入主訴分類名稱', None, QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        groups_name = input_dialog.textValue()
        field = ['DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName']
        data = ('主訴', dict_groups, groups_name)
        self.database.insert_record('dict_groups', field, data)
        self._read_dict_groups_name(dict_groups)

    # 移除主訴類別
    def _remove_groups_name(self):
        msg_box = dialog_utils.get_message_box(
            '刪除主訴分類資料', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除 [{0}] 主訴分類?</b></font>'.format(self.table_widget_dict_groups_name.field_value(1)),
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
            '主訴分類', '請輸入主訴分類',
            old_groups_name,
            QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_groups_name = input_dialog.textValue()
        data = (dict_groups_name,)

        sql = '''
            UPDATE clinic set Groups = "{0}" WHERE 
            ClinicType = "主訴" and Groups = "{1}"
        '''.format(dict_groups_name, old_groups_name)
        self.database.exec_sql(sql)

        fields = ['DictGroupsName']
        self.database.update_record('dict_groups', fields, 'DictGroupsKey',
                                    self.table_widget_dict_groups_name.field_value(0), data)
        self.ui.tableWidget_dict_groups_name.item(
            self.ui.tableWidget_dict_groups_name.currentRow(), 1).setText(dict_groups_name)

    # 新增主訴
    def _add_symptom(self):
        dialog = dialog_input_diagnostic.DialogInputDiagnostic(self, self.database, self.system_settings)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_dict_symptom.rowCount()
            self.ui.tableWidget_dict_symptom.insertRow(current_row)
            dict_groups_name = self.table_widget_dict_groups_name.field_value(1)
            fields = ['ClinicType', 'ClinicCode', 'InputCode', 'ClinicName', 'Groups']
            data = (
                '主訴',
                dialog.ui.lineEdit_diagnostic_code.text(),
                dialog.ui.lineEdit_input_code.text(),
                dialog.ui.lineEdit_diagnostic_name.text(),
                dict_groups_name,
            )
            self.database.insert_record('clinic', fields, data)
            self._read_dict_symptom(dict_groups_name)

        dialog.close_all()

    # 移除主訴
    def _remove_symptom(self):
        msg_box = dialog_utils.get_message_box(
            '刪除主訴資料', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除主訴: "{0}"?</b></font>'.format(self.table_widget_dict_symptom.field_value(3)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_symptom.field_value(0)
        self.database.delete_record('clinic', 'ClinicKey', key)
        self.ui.tableWidget_dict_symptom.removeRow(self.ui.tableWidget_dict_symptom.currentRow())

    # 更改主訴
    def _edit_symptom(self):
        key = self.table_widget_dict_symptom.field_value(0)
        dialog = dialog_input_diagnostic.DialogInputDiagnostic(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM clinic WHERE ClinicKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_dict_symptom_data(self.ui.tableWidget_dict_symptom.currentRow(), row_data)

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
    widget = DictSymptom()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()