#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from classes import table_widget
from dialog import dialog_input_medicine
from dialog import dialog_ins_care


# 輸入健保處方 2018.04.14
class InsCareRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsCareRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.medicine_set = args[3]
        self.case_date = self.parent.medical_record['CaseDate']
        self.treat_type = self.parent.tab_registration.ui.comboBox_treat_type.currentText()
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_CARE_RECORD, self)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6])
        self._set_table_width()

        if self.treat_type in ['助孕照護', '保胎照護']:
            self.ui.toolButton_add_medicine.setEnabled(False)

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self._open_ins_care_dialog)
        self.ui.toolButton_remove_medicine.clicked.connect(self._remove_medicine)
        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press

    def _table_widget_prescript_key_press(self, event):
        key = event.key()
        current_row = self.ui.tableWidget_prescript.currentRow()

        if key == QtCore.Qt.Key_Delete:
            self._remove_medicine()
        elif key == QtCore.Qt.Key_Up:
            if self.ui.tableWidget_prescript.item(current_row, 0) is None:
                self.ui.tableWidget_prescript.removeRow(current_row)
                return
        elif key == QtCore.Qt.Key_Down:
            if current_row == self.ui.tableWidget_prescript.rowCount() - 1 and \
                    self.ui.tableWidget_prescript.item(current_row, 0) is not None:
                self.append_null_medicine()
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if self.ui.tableWidget_prescript.currentColumn() == 1:
                self.open_medicine_dialog()
            elif self.ui.tableWidget_prescript.currentColumn() == 2:
                self.table_widget_prescript.set_cell_text_format(
                    current_row, self.ui.tableWidget_prescript.currentColumn(), '.2f', 'float')
                self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow()+1, 2)

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_prescript, event)

    def open_medicine_dialog(self):
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 2)
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 1)
        item = self.ui.tableWidget_prescript.item(self.ui.tableWidget_prescript.currentRow(), 1)
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
            self.append_prescript(rows[0], self.ui.tableWidget_prescript.currentRow())
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

    def _set_table_width(self):
        medicine_width = [
            70, 100, 100, 100, 100, 100, 100,
            250, 90, 60, 50, 50, 60,
        ]
        self.table_widget_prescript.set_table_heading_width(medicine_width)

    def _read_prescript(self):
        sql = """ 
            SELECT * FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1})
            ORDER BY PrescriptNo, PrescriptKey
        """.format(self.case_key, self.medicine_set)
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

        if self.ui.tableWidget_prescript.rowCount() <= 0:
            if self.treat_type == '助孕照護':
                self._add_care_row('P39002', 0)  # 預設為助孕照護無針灸
            elif self.treat_type == '保胎照護':
                self._add_care_row('P39004', 0)  # 預設為保胎照護無針灸
            elif self.treat_type == '兒童鼻炎':
                self._add_care_row('P58005', 0)  # 預設為兒童鼻炎

    def _set_medicine_data(self, row_no, row):
        dosage = number_utils.get_integer(row['Dosage'])
        price = number_utils.get_integer(row['Price'])
        amount = dosage * price

        prescript_row = [
            string_utils.xstr(row['PrescriptKey']),
            string_utils.xstr(row['PrescriptNo']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['MedicineSet']),
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(price),
            string_utils.xstr(dosage),
            string_utils.xstr(row['Unit']),
            string_utils.xstr(amount),
        ]

        for column in range(len(prescript_row)):
            self.ui.tableWidget_prescript.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(prescript_row[column])
            )
            if column in [9, 10, 12]:
                self.ui.tableWidget_prescript.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [11]:
                self.ui.tableWidget_prescript.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsCode'] == '':
                self.ui.tableWidget_prescript.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

    # 增加處方資料
    def append_null_medicine(self):
        row_count = self.ui.tableWidget_prescript.rowCount()
        if row_count <= 0:
            self._insert_medicine_row(row_count)
            return

        item = self.ui.tableWidget_prescript.item(row_count-1, 7)  # Medicine Name
        if item is None or item.text().strip() == '':
            return

        self._insert_medicine_row(row_count)

    def _insert_medicine_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(index, 7)

    # 刪除處方
    def _remove_medicine(self):
        index = self.ui.tableWidget_prescript.currentRow()
        self.ui.tableWidget_prescript.removeRow(index)
        self.parent.calculate_ins_fees()

    def save_prescript(self):
        prescript_rows = []
        for i in range(self.ui.tableWidget_prescript.rowCount()):
            prescript_item = []
            for j in range(self.ui.tableWidget_prescript.columnCount()):
                try:
                    prescript_item.append(self.ui.tableWidget_prescript.item(i, j).text())
                except AttributeError:
                    prescript_item.append(None)

            prescript_rows.append(prescript_item)

        self.delete_not_exists_prescript(prescript_rows)

        prescript_no = 0  # 重編 PrescriptNo
        for items in prescript_rows:
            if items[0] is None:
                continue

            if items[6] == '':  # MedicineKey
                items[6] = None

            prescript_no += 1
            items[1] = str(prescript_no)

            if items[0] == '-1':
                self.insert_prescript(items)
            else:
                self.update_prescript(items)

    # 刪除不在tableWidget內的處方
    def delete_not_exists_prescript(self, prescript_rows):
        prescript_key_list = []
        for items in prescript_rows:
            prescript_key_list.append(items[0])

        sql = '''
            SELECT * FROM prescript WHERE 
            CaseKey = {0} AND 
            MedicineSet = {1} AND
            MedicineType = "照護"
        '''.format(self.case_key, self.medicine_set)

        rows = self.database.select_record(sql)
        for row in rows:
            if string_utils.xstr(row['PrescriptKey']) not in prescript_key_list:
                self.database.exec_sql('DELETE FROM prescript where PrescriptKey = {0}'.format(row['PrescriptKey']))
                self.database.exec_sql('DELETE FROM presextend where PrescriptKey = {0}'.format(row['PrescriptKey']))

    # 插入處方資料至資料庫內
    def insert_prescript(self, items):
        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate', 'MedicineSet', 'MedicineType', 'MedicineKey',
            'MedicineName', 'InsCode', 'Price', 'Dosage', 'Unit', 'Amount',
        ]
        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
            items[8], items[9], items[10], items[11], items[12],
        ]

        self.database.insert_record('prescript', fields, data)

    # 更新處方資料至資料庫內
    def update_prescript(self, items):
        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate', 'MedicineSet', 'MedicineType', 'MedicineKey',
            'MedicineName', 'InsCode', 'Price', 'Dosage', 'Unit', 'Amount',
        ]
        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
            items[8], items[9], items[10], items[11], items[12],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 助孕照護
    def set_aid_pregnant_treat(self, treatment):
        if treatment == '針灸治療':
            treat_code = 'P39001'
        else:
            treat_code = 'P39002'

        if self.ui.tableWidget_prescript.rowCount() > 0:
            self.ui.tableWidget_prescript.setCurrentCell(0, 7)
            ins_code = self.ui.tableWidget_prescript.item(0, 8).text()
            if treat_code == ins_code:
                return

        self.ui.tableWidget_prescript.setRowCount(0)
        self._add_care_row(treat_code, 0)

    # 保胎照護
    def set_keep_baby_treat(self, treatment):
        if treatment == '針灸治療':
            treat_code = 'P39003'
        else:
            treat_code = 'P39004'

        if self.ui.tableWidget_prescript.rowCount() > 0:
            self.ui.tableWidget_prescript.setCurrentCell(0, 7)
            ins_code = self.ui.tableWidget_prescript.item(0, 8).text()
            if treat_code == ins_code:
                return

        self.ui.tableWidget_prescript.setRowCount(0)
        self._add_care_row(treat_code, 0)

    # 乳癌肝癌照護處置
    def set_cancer_treat(self, treatment):
        if treatment in ['針灸治療', '傷科治療']:
            treat_code = 'P56005'
        else:
            treat_code = ''

        self._remove_specific_treat_code(['P56005'])  # 歸零
        if treat_code != '':
            self._add_care_row(treat_code, self.ui.tableWidget_prescript.rowCount())

    # 乳癌肝癌照護給藥
    def set_cancer_prescript(self, pres_days):
        if pres_days <= 0:  #未給藥
            return

        if pres_days <= 7:
            treat_code = 'P56001'
        elif pres_days <= 14:
            treat_code = 'P56002'
        elif pres_days <= 21:
            treat_code = 'P56003'
        else:
            treat_code = 'P56004'

        self._remove_specific_treat_code(['P56001', 'P56002', 'P56003', 'P56004'])  # 歸零
        self._add_care_row(treat_code, self.ui.tableWidget_prescript.rowCount())

    # 移除指定的醫令list
    def _remove_specific_treat_code(self, treat_code):
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            ins_code = self.ui.tableWidget_prescript.item(row_no, 8)
            if ins_code is not None:
                ins_code = ins_code.text()

            if ins_code in treat_code:  # 刪掉指定的醫令
                self.ui.tableWidget_prescript.removeRow(row_no)

    def _add_care_row(self, treat_code, row_no):
        sql = '''
            SELECT * FROM charge_settings
            WHERE
                ChargeType = "照護費" AND
                InsCode = "{0}" 
        '''.format(treat_code)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        charge_row = rows[0]

        row = {}
        row['MedicineType'] = '照護'
        row['MedicineKey'] = string_utils.xstr(charge_row['ChargeSettingsKey'])
        row['MedicineName'] = string_utils.xstr(charge_row['ItemName'])
        row['InsCode'] = treat_code
        row['Price'] = number_utils.get_integer(charge_row['Amount'])
        row['Dosage'] = 1
        row['Unit'] = '次'
        row['Amount'] = row['Price']
        self.append_null_medicine()
        self.append_prescript(row, row_no)

    def append_prescript(self, row, row_no):
        prescript_row = [
            '-1',
            string_utils.xstr(row_no+1),
            string_utils.xstr(self.case_key),
            string_utils.xstr(self.case_date),
            string_utils.xstr(self.medicine_set),
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['Price']),
            string_utils.xstr(row['Dosage']),
            string_utils.xstr(row['Unit']),
            string_utils.xstr(row['Amount']),
        ]

        for col_no, item in zip(range(len(prescript_row)), prescript_row):
            self.ui.tableWidget_prescript.setItem(
                row_no, col_no, QtWidgets.QTableWidgetItem(item)
            )
            if col_no in [9, 10, 12]:
                self.ui.tableWidget_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [11]:
                self.ui.tableWidget_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    # 開啟加強照護支付標準表
    def _open_ins_care_dialog(self):
        dialog = dialog_ins_care.DialogInsCare(
            self, self.database, self.system_settings, self.treat_type,
        )

        if dialog.exec_():
            treat_code = dialog.ins_code
            self._add_care_row(treat_code, self.ui.tableWidget_prescript.rowCount())
            self.parent.calculate_ins_fees()

        dialog.close_all()
        dialog.deleteLater()

