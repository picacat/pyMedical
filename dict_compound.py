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
class DictCompound(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictCompound, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.dict_type = '成方'

        self._set_ui()
        self._set_signal()
        self._read_medicine()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_COMPOUND, self)
        self.table_widget_dict_compound = table_widget.TableWidget(self.ui.tableWidget_dict_compound, self.database)
        self.table_widget_dict_compound.set_column_hidden([0])
        self.table_widget_dict_medicine = table_widget.TableWidget(self.ui.tableWidget_dict_medicine, self.database)
        self.table_widget_dict_medicine.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_compound.itemSelectionChanged.connect(self.dict_compound_changed)
        # self.ui.toolButton_add_dict_compound.clicked.connect(self._add_dict_compound)
        # self.ui.toolButton_remove_dict_compound.clicked.connect(self._remove_dict_compound)
        # self.ui.toolButton_edit_dict_compound.clicked.connect(self._edit_dict_compound)
        # self.ui.tableWidget_dict_compound.doubleClicked.connect(self._edit_dict_compound)
        # self.ui.toolButton_add_medicine.clicked.connect(self._add_medicine)
        # self.ui.toolButton_remove_medicine.clicked.connect(self._remove_medicine)
        # self.ui.toolButton_edit_medicine.clicked.connect(self._edit_medicine)
        # self.ui.tableWidget_dict_medicine.doubleClicked.connect(self._edit_medicine)
        # self.ui.tableWidget_dict_medicine.itemSelectionChanged.connect(self.dict_medicine_changed)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_compound_width = [100, 180, 100, 300, 50, 100]
        dict_medicine_width = [100, 120, 250, 120, 50, 100, 120]
        self.table_widget_dict_compound.set_table_heading_width(dict_compound_width)
        self.table_widget_dict_medicine.set_table_heading_width(dict_medicine_width)

    def _read_medicine(self):
        self._read_dict_compound()

    def _read_dict_compound(self):
        sql = 'SELECT * FROM medicine WHERE MedicineType = "{0}" ORDER BY MedicineKey'.format(self.dict_type)
        self.table_widget_dict_compound.set_db_data(sql, self._set_dict_compound_data)

    def _set_dict_compound_data(self, rec_no, rec):
        dict_compound_rec = [
            string_utils.xstr(rec['MedicineKey']),
            string_utils.xstr(rec['MedicineCode']),
            string_utils.xstr(rec['InputCode']),
            string_utils.xstr(rec['MedicineName']),
            string_utils.xstr(rec['Unit']),
            string_utils.xstr(rec['SalePrice']),
        ]

        for column in range(len(dict_compound_rec)):
            self.ui.tableWidget_dict_compound.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_compound_rec[column])
            )

    def dict_compound_changed(self):
        compound_key = self.table_widget_dict_compound.field_value(0)
        self._read_ref_compound(compound_key)
        self.ui.tableWidget_dict_compound.setFocus(True)

    def _read_ref_compound(self, compound_key):
        sql = '''
            SELECT * FROM refcompound WHERE CompoundKey = {0} ORDER BY RefCompoundKey
        '''.format(compound_key)
        self.table_widget_dict_medicine.set_db_data(sql, self._set_dict_medicine_data)

    def _set_dict_medicine_data(self, rec_no, rec):
        if rec['MedicineKey'] is None:
            return

        sql = '''
            SELECT * FROM medicine WHERE MedicineKey = {0}
        '''.format(rec['MedicineKey'])
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]

        dict_medicine_rec = [
            string_utils.xstr(rec['MedicineKey']),
            string_utils.xstr(row['MedicineCode']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['Unit']),
            string_utils.xstr(rec['Quantity']),
            string_utils.xstr(row['SalePrice']),
        ]

        for column in range(len(dict_medicine_rec)):
            self.ui.tableWidget_dict_medicine.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_medicine_rec[column])
            )
            if column in [4, 5]:
                self.ui.tableWidget_dict_medicine.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [3]:
                self.ui.tableWidget_dict_medicine.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

