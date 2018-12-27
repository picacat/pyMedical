#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QInputDialog, QMessageBox, QPushButton

from classes import table_widget
from dialog import dialog_input_drug
from dialog import dialog_medicine

from libs import ui_utils
from libs import string_utils
from libs import dialog_utils
from libs import system_utils


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
        self.table_widget_dict_medicine.set_column_hidden([0, 1])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_compound.itemSelectionChanged.connect(self.dict_compound_changed)

        self.ui.toolButton_add_dict_compound.clicked.connect(self._add_dict_compound)
        self.ui.toolButton_remove_dict_compound.clicked.connect(self._remove_dict_compound)
        self.ui.toolButton_edit_dict_compound.clicked.connect(self._edit_dict_compound)
        self.ui.tableWidget_dict_compound.doubleClicked.connect(self._edit_dict_compound)

        self.ui.toolButton_add_dict_medicine.clicked.connect(self._add_dict_medicine)
        self.ui.toolButton_remove_dict_medicine.clicked.connect(self._remove_dict_medicine)
        self.ui.toolButton_save_dosage.clicked.connect(self._save_dosage)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_compound_width = [100, 180, 100, 300, 50, 100]
        dict_medicine_width = [100, 100, 120, 60, 250, 120, 50, 60, 80]
        self.table_widget_dict_compound.set_table_heading_width(dict_compound_width)
        self.table_widget_dict_medicine.set_table_heading_width(dict_medicine_width)

    def _read_medicine(self):
        self._read_dict_compound()

    def _read_dict_compound(self):
        sql = '''
            SELECT * FROM medicine 
            WHERE 
                MedicineType = "{0}" 
            ORDER BY LENGTH(MedicineName), CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''.format(self.dict_type)
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
            SELECT * FROM refcompound 
            WHERE 
                CompoundKey = {0} AND
                MedicineKey IS NOT NULL
            ORDER BY RefCompoundKey
        '''.format(compound_key)
        self.table_widget_dict_medicine.set_db_data(sql, self._set_dict_medicine_data)

    def _set_dict_medicine_data(self, row_no, row):
        if row['MedicineKey'] is None:
            return

        sql = '''
            SELECT * FROM medicine WHERE MedicineKey = {0}
        '''.format(row['MedicineKey'])
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            medicine_row = {
                'RefCompoundKey': None,
                'MedicineKey': None,
                'MedicineCode': None,
                'MedicineType': None,
                'MedicineName': None,
                'InsCode': None,
                'Unit': None,
                'Quantity': None,
                'SalePrice': None,
            }
        else:
            medicine_row = rows[0]

        dict_medicine_row = [
            string_utils.xstr(row['RefCompoundKey']),
            string_utils.xstr(medicine_row['MedicineKey']),
            string_utils.xstr(medicine_row['MedicineCode']),
            string_utils.xstr(medicine_row['MedicineType']),
            string_utils.xstr(medicine_row['MedicineName']),
            string_utils.xstr(medicine_row['InsCode']),
            string_utils.xstr(medicine_row['Unit']),
            string_utils.xstr(row['Quantity']),
            string_utils.xstr(medicine_row['SalePrice']),
        ]

        for column in range(len(dict_medicine_row)):
            self.ui.tableWidget_dict_medicine.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(dict_medicine_row[column])
            )
            if column in [7, 8]:
                self.ui.tableWidget_dict_medicine.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [6]:
                self.ui.tableWidget_dict_medicine.item(row_no, column).setTextAlignment(
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

    # 新增成方
    def _add_dict_compound(self):
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings)

        if dialog.exec_():
            current_row = self.ui.tableWidget_dict_compound.rowCount()
            self.ui.tableWidget_dict_compound.insertRow(current_row)

            fields = [
                'MedicineType', 'MedicineCode', 'InputCode', 'MedicineName', 'Unit', 'MedicineMode', 'InsCode',
                'Dosage', 'MedicineAlias', 'Location', 'InPrice', 'SalePrice', 'Quantity', 'SafeQuantity',
                'Description',
            ]
            data = [
                '成方',
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
            self._read_dict_compound()

        dialog.close_all()
        dialog.deleteLater()

    # 移除成方
    def _remove_dict_compound(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}: "{1}"?</b></font>'.format(
                self.dict_type, self.table_widget_dict_compound.field_value(3)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_compound.field_value(0)
        self.database.delete_record('refcompound', 'CompoundKey', key)
        self.database.delete_record('medicine', 'MedicineKey', key)

        self.ui.tableWidget_dict_compound.removeRow(self.ui.tableWidget_dict_compound.currentRow())

    # 更改成方
    def _edit_dict_compound(self):
        key = self.table_widget_dict_compound.field_value(0)
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

        # 重新顯示資料
        sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_dict_compound_data(self.ui.tableWidget_dict_compound.currentRow(), row_data)

    # 移除成方內容
    def _remove_dict_medicine(self):
        msg_box = dialog_utils.get_message_box(
            '移除成方內容', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定移除{0}內容: "{1}"?</b></font>'.format(
                self.dict_type, self.table_widget_dict_medicine.field_value(4)),
            '注意！資料移除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_medicine.field_value(0)
        self.database.delete_record('refcompound', 'RefCompoundKey', key)
        self.ui.tableWidget_dict_medicine.removeRow(self.ui.tableWidget_dict_medicine.currentRow())

    # 新增主訴
    def _add_dict_medicine(self):
        dialog = dialog_medicine.DialogMedicine(
            self, self.database, self.system_settings,
            self.ui.tableWidget_dict_medicine, None,
            '成方',
        )
        dialog.exec_()
        dialog.deleteLater()

    def add_ref_compound(self, row):
        compound_key = self.table_widget_dict_compound.field_value(0)

        fields = ['CompoundKey', 'MedicineKey']
        data = [
            compound_key,
            row['MedicineKey'],
        ]

        self.database.insert_record('refcompound', fields, data)
        self._read_ref_compound(compound_key)

    def _save_dosage(self):
        for row_no in range(self.ui.tableWidget_dict_medicine.rowCount()):
            dosage = self.ui.tableWidget_dict_medicine.item(row_no, 7)

            data = 'NULL'
            if dosage is not None:
                data = dosage.text()
            if data == '':
                data = 'NULL'

            self.ui.tableWidget_dict_medicine.setCurrentCell(row_no, 0)
            sql = '''
                UPDATE refcompound SET Quantity = {0} WHERE RefCompoundKey = {1}
            '''.format(data, self.table_widget_dict_medicine.field_value(0))
            self.database.exec_sql(sql)

        system_utils.show_message_box(
            QMessageBox.Information,
            '存檔完畢',
            '<h3>劑量已全部存檔完成</h3>',
            '資料正確.'
        )
