#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from classes import table_widget
from dialog import dialog_input_medicine

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import prescript_utils


# 輸入健保處方 2018.04.14
class SelfPrescriptRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(SelfPrescriptRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.medicine_set = args[3]
        self.case_date = self.parent.medical_record['CaseDate']
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_prescript()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_SELF_PRESCRIPT_RECORD, self)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7, 8])
        self._set_table_width()
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self.append_null_medicine)
        self.ui.toolButton_remove_medicine.clicked.connect(self.remove_medicine)
        self.ui.toolButton_dictionary.clicked.connect(self._open_dictionary)
        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press
        self.ui.tableWidget_prescript.itemChanged.connect(self._prescript_item_changed)
        self.ui.comboBox_pres_days.currentTextChanged.connect(self.pres_days_changed)

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_package, nhi_utils.PACKAGE, None)
        ui_utils.set_combo_box(self.ui.comboBox_pres_days, nhi_utils.SELF_PRESDAYS, None)
        ui_utils.set_combo_box(self.ui.comboBox_instruction, nhi_utils.INSTRUCTION, None)

    def _table_widget_prescript_key_press(self, event):
        key = event.key()
        current_row = self.ui.tableWidget_prescript.currentRow()

        if key == QtCore.Qt.Key_Delete:
            self.remove_medicine()
        elif key == QtCore.Qt.Key_Up:
            if self.ui.tableWidget_prescript.item(current_row, 0) is None:
                self.ui.tableWidget_prescript.removeRow(current_row)
                return
            if self.ui.tableWidget_prescript.currentColumn() in [10, 13, 14]:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
        elif key == QtCore.Qt.Key_Down:
            if (current_row == self.ui.tableWidget_prescript.rowCount() - 1 and
                    self.ui.tableWidget_prescript.item(current_row, 0) is not None):
                self.append_null_medicine()
            if self.ui.tableWidget_prescript.currentColumn() in [10, 13, 14]:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if self.ui.tableWidget_prescript.currentColumn() == 9:
                self.open_medicine_dialog()
            elif self.ui.tableWidget_prescript.currentColumn() in [10, 13, 14]:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
                if current_row < self.ui.tableWidget_prescript.rowCount() - 1:
                    self.ui.tableWidget_prescript.setCurrentCell(
                        self.ui.tableWidget_prescript.currentRow()+1, 10
                    )

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_prescript, event)

    def _set_dosage_format(self, row_no, col_no):
        if self.system_settings.field('劑量模式') in ['日劑量', '總量']:
            dosage_format = '.1f'
        else:
            dosage_format = '.2f'

        self.table_widget_prescript.set_cell_text_format(
            row_no, col_no, dosage_format, 'float',
        )

    def open_medicine_dialog(self):
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 10)
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 9)
        item = self.ui.tableWidget_prescript.item(self.ui.tableWidget_prescript.currentRow(), 9)
        if item is None or item.text() == '':
            return

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
        '''.format(item.text())
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            if self.table_widget_prescript.field_value(0) is None:
                item.setText(None)
            else:
                item.setText(item.text())
        elif len(rows) == 1:
            self.append_prescript(rows[0])
            self.append_null_medicine()
        else:
            dialog = dialog_input_medicine.DialogInputMedicine(
                self, self.database,
                self.system_settings,
                None,
                self.medicine_set,
                self.ui.tableWidget_prescript,
            )
            dialog.exec_()
            dialog.deleteLater()

    def append_prescript(self, row, dosage=None):
        medicine_key = string_utils.xstr(row['MedicineKey'])
        if prescript_utils.check_prescript_duplicates(
                self.ui.tableWidget_prescript, 6, medicine_key):
            return

        price = string_utils.get_formatted_str('單價', row['Price'])
        amount = string_utils.get_formatted_str('單價', row['Amount'])

        prescript_row = [
            [0, '-1'],
            [1, string_utils.xstr(self.ui.tableWidget_prescript.currentRow() + 1)],
            [2, string_utils.xstr(self.case_key)],
            [3, string_utils.xstr(self.case_date)],
            [4, string_utils.xstr(self.medicine_set)],
            [5, string_utils.xstr(row['MedicineType'])],
            [6, medicine_key],
            [7, string_utils.xstr(row['InsCode'])],
            [8, self.system_settings.field('劑量模式')],
            [9, string_utils.xstr(row['MedicineName'])],
            [10, string_utils.xstr(dosage)],
            [11, string_utils.xstr(row['Unit'])],
            [12, None],
            [13, price],
            [14, amount],
        ]

        self.set_prescript(prescript_row)

    def set_prescript(self, row):
        row_no = self.ui.tableWidget_prescript.currentRow()
        for item in row:
            self.ui.tableWidget_prescript.setItem(
                row_no, item[0], QtWidgets.QTableWidgetItem(item[1])
            )

            if item[0] in [11]:
                self.ui.tableWidget_prescript.item(row_no, item[0]).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            elif item[0] in [13, 14]:
                item = self.ui.tableWidget_prescript.item(row_no, item[0])
                if item is not None:
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    item.setFlags(QtCore.Qt.ItemIsEnabled)

    def _set_table_width(self):
        medicine_width = [
            70,
            100, 100, 100, 100, 100, 100, 100, 100,
            240, 60, 50, 60, 70, 70
        ]
        self.table_widget_prescript.set_table_heading_width(medicine_width)

    def _read_prescript(self):
        self._read_dosage()
        self._read_medicine()
        self._calculate_total_dosage()

        if self.parent.call_from == '醫師看診作業':
            self.append_null_medicine()

    def _read_dosage(self):
        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = {1} 
        '''.format(self.case_key, self.medicine_set)
        row = self.database.select_record(sql)
        if len(row) <= 0:
            return

        self.ui.comboBox_package.setCurrentText(string_utils.xstr(row[0]['Packages']))
        self.ui.comboBox_pres_days.setCurrentText(string_utils.xstr(row[0]['Days']))
        self.ui.comboBox_instruction.setCurrentText(string_utils.xstr(row[0]['Instruction']))

    def _read_medicine(self):
        sql = """ 
            SELECT * FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1})
            ORDER BY PrescriptNo, PrescriptKey
        """.format(self.case_key, self.medicine_set)
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        dosage = string_utils.get_formatted_str(self.system_settings.field('劑量形式'), row['Dosage'])
        price = string_utils.get_formatted_str('單價', row['Price'])
        amount = string_utils.get_formatted_str('單價', row['Amount'])

        prescript_row = [
            string_utils.xstr(row['PrescriptKey']),
            string_utils.xstr(row['PrescriptNo']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['MedicineSet']),
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['DosageMode']),
            string_utils.xstr(row['MedicineName']),
            dosage,
            string_utils.xstr(row['Unit']),
            string_utils.xstr(row['Instruction']),
            price,
            amount,
        ]

        for col_no in range(len(prescript_row)):
            self.ui.tableWidget_prescript.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(prescript_row[col_no])
            )

            align = QtCore.Qt.AlignLeft
            if col_no in [10, 13, 14]:
                align = QtCore.Qt.AlignRight
            elif col_no in [11]:
                align = QtCore.Qt.AlignCenter

            self.ui.tableWidget_prescript.item(
                row_no, col_no).setTextAlignment(align | QtCore.Qt.AlignVCenter)

            if col_no in [13, 14]:
                item = self.ui.tableWidget_prescript.item(row_no, col_no)
                if item is not None:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)


    # 增加處方資料
    def append_null_medicine(self):
        row_count = self.table_widget_prescript.row_count()
        if row_count <= 0:
            self._insert_medicine_row(row_count)
            return

        item = self.ui.tableWidget_prescript.item(row_count-1, 9)
        if item is None or item.text().strip() == '':
            return

        self._insert_medicine_row(row_count)

    def _insert_medicine_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(index, 9)

        self.ui.tableWidget_prescript.setItem(index, 10, QtWidgets.QTableWidgetItem(''))
        self.ui.tableWidget_prescript.item(index, 10).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    # 刪除處方
    def remove_medicine(self):
        index = self.ui.tableWidget_prescript.currentRow()
        self.ui.tableWidget_prescript.removeRow(index)
        if self.ui.tableWidget_prescript.rowCount() <= 0:
            self.ui.comboBox_package.setCurrentText(None)
            self.ui.comboBox_pres_days.setCurrentText(None)
            self.ui.comboBox_instruction.setCurrentText(None)
            self.append_null_medicine()

        self.parent.calculate_self_fees()
        self._calculate_total_dosage()

    def save_prescript(self):
        self._save_dosage()
        self._save_medicine()

    def _save_dosage(self):
        fields = ['CaseKey', 'MedicineSet', 'Packages', 'Days', 'Instruction',]
        data = [
            str(self.case_key),
            str(self.medicine_set),
            self.ui.comboBox_package.currentText(),
            self.ui.comboBox_pres_days.currentText(),
            self.ui.comboBox_instruction.currentText(),
        ]

        sql = '''
            SELECT * FROM dosage WHERE
            CaseKey = {0} AND MedicineSet = {1} 
        '''.format(self.case_key, self.medicine_set)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            self.database.update_record('dosage', fields, 'DosageKey', rows[0]['DosageKey'], data)
        else:
            self.database.insert_record('dosage', fields, data)

    def _save_medicine(self):
        prescript_data_set = []
        for i in range(self.ui.tableWidget_prescript.rowCount()):
            prescript_rec = []
            for j in range(self.ui.tableWidget_prescript.columnCount()):
                try:
                    prescript_rec.append(self.ui.tableWidget_prescript.item(i, j).text())
                except AttributeError:
                    prescript_rec.append(None)

            prescript_data_set.append(prescript_rec)

        self.delete_not_exists_prescript(prescript_data_set, '藥品類別')

        prescript_no = 0  # 重編 PrescriptNo
        for items in prescript_data_set:
            if items[0] is None:
                continue

            if items[10] == '':
                items[10] = None

            prescript_no += 1
            items[1] = str(prescript_no)

            if items[0] == '-1':
                self.insert_prescript(items)
            else:
                self.update_prescript(items)

    # 刪除不在tableWidget內的處方
    def delete_not_exists_prescript(self, prescript_data_set, medicine_type):
        prescript_key_list = []
        for items in prescript_data_set:
            prescript_key_list.append(items[0])

        sql = '''
            SELECT * FROM prescript WHERE 
            CaseKey = {0} AND 
            MedicineSet = {1}
        '''.format(self.case_key, self.medicine_set)

        rows = self.database.select_record(sql)
        for row in rows:
            if str(row['PrescriptKey']) not in prescript_key_list:
                self.database.exec_sql('DELETE FROM prescript where PrescriptKey = {0}'.format(row['PrescriptKey']))

    # 插入處方資料至資料庫內
    def insert_prescript(self, items):
        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
            'MedicineName', 'Dosage', 'Unit', 'Instruction',
            'Price', 'Amount',
        ]

        data = [
            items[1], items[2], items[3],
            items[4], items[5], items[6], items[7], items[8],
            items[9], items[10], items[11], items[12],
            items[13], items[14],
        ]
        self.database.insert_record('prescript', fields, data)

    # 更新處方資料至資料庫內
    def update_prescript(self, items):
        if items[6] == '':
            items[6] = None

        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
            'MedicineName', 'Dosage', 'Unit', 'Instruction',
            'Price', 'Amount',
        ]
        data = [
            items[1], items[2], items[3],
            items[4], items[5], items[6], items[7], items[8],
            items[9], items[10], items[11], items[12],
            items[13], items[14],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 拷貝過去病歷的處方
    def copy_past_prescript(self, case_key):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        sql = '''
            SELECT * FROM prescript WHERE CaseKey = {0} AND 
                MedicineSet = {1} ORDER BY PrescriptKey'''.format(case_key, self.medicine_set)
        rows = self.database.select_record(sql)
        for row in rows:
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row)

    # 藥日變更重新批價
    def pres_days_changed(self):
        self.parent.calculate_self_fees()

    def _prescript_item_changed(self, item):
        if item is None:
            return

        row_no = item.row()
        col_no = item.column()
        if col_no == 10:
            self._calculate_total_price(row_no, col_no, item)
            self._adjust_price_column_align(row_no)
            self.parent.calculate_self_fees()

            self ._calculate_total_dosage()

    def _calculate_total_price(self, row_no, col_no, item):
        sale_price = self.ui.tableWidget_prescript.item(row_no, 13)
        if sale_price is None:
            return

        dosage = item.text()
        if dosage == '':
            dosage = 0

        sale_price = sale_price.text()
        if sale_price == '':
            sale_price = 0

        subtotal = float(dosage) * float(sale_price)

        self.ui.tableWidget_prescript.setItem(
            row_no, 14,
            QtWidgets.QTableWidgetItem(string_utils.get_formatted_str('單價', subtotal))
        )

    def _adjust_price_column_align(self, row_no):
        for col_no in [13, 14]:
            item = self.ui.tableWidget_prescript.item(row_no, col_no)

            if item is not None:
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                item.setFlags(QtCore.Qt.ItemIsEnabled)

    def _calculate_total_dosage(self):
        total_dosage = 0.0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            item = self.ui.tableWidget_prescript.item(row_no, 10)
            if item is None:
                continue

            dosage = number_utils.get_float(item.text())
            total_dosage += dosage

        self.ui.label_total_dosage.setText('總量: {0}'.format(total_dosage))

    def _open_dictionary(self):
        self.parent.open_dictionary(self.medicine_set, '自費處方')