"""
    # 新增主訴類別
    def _add_dict_compound(self):
        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入{0}類別'.format(self.dict_type),
            None, QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_compound = input_dialog.textValue()
        field = ['DictGroupsType', 'DictGroupsName']
        data = [
            '{0}類別'.format(self.dict_type), dict_compound,
        ]
        self.database.insert_record('dict_compound', field, data)
        self._read_dict_compound()

    # 移除主訴類別
    def _remove_dict_compound(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}類別資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除 [{0}] {1}類別?</b></font>'.format(
                self.table_widget_dict_compound.field_value(1), self.dict_type),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_compound.field_value(0)
        self.database.delete_record('dict_compound', 'DictGroupsKey', key)
        self.ui.tableWidget_dict_compound.removeRow(self.ui.tableWidget_dict_compound.currentRow())

    # 更改主訴類別
    def _edit_dict_compound(self):
        old_compound = self.table_widget_dict_compound.field_value(1)
        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入{0}類別'.format(self.dict_type),
            old_compound,
            QInputDialog.TextInput, 320, 200)
        ok = input_dialog.exec_()
        if not ok:
            return

        dict_compound_name = input_dialog.textValue()
        data = [
            dict_compound_name,
        ]

        sql = '''
            UPDATE dict_compound set DictGroupsTopLevel = "{0}" WHERE 
            DictGroupsType = "{1}" and DictGroupsTopLevel = "{2}"
        '''.format(dict_compound_name, self.dict_type, old_compound)
        self.database.exec_sql(sql)

        fields = ['DictGroupsName']
        self.database.update_record('dict_compound', fields, 'DictGroupsKey',
                                    self.table_widget_dict_compound.field_value(0), data)
        self.ui.tableWidget_dict_compound.item(self.ui.tableWidget_dict_compound.currentRow(), 1).setText(dict_compound_name)

    # 新增主訴
    def _add_medicine(self):
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings)
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_dict_medicine.rowCount()
            self.ui.tableWidget_dict_medicine.insertRow(current_row)
            dict_compound_type = self.table_widget_dict_compound.field_value(1)
            fields = [
                'MedicineType', 'MedicineCode', 'InputCode', 'MedicineName', 'Unit', 'MedicineMode', 'InsCode',
                'Dosage', 'MedicineAlias', 'Location', 'InPrice', 'SalePrice', 'Quantity', 'SafeQuantity',
                'Description',
            ]
            data = [
                dict_compound_type,
                dialog.ui.lineEdit_medicine_code.text(),
                dialog.ui.lineEdit_input_code.text(),
                dialog.ui.lineEdit_medicine_name.text(),
                dialog.ui.comboBox_unit.currentText(),
                dialog.ui.comboBox_medicine_mode.currentText(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.lineEdit_medicine_alias.text(),
                dialog.ui.lineEdit_sale_price.text(),
                dialog.ui.textEdit_description.toPlainText(),
            ]
            strings.str_to_none(data)
            self.database.insert_record('medicine', fields, data)
            self._read_ref_compound(dict_compound_type)

        dialog.close_all()
        dialog.deleteLater()

    # 移除主訴
    def _remove_medicine(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}: "{1}"?</b></font>'.format(
                self.dict_type, self.table_widget_dict_medicine.field_value(3)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_medicine.field_value(0)
        self.database.delete_record('medicine', 'MedicineKey', key)
        self.ui.tableWidget_dict_medicine.removeRow(self.ui.tableWidget_dict_medicine.currentRow())

    # 更改主訴
    def _edit_medicine(self):
        key = self.table_widget_dict_medicine.field_value(0)
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()
        
        sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_dict_medicine_data(self.ui.tableWidget_dict_medicine.currentRow(), row_data)
        self.dict_medicine_changed()

    def dict_medicine_changed(self):
        medicine_key = self.table_widget_dict_medicine.field_value(0)
        self._read_medicine_description(medicine_key)

    def _read_medicine_description(self, medicine_key):
        self.ui.textEdit_description.setText('')

        sql = '''
            SELECT * FROM medicine WHERE MedicineKey = "{0}"
        '''.format(medicine_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        try:
            self.ui.textEdit_description.setText(strings.get_str(rows[0]['Description'], 'utf8'))
        except TypeError:
            pass
"""

