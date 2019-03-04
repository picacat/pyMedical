#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from classes import table_widget
from dialog import dialog_input_medicine
from dialog import dialog_rich_text

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
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self._set_table_width()
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self.append_null_medicine)
        self.ui.toolButton_remove_medicine.clicked.connect(self.remove_medicine)
        self.ui.toolButton_dictionary.clicked.connect(self._open_dictionary)
        self.ui.toolButton_show_costs.clicked.connect(self._show_costs)
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
            if self.ui.tableWidget_prescript.item(
                    current_row, prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']) is None:
                self.ui.tableWidget_prescript.removeRow(current_row)
                return
            if self.ui.tableWidget_prescript.currentColumn() in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
        elif key == QtCore.Qt.Key_Down:
            if (current_row == self.ui.tableWidget_prescript.rowCount() - 1 and
                    self.ui.tableWidget_prescript.item(
                        current_row, prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']) is not None):
                self.append_null_medicine()
            if self.ui.tableWidget_prescript.currentColumn() in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if self.ui.tableWidget_prescript.currentColumn() == prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']:
                self.open_medicine_dialog()
            elif self.ui.tableWidget_prescript.currentColumn() in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
                if current_row < self.ui.tableWidget_prescript.rowCount() - 1:
                    self.ui.tableWidget_prescript.setCurrentCell(
                        self.ui.tableWidget_prescript.currentRow()+1, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']
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
        self.ui.tableWidget_prescript.setCurrentCell(
            self.ui.tableWidget_prescript.currentRow(), prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
        self.ui.tableWidget_prescript.setCurrentCell(
            self.ui.tableWidget_prescript.currentRow(), prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName'])
        item = self.ui.tableWidget_prescript.item(
            self.ui.tableWidget_prescript.currentRow(), prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName'])

        if item is None or item.text() == '':
            return

        previous_medicine_name = self.table_widget_prescript.field_value(
            prescript_utils.SELF_PRESCRIPT_COL_NO['BackupMedicineName']
        )

        if item.text() == previous_medicine_name:
            return

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
        '''.format(item.text())
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            item.setText(previous_medicine_name)
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
                previous_medicine_name,
            )
            dialog.exec_()
            dialog.deleteLater()

    def append_prescript(self, row, dosage=None):
        medicine_key = string_utils.xstr(row['MedicineKey'])
        medicine_type = string_utils.xstr(row['MedicineType'])
        if prescript_utils.check_prescript_duplicates(
                self.ui.tableWidget_prescript,
                medicine_type,
                prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey'], medicine_key):
            return

        try:
            price = string_utils.get_formatted_str('單價', row['Price'])
            amount = string_utils.get_formatted_str('單價', row['Amount'])
        except Exception:
            price = string_utils.get_formatted_str('單價', row['SalePrice'])
            amount = string_utils.get_formatted_str('單價', None)


        prescript_row = [
            [prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey'], '-1'],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptNo'],
             string_utils.xstr(self.ui.tableWidget_prescript.currentRow() + 1)],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['CaseKey'], string_utils.xstr(self.case_key)],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['CaseDate'], string_utils.xstr(self.case_date)],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineSet'], string_utils.xstr(self.medicine_set)],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineType'], string_utils.xstr(row['MedicineType'])],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey'], medicine_key],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['InsCode'], string_utils.xstr(row['InsCode'])],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['DosageMode'], self.system_settings.field('劑量模式')],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['BackupMedicineName'], string_utils.xstr(row['MedicineName'])],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName'], string_utils.xstr(row['MedicineName'])],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'], string_utils.xstr(dosage)],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['Unit'], string_utils.xstr(row['Unit'])],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['Instruction'], None],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['Price'], price],
            [prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'], amount],
        ]

        self.set_prescript(prescript_row)

    def set_prescript(self, row):
        row_no = self.ui.tableWidget_prescript.currentRow()
        for item in row:
            self.ui.tableWidget_prescript.setItem(
                row_no, item[0], QtWidgets.QTableWidgetItem(item[1])
            )

            if item[0] in [prescript_utils.SELF_PRESCRIPT_COL_NO['Unit']]:
                self.ui.tableWidget_prescript.item(row_no, item[0]).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            elif item[0] in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Info'],
            ]:
                item = self.ui.tableWidget_prescript.item(row_no, item[0])
                if item is not None:
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                    item.setFlags(QtCore.Qt.ItemIsEnabled)

        medicine_key = row[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']][1]
        description = prescript_utils.get_medicine_description(self.database, medicine_key)
        self._add_prescript_info_button(row_no, description)

    def _set_table_width(self):
        medicine_width = [
            70,
            100, 100, 100, 100, 100, 100, 100, 100, 100,
            220, 60, 50, 60, 80, 80, 20
        ]
        self.table_widget_prescript.set_table_heading_width(medicine_width)

    def _read_prescript(self):
        self._read_dosage()
        self._read_medicine()
        self._calculate_total_dosage()
        self._calculate_total_costs()

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
        medicine_key = row['MedicineKey']
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
            string_utils.xstr(medicine_key),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['DosageMode']),
            string_utils.xstr(row['MedicineName']),
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
            if col_no in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                align = QtCore.Qt.AlignRight
            elif col_no in [prescript_utils.SELF_PRESCRIPT_COL_NO['Unit']]:
                align = QtCore.Qt.AlignCenter

            self.ui.tableWidget_prescript.item(
                row_no, col_no).setTextAlignment(align | QtCore.Qt.AlignVCenter)

            if col_no in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Info']
            ]:
                item = self.ui.tableWidget_prescript.item(row_no, col_no)
                if item is not None:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)

        description = prescript_utils.get_medicine_description(self.database, medicine_key)
        self._add_prescript_info_button(row_no, description)

    def _add_prescript_info_button(self, row_no, description):
        button = QtWidgets.QPushButton(self.ui.tableWidget_prescript)
        button.setIcon(QtGui.QIcon('./icons/gtk-info.svg'))
        button.setFlat(True)
        if description is None:
            button.setEnabled(False)

        button.clicked.connect(lambda : self._show_medicine_description(description))
        self.ui.tableWidget_prescript.setCellWidget(
            row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Info'], button)

    def _show_medicine_description(self, description):
        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'rich_text', description
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

    # 增加處方資料
    def append_null_medicine(self):
        row_count = self.table_widget_prescript.row_count()
        if row_count <= 0:
            self._insert_medicine_row(row_count)
            return

        item = self.ui.tableWidget_prescript.item(row_count-1, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName'])
        if item is None or item.text().strip() == '':
            return

        self._insert_medicine_row(row_count)

    def _insert_medicine_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(index, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName'])

        self.ui.tableWidget_prescript.setItem(
            index, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'], QtWidgets.QTableWidgetItem(''))
        self.ui.tableWidget_prescript.item(
            index, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']).setTextAlignment(
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
        self._calculate_total_costs()

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
            if items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']] is None:
                continue

            if items[prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']] == '':
                items[prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']] = None

            prescript_no += 1
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptNo']] = str(prescript_no)

            if items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']] == '-1':
                self.insert_prescript(items)
            else:
                self.update_prescript(items)

    # 刪除不在tableWidget內的處方
    def delete_not_exists_prescript(self, prescript_data_set, medicine_type):
        prescript_key_list = []
        for items in prescript_data_set:
            prescript_key_list.append(items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']])

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
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptNo']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['CaseKey']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['CaseDate']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineSet']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineType']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['InsCode']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['DosageMode']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Unit']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Instruction']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Price']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']],
        ]

        self.database.insert_record('prescript', fields, data)

    # 更新處方資料至資料庫內
    def update_prescript(self, items):
        if items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']] == '':
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']] = None

        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
            'MedicineName', 'Dosage', 'Unit', 'Instruction',
            'Price', 'Amount',
        ]
        data = [
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptNo']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['CaseKey']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['CaseDate']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineSet']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineType']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['InsCode']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['DosageMode']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Unit']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Instruction']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Price']],
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']],
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
        for row_no, row in zip(range(len(rows)), rows):
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'])

        self.ui.tableWidget_prescript.resizeRowsToContents()

    # 藥日變更重新批價
    def pres_days_changed(self):
        self.parent.calculate_self_fees()

    def _prescript_item_changed(self, item):
        if item is None:
            return

        row_no = item.row()
        col_no = item.column()
        if col_no in [prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']]:
            self._calculate_total_price(row_no, item)
            self._adjust_price_column_align(row_no)
            self.parent.calculate_self_fees()

            self ._calculate_total_dosage()
            self ._calculate_total_costs()

    def _calculate_total_price(self, row_no, item):
        sale_price = self.ui.tableWidget_prescript.item(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price'])
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
            row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
            QtWidgets.QTableWidgetItem(string_utils.get_formatted_str('單價', subtotal))
        )

    def _adjust_price_column_align(self, row_no):
        for col_no in [
            prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
            prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
            prescript_utils.SELF_PRESCRIPT_COL_NO['Info'],
        ]:
            item = self.ui.tableWidget_prescript.item(row_no, col_no)

            if item is not None:
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                item.setFlags(QtCore.Qt.ItemIsEnabled)

    def _calculate_total_dosage(self):
        total_dosage = 0.0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            item = self.ui.tableWidget_prescript.item(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
            if item is None:
                continue

            dosage = number_utils.get_float(item.text())
            total_dosage += dosage

        self.ui.label_total_dosage.setText('總量: {0}'.format(total_dosage))

    def _calculate_total_costs(self):
        total_costs = 0.0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            dosage_item = self.ui.tableWidget_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
            if dosage_item is None:
                continue

            medicine_key_item = self.ui.tableWidget_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey'])
            if medicine_key_item is None:
                continue

            medicine_key = medicine_key_item.text()
            if medicine_key == '':
                continue

            sql = 'SELECT InPrice FROM medicine WHERE MedicineKey = {0}'.format(medicine_key)
            rows = self.database.select_record(sql)
            if len(rows) <= 0:
                continue

            cost = number_utils.get_float(rows[0]['InPrice'])
            dosage = number_utils.get_float(dosage_item.text())
            total_costs += dosage * cost

        self.ui.label_total_costs.setText('成本: {0:.1f}'.format(total_costs))

    def _open_dictionary(self):
        self.parent.open_dictionary(self.medicine_set, '自費處方')

    def _show_costs(self):
        html = prescript_utils.get_costs_html(
            self.database, self.ui.tableWidget_prescript, prescript_utils.SELF_PRESCRIPT_COL_NO
        )
        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'html', html
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

