#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from libs import ui_settings
from libs import strings
from libs import nhi_utils
from classes import table_widget
from dialog import dialog_input_medicine


# 輸入健保處方 2018.04.14
class InsPrescriptRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsPrescriptRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.case_date = self.parent.medical_record['CaseDate']
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._set_medical_record()
        self._read_cases()
        self._read_prescript()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_INS_PRESCRIPT_RECORD, self)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0, 5, 6, 7, 8, 9, 10, 11, 12])
        self.table_widget_treat = table_widget.TableWidget(self.ui.tableWidget_treat, self.database)
        self.table_widget_treat.set_column_hidden([0, 2, 3, 4, 5, 6, 7])
        self._set_table_width()
        self._set_combo_box()
        self._set_treat_ui()

    def _set_treat_ui(self):
        self.combo_box_treatment = QtWidgets.QComboBox()
        ui_settings.set_combo_box(self.combo_box_treatment, nhi_utils.INS_TREAT, None)
        self.ui.tableWidget_treat.setRowCount(1)
        self.ui.tableWidget_treat.setCellWidget(0, 1, self.combo_box_treatment)
        self.combo_box_treatment.currentTextChanged.connect(self._combo_box_treat_changed)

    def _set_combo_box(self):
        ui_settings.set_combo_box(
            self.ui.comboBox_package,
            nhi_utils.PACKAGE
        )
        ui_settings.set_combo_box(
            self.ui.comboBox_pres_days,
            nhi_utils.PRESDAYS
        )
        ui_settings.set_combo_box(
            self.ui.comboBox_instruction,
            nhi_utils.INSTRUCTION
        )

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self.append_null_medicine)
        self.ui.toolButton_remove_medicine.clicked.connect(self.remove_medicine)
        self.ui.toolButton_add_treat.clicked.connect(self.append_null_treat)
        self.ui.toolButton_remove_treat.clicked.connect(self.remove_treat)
        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press
        self.ui.tableWidget_treat.keyPressEvent = self._table_widget_treat_key_press
        self.ui.comboBox_pres_days.currentTextChanged.connect(self.pres_days_changed)

    def _table_widget_prescript_key_press(self, event):
        key = event.key()
        current_row = self.ui.tableWidget_prescript.currentRow()

        if key == QtCore.Qt.Key_Delete:
            self.remove_medicine()
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
                self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow()+1, 2)

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_prescript, event)

    def open_medicine_dialog(self):
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 2)
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 1)
        item = self.ui.tableWidget_prescript.item(self.ui.tableWidget_prescript.currentRow(), 1)
        if item is None or item.text() == '':
            return

        medicine_type = 'AND (MedicineType = "單方" OR MedicineType = "複方" OR MedicineType = "成方")'
        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
            {1}
        '''.format(item.text(), medicine_type)
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
                '健保藥品',
                self.ui.tableWidget_prescript,
            )
            dialog.exec_()
            dialog.deleteLater()

    def _table_widget_treat_key_press(self, event):
        key = event.key()
        current_row = self.ui.tableWidget_treat.currentRow()

        if key == QtCore.Qt.Key_Delete:
            self.remove_treat()
        elif key == QtCore.Qt.Key_Up:
            if current_row == 1:
                return

            if self.ui.tableWidget_treat.item(current_row, 0) is None:
                self.ui.tableWidget_treat.removeRow(current_row)
                return
        elif key == QtCore.Qt.Key_Down:
            if current_row == self.ui.tableWidget_treat.rowCount() - 1 and \
                    self.ui.tableWidget_treat.item(current_row, 0) is not None:
                self.append_null_treat()
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if self.ui.tableWidget_treat.currentColumn() == 1:
                self.open_treat_dialog()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_treat, event)

    def open_treat_dialog(self):
        self.ui.tableWidget_treat.setCurrentCell(self.ui.tableWidget_treat.currentRow(), 2)
        self.ui.tableWidget_treat.setCurrentCell(self.ui.tableWidget_treat.currentRow(), 1)
        item = self.ui.tableWidget_treat.item(self.ui.tableWidget_treat.currentRow(), 1)
        if item is None or item.text() == '':
            return

        medicine_type = 'AND (MedicineType = "穴道" OR MedicineType = "處置" OR MedicineType = "成方")'
        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
            {1}
        '''.format(item.text(), medicine_type)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            if self.table_widget_treat.field_value(0) is None:
                item.setText(None)
            else:
                item.setText(item.text())
        elif len(rows) == 1:
            self.append_treat(rows[0])
            self.append_null_treat()
        else:
            dialog = dialog_input_medicine.DialogInputMedicine(
                self, self.database,
                self.system_settings,
                '健保處置',
                self.ui.tableWidget_treat,
            )
            dialog.exec_()
            dialog.deleteLater()

    def append_prescript(self, row):
        if row['Dosage'] is None:
            dosage = ''
        else:
            dosage = str(row['Dosage'])

        prescript_rec = [
            [0, '-1'],
            [1, row['MedicineName']],
            [2, dosage],
            [3, row['Unit']],
            [4, None],
            [5, str(self.ui.tableWidget_prescript.currentRow()+1)],
            [6, str(self.case_key)],
            [7, str(self.case_date)],
            [8, '1'],
            [9, row['MedicineType']],
            [10, row['MedicineKey']],
            [11, row['InsCode']],
            [12, self.system_settings.field('劑量模式')],
        ]

        self.set_prescript(prescript_rec)
        self.set_default_pres_days()

    def append_treat(self, row):
        treat_rec = [
            [0, '-1'],
            [1, row['MedicineName']],
            [2, str(self.case_key)],
            [3, str(self.case_date)],
            [4, '1'],
            [5, row['MedicineType']],
            [6, row['MedicineKey']],
            [7, row['InsCode']],
        ]

        self.set_treat(treat_rec)

    def set_prescript(self, prescript_rec):
        for item in prescript_rec:
            self.ui.tableWidget_prescript.setItem(
                self.ui.tableWidget_prescript.currentRow(), item[0],
                QtWidgets.QTableWidgetItem(item[1])
            )

    def set_treat(self, treat_rec):
        for item in treat_rec:
            self.ui.tableWidget_treat.setItem(
                self.ui.tableWidget_treat.currentRow(), item[0],
                QtWidgets.QTableWidgetItem(item[1])
            )

    def _set_table_width(self):
        medicine_width = [
            70,
            200, 60, 50, 60,
            100, 100, 100, 100, 100, 100, 100, 100
        ]
        treat_width = [
            70,
            120,
            100, 100, 100, 100, 100, 100,
        ]

        self.table_widget_prescript.set_table_heading_width(medicine_width)
        self.table_widget_treat.set_table_heading_width(treat_width)

    def _set_medical_record(self):
        package = strings.xstr(self.parent.medical_record['Package1'])
        if package == '0':
            package = None
        pres_days = strings.xstr(self.parent.medical_record['PresDays1'])
        if pres_days == '0':
            pres_days = None
        instruction = strings.xstr(self.parent.medical_record['Instruction1'])
        if instruction == '':
            instruction = None

        self.ui.comboBox_package.setCurrentText(package)
        self.ui.comboBox_pres_days.setCurrentText(pres_days)
        self.ui.comboBox_instruction.setCurrentText(instruction)

    def _read_cases(self):
        sql = """ 
            SELECT Treatment FROM cases WHERE 
            (CaseKey = {0})
        """.format(self.case_key)
        row = self.database.select_record(sql)[0]
        self.treatment = row['Treatment']

    def _read_prescript(self):
        self._read_medicine()
        self._read_treat()

        if self.parent.call_from == '醫師看診作業':
            self.append_null_medicine()
            if self.treatment is not None or str(self.treatment).strip() != '':
                self.append_null_treat()

    def _read_medicine(self):
        medicine_groups = nhi_utils.get_medicine_type(self.database, '藥品類別')
        sql = """ 
            SELECT * FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = 1) AND
            (MedicineType in {1})
            ORDER BY PrescriptNo, PrescriptKey
        """.format(self.case_key, tuple(medicine_groups))
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, rec_no, rec):
        prescript_rec = [
            strings.xstr(rec['PrescriptKey']),
            strings.xstr(rec['MedicineName']),
            strings.xstr(rec['Dosage']),
            strings.xstr(rec['Unit']),
            strings.xstr(rec['Instruction']),
            strings.xstr(rec['PrescriptNo']),
            strings.xstr(rec['CaseKey']),
            strings.xstr(rec['CaseDate']),
            strings.xstr(rec['MedicineSet']),
            strings.xstr(rec['MedicineType']),
            strings.xstr(rec['MedicineKey']),
            strings.xstr(rec['InsCode']),
            strings.xstr(rec['DosageMode']),
        ]

        for column in range(0, self.ui.tableWidget_prescript.columnCount()):
            self.ui.tableWidget_prescript.setItem(rec_no,
                                                  column,
                                                  QtWidgets.QTableWidgetItem(prescript_rec[column]))
            if column in [2]:
                self.ui.tableWidget_prescript.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [3]:
                self.ui.tableWidget_prescript.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            if rec['InsCode'] == '':
                self.ui.tableWidget_prescript.item(rec_no, column).setForeground(QtGui.QColor('blue'))

    def _read_treat(self):
        self.combo_box_treatment.setCurrentText('')
        if self.treatment is not None or str(self.treatment).strip() != '':
            self.combo_box_treatment.setCurrentText(self.treatment)

        medicine_groups = nhi_utils.get_medicine_type(self.database, '處置類別')
        sql = """ 
            SELECT * FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = 1) AND
            (MedicineType in {1}) AND
            (MedicineName not in {2})
            ORDER BY PrescriptKey
        """.format(self.case_key, tuple(medicine_groups), tuple(nhi_utils.INS_TREAT))
        self.table_widget_treat.set_db_data(sql, self._set_treat_data, None, 1)

    def _set_treat_data(self, rec_no, rec):
        treat_rec = [
            strings.xstr(rec['PrescriptKey']),
            strings.xstr(rec['MedicineName']),
            strings.xstr(rec['CaseKey']),
            strings.xstr(rec['CaseDate']),
            strings.xstr(rec['MedicineSet']),
            strings.xstr(rec['MedicineType']),
            strings.xstr(rec['MedicineKey']),
            strings.xstr(rec['InsCode']),
        ]

        for column in range(0, self.ui.tableWidget_treat.columnCount()):
            self.ui.tableWidget_treat.setItem(
                rec_no, column, QtWidgets.QTableWidgetItem(treat_rec[column]))

    # 增加處方資料
    def append_null_medicine(self):
        row_count = self.table_widget_prescript.row_count()
        if row_count <= 0:
            self._insert_medicine_row(row_count)
            return

        item = self.ui.tableWidget_prescript.item(row_count-1, 1)
        if item is None or item.text().strip() == '':
            return

        self._insert_medicine_row(row_count)

    # 增加處方資料
    def append_null_treat(self):
        if self.combo_box_treatment.currentText() == '':
            return

        row_count = self.table_widget_treat.row_count()
        if row_count <= 1:
            self._insert_treat_row(row_count)
            return

        item = self.ui.tableWidget_treat.item(row_count-1, 1)
        if item is None or item.text().strip() == '':
            return

        self._insert_treat_row(row_count)

    def _insert_medicine_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(index, 1)

    def _insert_treat_row(self, index):
        self.ui.tableWidget_treat.setFocus(True)
        self.ui.tableWidget_treat.insertRow(index)
        self.ui.tableWidget_treat.setCurrentCell(index, 1)

    def set_default_pres_days(self):
        if self.ui.tableWidget_prescript.rowCount() <= 0:
            return

        if self.ui.tableWidget_prescript.item(0, 1) is None:
            return

        if self.ui.comboBox_package.currentText() != '':
            return

        if self.ui.comboBox_pres_days.currentText() != '':
            return

        self.ui.comboBox_package.setCurrentText(self.system_settings.field('給藥包數'))
        self.ui.comboBox_pres_days.setCurrentText(self.system_settings.field('給藥天數'))
        self.ui.comboBox_instruction.setCurrentText(self.system_settings.field('用藥指示'))

    # 刪除處方
    def remove_medicine(self):
        index = self.ui.tableWidget_prescript.currentRow()
        self.ui.tableWidget_prescript.removeRow(index)
        if self.ui.tableWidget_prescript.rowCount() <= 0:
            self.ui.comboBox_package.setCurrentText(None)
            self.ui.comboBox_pres_days.setCurrentText(None)
            self.ui.comboBox_instruction.setCurrentText(None)
            self.append_null_medicine()

    # 刪除處置
    def remove_treat(self):
        index = self.ui.tableWidget_treat.currentRow()
        if index > 0:
            self.ui.tableWidget_treat.removeRow(index)

        if self.ui.tableWidget_treat.rowCount() <= 1:
            self.append_null_treat()

    def save_prescript(self):
        self.save_medicine()
        self.save_treat()

    def save_medicine(self):
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

            if items[2] == '':
                items[2] = None
            prescript_no += 1
            items[5] = str(prescript_no)

            if items[0] == '-1':
                self.insert_prescript(items)
            else:
                self.update_prescript(items)

    def save_treat(self):
        treat_data_set = []
        for i in range(self.ui.tableWidget_treat.rowCount()):
            treat_rec = []
            for j in range(self.ui.tableWidget_treat.columnCount()):
                try:
                    treat_rec.append(self.ui.tableWidget_treat.item(i, j).text())
                except AttributeError:
                    treat_rec.append(None)

            treat_data_set.append(treat_rec)

        self.delete_not_exists_prescript(treat_data_set, '處置類別')

        for items in treat_data_set:
            if items[0] is None:
                continue

            if items[0] == '-1':
                self.insert_treat(items)
            else:
                self.update_treat(items)

    # 刪除不在tableWidget內的處方
    def delete_not_exists_prescript(self, prescript_data_set, medicine_type):
        prescript_key_list = []
        for items in prescript_data_set:
            prescript_key_list.append(items[0])

        medicine_type_list = nhi_utils.get_medicine_type(self.database, medicine_type)
        sql = '''
            SELECT * FROM prescript WHERE 
            CaseKey = {0} AND 
            MedicineSet = 1 AND
            MedicineType in {1}
        '''.format(self.case_key, tuple(medicine_type_list))

        rows = self.database.select_record(sql)
        for row in rows:
            if str(row['PrescriptKey']) not in prescript_key_list:
                self.database.exec_sql('DELETE FROM prescript where PrescriptKey = {0}'.format(row['PrescriptKey']))

    # 插入處方資料至資料庫內
    def insert_prescript(self, items):
        fields = [
            'MedicineName', 'Dosage', 'Unit', 'Instruction', 'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
        ]

        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
            items[8], items[9], items[10], items[11], items[12],
        ]
        self.database.insert_record('prescript', fields, data)

    # 插入處置資料至資料庫內
    def insert_treat(self, items):
        fields = [
            'MedicineName', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode',
        ]

        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
        ]
        self.database.insert_record('prescript', fields, data)

    # 更新處方資料至資料庫內
    def update_prescript(self, items):
        if items[10] == '':
            items[10] = None

        fields = [
            'MedicineName', 'Dosage', 'Unit', 'Instruction', 'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
        ]
        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
            items[8], items[9], items[10], items[11], items[12],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 更新處置資料至資料庫內
    def update_treat(self, items):
        fields = [
            'MedicineName', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode',
        ]
        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 拷貝過去病歷的處方
    def copy_past_prescript(self, case_key):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        sql = '''
            SELECT * FROM prescript WHERE CaseKey = {0} AND 
                MedicineSet = 1 ORDER BY PrescriptKey'''.format(case_key)
        rows = self.database.select_record(sql)
        for row in rows:
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row)

    # 處置內容變更
    def _combo_box_treat_changed(self):
        if self.combo_box_treatment.currentText() == '':
            self.ui.tableWidget_treat.setRowCount(0)
            self._set_treat_ui()
        else:
            self.append_null_treat()

        self.parent.calculate_ins_fees()

    # 藥日變更重新批價
    def pres_days_changed(self):
        self.parent.calculate_ins_fees()

