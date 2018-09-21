#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QPushButton
from libs import ui_utils
from libs import string_utils
from libs import dialog_utils
from classes import table_widget
from dialog import dialog_input_drug


# 收費設定 2018.04.14
class DictTreat(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictTreat, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.dict_type = '處置'

        self._set_ui()
        self._set_signal()
        self._read_treat()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_TREAT, self)
        self.table_widget_dict_groups = table_widget.TableWidget(self.ui.tableWidget_dict_groups, self.database)
        self.table_widget_dict_groups.set_column_hidden([0])
        self.table_widget_dict_treat = table_widget.TableWidget(self.ui.tableWidget_dict_treat, self.database)
        self.table_widget_dict_treat.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_groups.itemSelectionChanged.connect(self.dict_groups_changed)
        self.ui.toolButton_add_dict_groups.clicked.connect(self._add_dict_groups)
        self.ui.toolButton_remove_dict_groups.clicked.connect(self._remove_dict_groups)
        self.ui.toolButton_edit_dict_groups.clicked.connect(self._edit_dict_groups)
        self.ui.tableWidget_dict_groups.doubleClicked.connect(self._edit_dict_groups)
        self.ui.toolButton_add_treat.clicked.connect(self._add_treat)
        self.ui.toolButton_remove_treat.clicked.connect(self._remove_treat)
        self.ui.toolButton_edit_treat.clicked.connect(self._edit_treat)
        self.ui.tableWidget_dict_treat.doubleClicked.connect(self._edit_treat)
        self.ui.tableWidget_dict_treat.itemSelectionChanged.connect(self.dict_treat_changed)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_groups_width = [100, 180]
        dict_treat_width = [100, 180, 100, 300, 100, 50, 120, 150, 120]
        self.table_widget_dict_groups.set_table_heading_width(dict_groups_width)
        self.table_widget_dict_treat.set_table_heading_width(dict_treat_width)

    def _read_treat(self):
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
        self._read_dict_treat(dict_groups_type)
        self.ui.tableWidget_dict_groups.setFocus(True)

    def _read_dict_treat(self, dict_groups_type):
        sql = '''
            SELECT * FROM medicine WHERE MedicineType = "{0}" ORDER BY MedicineCode, MedicineName
        '''.format(dict_groups_type)
        self.table_widget_dict_treat.set_db_data(sql, self._set_dict_treat_data)
        medicine_key = self.table_widget_dict_treat.field_value(0)
        self._read_treat_description(medicine_key)

    def _set_dict_treat_data(self, rec_no, rec):
        dict_treat_rec = [
            string_utils.xstr(rec['MedicineKey']),
            string_utils.xstr(rec['MedicineCode']),
            string_utils.xstr(rec['InputCode']),
            string_utils.xstr(rec['MedicineName']),
            string_utils.xstr(rec['InsCode']),
            string_utils.xstr(rec['Unit']),
            string_utils.xstr(rec['MedicineMode']),
            string_utils.xstr(rec['MedicineAlias']),
            string_utils.xstr(rec['SalePrice']),
        ]

        for column in range(len(dict_treat_rec)):
            self.ui.tableWidget_dict_treat.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_treat_rec[column])
            )
            if column in [8]:
                self.ui.tableWidget_dict_treat.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5]:
                self.ui.tableWidget_dict_treat.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
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

    # 新增主訴
    def _add_treat(self):
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_dict_treat.rowCount()
            self.ui.tableWidget_dict_treat.insertRow(current_row)
            dict_groups_type = self.table_widget_dict_groups.field_value(1)
            fields = [
                'MedicineType', 'MedicineCode', 'InputCode', 'MedicineName', 'Unit', 'MedicineMode', 'InsCode',
                'Dosage', 'MedicineAlias', 'Location', 'InPrice', 'SalePrice', 'Quantity', 'SafeQuantity',
                'Description',
            ]
            data = [
                dict_groups_type,
                dialog.ui.lineEdit_medicine_code.text(),
                dialog.ui.lineEdit_input_code.text(),
                dialog.ui.lineEdit_medicine_name.text(),
                dialog.ui.comboBox_unit.currentText(),
                dialog.ui.comboBox_medicine_mode.currentText(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.lineEdit_dosage.text(),
                dialog.ui.lineEdit_medicine_alias.text(),
                dialog.ui.lineEdit_location.text(),
                dialog.ui.lineEdit_in_price.text(),
                dialog.ui.lineEdit_sale_price.text(),
                dialog.ui.lineEdit_quantity.text(),
                dialog.ui.lineEdit_safe_quantity.text(),
                dialog.ui.textEdit_description.toPlainText(),
            ]
            string_utils.str_to_none(data)
            self.database.insert_record('medicine', fields, data)
            self._read_dict_treat(dict_groups_type)

        dialog.close_all()
        dialog.deleteLater()

    # 移除主訴
    def _remove_treat(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}: "{1}"?</b></font>'.format(
                self.dict_type, self.table_widget_dict_treat.field_value(3)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_treat.field_value(0)
        self.database.delete_record('medicine', 'MedicineKey', key)
        self.ui.tableWidget_dict_treat.removeRow(self.ui.tableWidget_dict_treat.currentRow())

    # 更改主訴
    def _edit_treat(self):
        key = self.table_widget_dict_treat.field_value(0)
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

        sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_dict_treat_data(self.ui.tableWidget_dict_treat.currentRow(), row_data)
        self.dict_treat_changed()

    def dict_treat_changed(self):
        medicine_key = self.table_widget_dict_treat.field_value(0)
        self._read_treat_description(medicine_key)

    def _read_treat_description(self, medicine_key):
        self.ui.textEdit_description.setText('')

        sql = '''
            SELECT * FROM medicine WHERE MedicineKey = "{0}"
        '''.format(medicine_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        try:
            self.ui.textEdit_description.setText(string_utils.get_str(rows[0]['Description'], 'utf8'))
        except TypeError:
            pass

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()
