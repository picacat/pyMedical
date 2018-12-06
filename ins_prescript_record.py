
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import prescript_utils
from classes import table_widget
from dialog import dialog_input_medicine
from dialog import dialog_electric_acupuncture


# 輸入健保處方 2018.04.14
class InsPrescriptRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsPrescriptRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.medicine_set = args[3]
        self.case_date = self.parent.medical_record['CaseDate']
        self.ui = None

        self.signal_off = True
        self._set_ui()
        self._set_signal()
        self._read_cases()
        self._read_prescript()
        self.signal_off = False

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_PRESCRIPT_RECORD, self)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7, 8])
        self.table_widget_treat = table_widget.TableWidget(self.ui.tableWidget_treat, self.database)
        self.table_widget_treat.set_column_hidden([0, 1, 2, 3, 4, 5, 6])
        self._set_table_width()
        self._set_combo_box()
        self._set_treat_ui()

    def _set_treat_ui(self):
        self.combo_box_treatment = QtWidgets.QComboBox()
        ui_utils.set_combo_box(self.combo_box_treatment, nhi_utils.INS_TREAT, None)
        self.ui.tableWidget_treat.setRowCount(1)
        self.ui.tableWidget_treat.setCellWidget(0, 7, self.combo_box_treatment)
        self.combo_box_treatment.currentTextChanged.connect(self._combo_box_treat_changed)

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_package, nhi_utils.PACKAGE, None)
        ui_utils.set_combo_box(self.ui.comboBox_pres_days, nhi_utils.PRESDAYS, None)
        ui_utils.set_combo_box(self.ui.comboBox_instruction, nhi_utils.INSTRUCTION, None)

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self.append_null_medicine)
        self.ui.toolButton_remove_medicine.clicked.connect(self.remove_medicine)
        self.ui.toolButton_add_treat.clicked.connect(self.append_null_treat)
        self.ui.toolButton_remove_treat.clicked.connect(self.remove_treat)
        self.ui.toolButton_dictionary.clicked.connect(self._open_dictionary)
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
            if self.ui.tableWidget_prescript.currentColumn() == 9:
                self.open_medicine_dialog()
            elif self.ui.tableWidget_prescript.currentColumn() == 10:
                if self.system_settings.field('劑量模式') in ['日劑量', '總量']:
                    dosage_format = '.1f'
                else:
                    dosage_format = '.2f'

                self.table_widget_prescript.set_cell_text_format(
                    current_row, self.ui.tableWidget_prescript.currentColumn(),
                    dosage_format, 'float'
                )
                self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow()+1, 10)

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_prescript, event)

    def open_medicine_dialog(self):
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 10)
        self.ui.tableWidget_prescript.setCurrentCell(self.ui.tableWidget_prescript.currentRow(), 9)
        item = self.ui.tableWidget_prescript.item(self.ui.tableWidget_prescript.currentRow(), 9)
        if item is None or item.text() == '':
            return

        medicine_type = 'AND (MedicineType IN ("單方", "複方", "成方"))'
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
                self.medicine_set,
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
            if self.ui.tableWidget_treat.currentColumn() == 7:
                self.open_treat_dialog()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_treat, event)

    def open_treat_dialog(self):
        self.ui.tableWidget_treat.setCurrentCell(self.ui.tableWidget_treat.currentRow(), 6)
        self.ui.tableWidget_treat.setCurrentCell(self.ui.tableWidget_treat.currentRow(), 7)
        item = self.ui.tableWidget_treat.item(self.ui.tableWidget_treat.currentRow(), 7)
        if item is None or item.text() == '':
            return

        medicine_type = ''
        if self.combo_box_treatment.currentText() in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type = 'AND (MedicineType in ("穴道", "成方"))'
        elif self.combo_box_treatment.currentText() in nhi_utils.MASSAGE_TREAT:
            medicine_type = 'AND (MedicineType in ("處置", "成方"))'

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
                self.medicine_set,
                self.ui.tableWidget_treat,
            )
            dialog.exec_()
            dialog.deleteLater()

    def append_prescript(self, row, dosage=None):
        in_medicine_key = string_utils.xstr(row['MedicineKey'])
        if prescript_utils.check_prescript_exist(
                self.ui.tableWidget_prescript, 6, in_medicine_key):
            return

        prescript_row = [
            [0, '-1'],
            [1, string_utils.xstr(self.ui.tableWidget_prescript.currentRow() + 1)],
            [2, string_utils.xstr(self.case_key)],
            [3, string_utils.xstr(self.case_date)],
            [4, string_utils.xstr(self.medicine_set)],
            [5, string_utils.xstr(row['MedicineType'])],
            [6, string_utils.xstr(row['MedicineKey'])],
            [7, string_utils.xstr(row['InsCode'])],
            [8, self.system_settings.field('劑量模式')],
            [9, string_utils.xstr(row['MedicineName'])],
            [10, string_utils.xstr(dosage)],
            [11, string_utils.xstr(row['Unit'])],
            [12, None],
        ]

        self.set_prescript(prescript_row)
        self.set_default_pres_days()

    def set_prescript(self, row):
        row_no = self.ui.tableWidget_prescript.currentRow()
        for item in row:
            self.ui.tableWidget_prescript.setItem(
                row_no, item[0], QtWidgets.QTableWidgetItem(item[1])
            )

            if item[0] in [11]:
                self.ui.tableWidget_prescript.item(row_no, item[0]).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        ins_code = row[7][1]
        if ins_code == '':
            for column in range(self.ui.tableWidget_prescript.columnCount()):
                self.ui.tableWidget_prescript.item(row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

    def append_treat(self, row):
        in_medicine_key = string_utils.xstr(row['MedicineKey'])
        if prescript_utils.check_prescript_exist(
                self.ui.tableWidget_treat, 5, in_medicine_key):
            return

        treat_rec = [
            [0, '-1'],
            [1, string_utils.xstr(self.case_key)],
            [2, string_utils.xstr(self.case_date)],
            [3, string_utils.xstr(self.medicine_set)],
            [4, string_utils.xstr(row['MedicineType'])],
            [5, string_utils.xstr(row['MedicineKey'])],
            [6, string_utils.xstr(row['InsCode'])],
            [7, string_utils.xstr(row['MedicineName'])],
        ]

        self.set_treat(treat_rec)

    def set_treat(self, treat_rec):
        for item in treat_rec:
            self.ui.tableWidget_treat.setItem(
                self.ui.tableWidget_treat.currentRow(), item[0],
                QtWidgets.QTableWidgetItem(item[1])
            )

    def _set_table_width(self):
        medicine_width = [
            70,
            100, 100, 100, 100, 100, 100, 100, 100,
            200, 55, 50, 50,
        ]
        treat_width = [
            70,
            100, 100, 100, 100, 100, 100,
            150,
        ]

        self.table_widget_prescript.set_table_heading_width(medicine_width)
        self.table_widget_treat.set_table_heading_width(treat_width)

    def _read_cases(self):
        sql = """ 
            SELECT Treatment FROM cases WHERE 
            (CaseKey = {0})
        """.format(self.case_key)
        row = self.database.select_record(sql)[0]
        self.treatment = row['Treatment']

    def _read_prescript(self):
        self._read_dosage()
        self._read_medicine()
        self._read_treat()

        if self.parent.call_from == '醫師看診作業':
            self.append_null_medicine()
            if self.treatment is not None or str(self.treatment).strip() != '':
                self.append_null_treat()

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
        medicine_groups = nhi_utils.get_medicine_type(self.database, '藥品類別')
        sql = """ 
            SELECT * FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1}) AND
            (MedicineType in {2})
            ORDER BY PrescriptNo, PrescriptKey
        """.format(self.case_key, self.medicine_set, tuple(medicine_groups))
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        dosage = string_utils.xstr(row['Dosage'])
        if dosage != '':
            if self.system_settings.field('劑量模式') in ['日劑量', '總量']:
                dosage = '{0:.1f}'.format(row['Dosage'])
            elif self.system_settings.field('劑量模式') == '次劑量':
                dosage = '{0:.2f}'.format(row['Dosage'])

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
        ]

        for column in range(len(prescript_row)):
            self.ui.tableWidget_prescript.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(prescript_row[column])
            )
            if column in [10]:
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

    def _read_treat(self):
        self.combo_box_treatment.setCurrentText('')
        if self.treatment is not None or str(self.treatment).strip() != '':
            self.combo_box_treatment.setCurrentText(self.treatment)

        medicine_groups = nhi_utils.get_medicine_type(self.database, '處置類別')
        sql = """ 
            SELECT * FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1}) AND
            (MedicineType IN {2}) AND
            (MedicineName NOT IN {3})
            ORDER BY PrescriptKey
        """.format(self.case_key, self.medicine_set, tuple(medicine_groups), tuple(nhi_utils.INS_TREAT))
        self.table_widget_treat.set_db_data(sql, self._set_treat_data, None, 1)

    def _set_treat_data(self, rec_no, rec):
        treat_rec = [
            string_utils.xstr(rec['PrescriptKey']),
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['CaseDate']),
            string_utils.xstr(rec['MedicineSet']),
            string_utils.xstr(rec['MedicineType']),
            string_utils.xstr(rec['MedicineKey']),
            string_utils.xstr(rec['InsCode']),
            string_utils.xstr(rec['MedicineName']),
        ]

        for column in range(len(treat_rec)):
            self.ui.tableWidget_treat.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(treat_rec[column])
            )

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

    # 增加處方資料
    def append_null_treat(self):
        if self.combo_box_treatment.currentText() == '':
            return

        row_count = self.table_widget_treat.row_count()
        if row_count <= 1:
            self._insert_treat_row(row_count)
            return

        item = self.ui.tableWidget_treat.item(row_count-1, 7)
        if item is None or item.text().strip() == '':
            return

        self._insert_treat_row(row_count)

    def _insert_medicine_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(index, 9)

        self.ui.tableWidget_prescript.setItem(index, 10, QtWidgets.QTableWidgetItem(None))
        self.ui.tableWidget_prescript.item(index, 10).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _insert_treat_row(self, index):
        self.ui.tableWidget_treat.setFocus(True)
        self.ui.tableWidget_treat.insertRow(index)
        self.ui.tableWidget_treat.setCurrentCell(index, 7)

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
        self._save_dosage()
        self.save_medicine()
        self.save_treat()

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

            if items[10] == '':
                items[10] = None

            prescript_no += 1
            items[1] = str(prescript_no)

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
            MedicineSet = {1} AND
            MedicineType in {2}
        '''.format(self.case_key, self.medicine_set, tuple(medicine_type_list))

        rows = self.database.select_record(sql)
        for row in rows:
            if str(row['PrescriptKey']) not in prescript_key_list:
                self.database.exec_sql('DELETE FROM prescript where PrescriptKey = {0}'.format(row['PrescriptKey']))
                self.database.exec_sql('DELETE FROM presextend where PrescriptKey = {0}'.format(row['PrescriptKey']))

    # 插入處方資料至資料庫內
    def insert_prescript(self, items):
        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
            'MedicineName', 'Dosage', 'Unit', 'Instruction',
        ]

        data = [
            items[1], items[2], items[3],
            items[4], items[5], items[6], items[7], items[8],
            items[9], items[10], items[11], items[12],
        ]
        self.database.insert_record('prescript', fields, data)

    # 插入處置資料至資料庫內
    def insert_treat(self, items):
        fields = [
            'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode',
            'MedicineName'
        ]

        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
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
        ]
        data = [
            items[1], items[2], items[3],
            items[4], items[5], items[6], items[7], items[8],
            items[9], items[10], items[11], items[12],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 更新處置資料至資料庫內
    def update_treat(self, items):
        fields = [
            'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode',
            'MedicineName'
        ]
        data = [
            items[1], items[2], items[3], items[4], items[5], items[6], items[7],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 拷貝過去病歷的處方
    def copy_past_prescript(self, case_key):
        self._copy_past_medicine(case_key)
        self._copy_past_treat(case_key)

    def _copy_past_medicine(self, case_key):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        sql = '''
            SELECT * FROM prescript WHERE 
                CaseKey = {0} AND 
                MedicineSet = {1} AND
                MedicineType in ("單方", "複方") 
                ORDER BY PrescriptKey'''.format(case_key, self.medicine_set)
        rows = self.database.select_record(sql)
        for row in rows:
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])

    def _copy_past_treat(self, case_key):
        self.ui.tableWidget_treat.clearContents()
        self.ui.tableWidget_treat.setRowCount(1)
        self._set_treat_ui()
        sql = '''
            SELECT Treatment FROM cases WHERE 
                CaseKey = {0} 
        '''.format(case_key)
        row = self.database.select_record(sql)[0]
        treatment = row['Treatment']
        self.combo_box_treatment.setCurrentText(treatment)

        sql = '''
            SELECT * FROM prescript WHERE 
                CaseKey = {0} AND 
                MedicineType IN ("穴道", "處置") AND 
                MedicineSet = {1} ORDER BY PrescriptKey
        '''.format(case_key, self.medicine_set)
        rows = self.database.select_record(sql)
        for row in rows:
            if row['MedicineName'] is None:
                continue

            self.append_null_treat()
            self.append_treat(row)

    # 處置內容變更
    def _combo_box_treat_changed(self):
        if self.combo_box_treatment.currentText() == '':
            self.ui.tableWidget_treat.setRowCount(0)
            self._set_treat_ui()
        elif self.combo_box_treatment.currentText() == '電針治療':
            self._open_electric_acupuncture_dialog()
        else:
            self.append_null_treat()

        self._set_ins_care_treat(self.combo_box_treatment.currentText())
        self.parent.calculate_ins_fees()

    def _set_ins_care_treat(self, treatment):
        treat_type = self.parent.tab_registration.ui.comboBox_treat_type.currentText()
        if treat_type not in nhi_utils.IMPROVE_CARE_TREAT:
            return

        medicine_set = 11
        ins_care = self.parent.tab_list[medicine_set]
        if ins_care is not None:
            if treat_type == '助孕照護':
                ins_care.set_aid_pregnant_treat(treatment)
            elif treat_type == '保胎照護':
                ins_care.set_keep_baby_treat(treatment)
            elif treat_type in ['乳癌照護', '肝癌照護']:
                ins_care.set_cancer_treat(treatment)

    # 藥日變更重新批價
    def pres_days_changed(self):
        self._set_ins_care_pres_days()
        self.parent.calculate_ins_fees()

        treat_type = self.parent.tab_registration.ui.comboBox_treat_type.currentText()
        if treat_type in ['乳癌照護', '肝癌照護'] and self.ui.comboBox_pres_days.currentText() == '':
            self.ui.comboBox_pres_days.setCurrentText('7')  # 至少七天藥

        self.ui.comboBox_pres_days.setFocus(True)

    def _set_ins_care_pres_days(self):
        treat_type = self.parent.tab_registration.ui.comboBox_treat_type.currentText()
        if treat_type not in ['乳癌照護', '肝癌照護']:
            return

        pres_days = number_utils.get_integer(self.ui.comboBox_pres_days.currentText())

        medicine_set = 11
        ins_care = self.parent.tab_list[medicine_set]
        if ins_care is not None:
            if treat_type in ['乳癌照護', '肝癌照護']:
                ins_care.set_cancer_prescript(pres_days)

    # 開啟電針儀選擇視窗
    def _open_electric_acupuncture_dialog(self):
        if self.signal_off:
            return

        dialog = dialog_electric_acupuncture.DialogElectricAcupuncture(
            self, self.database, self.system_settings)

        dialog.exec_()

        wave = ''
        if dialog.ui.radioButton_1.isChecked():
            wave = '疏密波'
        elif dialog.ui.radioButton_1.isChecked():
            wave = '斷續波'
        elif dialog.ui.radioButton_1.isChecked():
            wave = '連續波'

        wave = '波形:{0}'.format(wave)
        freq = '頻率:{0}Hz'.format(dialog.ui.spinBox_freq.value())
        time = '時間:{0}分鐘'.format(dialog.ui.spinBox_time.value())

        electric_acupuncture_list = [
            wave, freq, time
        ]

        self.ui.tableWidget_treat.setRowCount(1)
        for item in electric_acupuncture_list:
            row = {}
            row['MedicineType'] = '穴道'
            row['MedicineKey'] = None
            row['InsCode'] = None
            row['MedicineName'] = item
            self.append_null_treat()
            self.append_treat(row)

        dialog.deleteLater()
        self.append_null_treat()

    def _open_dictionary(self):
        self.parent.open_dictionary(self.medicine_set, '健保處方')
