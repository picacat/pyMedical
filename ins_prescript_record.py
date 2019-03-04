
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import prescript_utils
from libs import db_utils

from classes import table_widget
from dialog import dialog_input_medicine
from dialog import dialog_electric_acupuncture
from dialog import dialog_rich_text


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
        self.copy_from = None

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
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.table_widget_treat = table_widget.TableWidget(self.ui.tableWidget_treat, self.database)
        self.table_widget_treat.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7])
        self._set_table_width()
        self._set_combo_box()
        self._set_treat_ui()

    def _set_treat_ui(self):
        self.combo_box_treatment = QtWidgets.QComboBox()
        ui_utils.set_combo_box(self.combo_box_treatment, nhi_utils.INS_TREAT, None)
        self.ui.tableWidget_treat.setRowCount(1)
        self.ui.tableWidget_treat.setCellWidget(
            0, prescript_utils.INS_TREAT_COL_NO['MedicineName'], self.combo_box_treatment)
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
        self.ui.toolButton_treat_dictionary.clicked.connect(self._open_treat_dictionary)
        self.ui.toolButton_show_costs.clicked.connect(self._show_costs)
        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press
        self.ui.tableWidget_treat.keyPressEvent = self._table_widget_treat_key_press
        self.ui.comboBox_pres_days.currentTextChanged.connect(self.pres_days_changed)
        self.ui.tableWidget_prescript.itemChanged.connect(self._prescript_item_changed)

    def _table_widget_prescript_key_press(self, event):
        key = event.key()
        current_row = self.ui.tableWidget_prescript.currentRow()

        if key == QtCore.Qt.Key_Delete:
            self.remove_medicine()
        elif key == QtCore.Qt.Key_Up:
            if self.ui.tableWidget_prescript.item(
                    current_row, prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']) is None:
                self.ui.tableWidget_prescript.removeRow(current_row)
                return

            if self.ui.tableWidget_prescript.currentColumn() == prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
        elif key == QtCore.Qt.Key_Down:
            if current_row == self.ui.tableWidget_prescript.rowCount() - 1 and \
                    self.ui.tableWidget_prescript.item(
                        current_row, prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']) is not None:
                self.append_null_medicine()

            if self.ui.tableWidget_prescript.currentColumn() == prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if self.ui.tableWidget_prescript.currentColumn() == prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']:
                self.open_medicine_dialog()
            elif self.ui.tableWidget_prescript.currentColumn() == prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
                if current_row < self.ui.tableWidget_prescript.rowCount() - 1:
                    self.ui.tableWidget_prescript.setCurrentCell(
                        self.ui.tableWidget_prescript.currentRow()+1,
                        prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'],
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
            self.ui.tableWidget_prescript.currentRow(),
            prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']
        )
        self.ui.tableWidget_prescript.setCurrentCell(
            self.ui.tableWidget_prescript.currentRow(),
            prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']
        )
        item = self.ui.tableWidget_prescript.item(
            self.ui.tableWidget_prescript.currentRow(),
            prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']
        )
        if item is None or item.text() == '':
            return

        previous_medicine_name = self.table_widget_prescript.field_value(
            prescript_utils.INS_PRESCRIPT_COL_NO['BackupMedicineName']
        )

        if item.text() == previous_medicine_name:
            return

        medicine_type = 'AND (MedicineType NOT IN ("水藥", "外用", "高貴", "穴道", "處置", "檢驗"))'
        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
            {1}
        '''.format(item.text(), medicine_type)
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
                '健保藥品',
                self.medicine_set,
                self.ui.tableWidget_prescript,
                previous_medicine_name,
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

            if self.ui.tableWidget_treat.item(
                    current_row, prescript_utils.INS_TREAT_COL_NO['PrescriptKey']) is None:
                self.ui.tableWidget_treat.removeRow(current_row)
                return
        elif key == QtCore.Qt.Key_Down:
            if current_row == self.ui.tableWidget_treat.rowCount() - 1 and \
                    self.ui.tableWidget_treat.item(
                        current_row, prescript_utils.INS_TREAT_COL_NO['PrescriptKey']) is not None:
                self.append_null_treat()
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if self.ui.tableWidget_treat.currentColumn() == prescript_utils.INS_TREAT_COL_NO['MedicineName']:
                self.open_treat_dialog()

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_treat, event)

    def open_treat_dialog(self):
        self.ui.tableWidget_treat.setCurrentCell(
            self.ui.tableWidget_treat.currentRow(),
            prescript_utils.INS_TREAT_COL_NO['InsCode']
        )
        self.ui.tableWidget_treat.setCurrentCell(
            self.ui.tableWidget_treat.currentRow(),
            prescript_utils.INS_TREAT_COL_NO['MedicineName']
        )
        item = self.ui.tableWidget_treat.item(
            self.ui.tableWidget_treat.currentRow(),
            prescript_utils.INS_TREAT_COL_NO['MedicineName']
        )
        if item is None or item.text() == '':
            return

        previous_medicine_name = self.table_widget_treat.field_value(
            prescript_utils.INS_TREAT_COL_NO['BackupMedicineName']
        )

        if item.text() == previous_medicine_name:
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
            item.setText(previous_medicine_name)
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
                prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey'], medicine_key):
            return

        prescript_row = [
            [prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey'], '-1'],
            [prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptNo'],
             string_utils.xstr(self.ui.tableWidget_prescript.currentRow() + 1)],
            [prescript_utils.INS_PRESCRIPT_COL_NO['CaseKey'], string_utils.xstr(self.case_key)],
            [prescript_utils.INS_PRESCRIPT_COL_NO['CaseDate'], string_utils.xstr(self.case_date)],
            [prescript_utils.INS_PRESCRIPT_COL_NO['MedicineSet'], string_utils.xstr(self.medicine_set)],
            [prescript_utils.INS_PRESCRIPT_COL_NO['MedicineType'], string_utils.xstr(row['MedicineType'])],
            [prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey'], medicine_key],
            [prescript_utils.INS_PRESCRIPT_COL_NO['InsCode'], string_utils.xstr(row['InsCode'])],
            [prescript_utils.INS_PRESCRIPT_COL_NO['DosageMode'], self.system_settings.field('劑量模式')],
            [prescript_utils.INS_PRESCRIPT_COL_NO['BackupMedicineName'], string_utils.xstr(row['MedicineName'])],
            [prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName'], string_utils.xstr(row['MedicineName'])],
            [prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'], string_utils.xstr(dosage)],
            [prescript_utils.INS_PRESCRIPT_COL_NO['Unit'], string_utils.xstr(row['Unit'])],
            [prescript_utils.INS_PRESCRIPT_COL_NO['Instruction'], None],
        ]

        self.set_prescript(prescript_row)
        if self.medicine_set == 1:  # 健保預設給藥日份
            self.set_default_pres_days()

        db_utils.increment_hit_rate(self.database, 'medicine', 'MedicineKey', medicine_key)

    def set_prescript(self, row):
        medicine_type = row[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineType']][1]
        if medicine_type == '成方':
            prescript_utils.extract_compound(
                self.database, row,
                self.ui.tableWidget_prescript, self.ui.tableWidget_treat,
            )
            return

        row_no = self.ui.tableWidget_prescript.currentRow()
        for item in row:
            self.ui.tableWidget_prescript.setItem(
                row_no, item[0], QtWidgets.QTableWidgetItem(item[1])
            )

            if item[0] in [prescript_utils.INS_PRESCRIPT_COL_NO['Unit']]:
                self.ui.tableWidget_prescript.item(row_no, item[0]).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

        ins_code = row[prescript_utils.INS_PRESCRIPT_COL_NO['InsCode']][1]
        if ins_code == '':
            for column in range(self.ui.tableWidget_prescript.columnCount()):
                item = self.ui.tableWidget_prescript.item(row_no, column)
                if item is not None:
                    item.setForeground(QtGui.QColor('blue'))

        medicine_key = row[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey']][1]
        description = prescript_utils.get_medicine_description(self.database, medicine_key)
        self._add_prescript_info_button(row_no, description)

    def append_treat(self, row):
        medicine_type = string_utils.xstr(row['MedicineType'])
        medicine_key = string_utils.xstr(row['MedicineKey'])
        if prescript_utils.check_prescript_duplicates(
                self.ui.tableWidget_treat,
                medicine_type,
                prescript_utils.INS_TREAT_COL_NO['MedicineKey'], medicine_key):
            return

        treat_row = [
            [prescript_utils.INS_TREAT_COL_NO['PrescriptKey'], '-1'],
            [prescript_utils.INS_TREAT_COL_NO['CaseKey'], string_utils.xstr(self.case_key)],
            [prescript_utils.INS_TREAT_COL_NO['CaseDate'], string_utils.xstr(self.case_date)],
            [prescript_utils.INS_TREAT_COL_NO['MedicineSet'], string_utils.xstr(self.medicine_set)],
            [prescript_utils.INS_TREAT_COL_NO['MedicineType'], string_utils.xstr(row['MedicineType'])],
            [prescript_utils.INS_TREAT_COL_NO['MedicineKey'], string_utils.xstr(row['MedicineKey'])],
            [prescript_utils.INS_TREAT_COL_NO['InsCode'], string_utils.xstr(row['InsCode'])],
            [prescript_utils.INS_TREAT_COL_NO['BackupMedicineName'], string_utils.xstr(row['MedicineName'])],
            [prescript_utils.INS_TREAT_COL_NO['MedicineName'], string_utils.xstr(row['MedicineName'])],
        ]

        self.set_treat(treat_row)

    def set_treat(self, treat_row):
        for item in treat_row:
            self.ui.tableWidget_treat.setItem(
                self.ui.tableWidget_treat.currentRow(), item[0],
                QtWidgets.QTableWidgetItem(item[1])
            )

    def _set_table_width(self):
        medicine_width = [
            70,
            100, 100, 100, 100, 100, 100, 100, 100, 100,
            190, 50, 50, 50, 20,
        ]
        treat_width = [
            70,
            100, 100, 100, 100, 100, 100, 100,
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
        self._calculate_total_dosage()
        self._calculate_total_costs()

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
            SELECT * FROM prescript 
            WHERE 
                (CaseKey = {0}) AND (MedicineSet = {1}) AND
                (MedicineType in {2})
            ORDER BY PrescriptNo, PrescriptKey
        """.format(self.case_key, self.medicine_set, tuple(medicine_groups))
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        medicine_key = row['MedicineKey']
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
            string_utils.xstr(medicine_key),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['DosageMode']),
            string_utils.xstr(row['MedicineName']),
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
            if column in [prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']]:
                self.ui.tableWidget_prescript.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [prescript_utils.INS_PRESCRIPT_COL_NO['Unit']]:
                self.ui.tableWidget_prescript.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsCode'] == '':
                self.ui.tableWidget_prescript.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

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
            row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Info'], button)

    def _show_medicine_description(self, description):
        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'rich_text', description
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

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

        item = self.ui.tableWidget_prescript.item(
            row_count-1, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName'])
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

        item = self.ui.tableWidget_treat.item(
            row_count-1, prescript_utils.INS_TREAT_COL_NO['MedicineName'])
        if item is None or item.text().strip() == '':
            return

        self._insert_treat_row(row_count)

    def _insert_medicine_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(
            index, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']
        )

        self.ui.tableWidget_prescript.setItem(
            index, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'], QtWidgets.QTableWidgetItem(None)
        )
        self.ui.tableWidget_prescript.item(
            index, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _insert_treat_row(self, index):
        self.ui.tableWidget_treat.setFocus(True)
        self.ui.tableWidget_treat.insertRow(index)
        self.ui.tableWidget_treat.setCurrentCell(
            index, prescript_utils.INS_TREAT_COL_NO['MedicineName']
        )

    def set_default_pres_days(self):
        if self.ui.tableWidget_prescript.rowCount() <= 0:
            return

        if self.ui.tableWidget_prescript.item(
                0, prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']) is None:
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

        self._calculate_total_dosage()
        self._calculate_total_costs()

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
            if items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']] is None:
                continue

            if items[prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']] == '':
                items[prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']] = None

            prescript_no += 1
            items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptNo']] = str(prescript_no)

            if items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']] == '-1':
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
            if items[prescript_utils.INS_TREAT_COL_NO['PrescriptKey']] is None:
                continue

            if items[prescript_utils.INS_TREAT_COL_NO['PrescriptKey']] == '-1':
                self.insert_treat(items)
            else:
                self.update_treat(items)

    # 刪除不在tableWidget內的處方
    def delete_not_exists_prescript(self, prescript_data_set, medicine_type):
        prescript_key_list = []
        for items in prescript_data_set:
            prescript_key_list.append(items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']])

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
            items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptNo']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['CaseKey']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['CaseDate']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineSet']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineType']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['InsCode']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['DosageMode']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['Unit']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['Instruction']],
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
            items[prescript_utils.INS_TREAT_COL_NO['CaseKey']],
            items[prescript_utils.INS_TREAT_COL_NO['CaseDate']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineSet']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineType']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineKey']],
            items[prescript_utils.INS_TREAT_COL_NO['InsCode']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineName']],
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
            items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptNo']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['CaseKey']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['CaseDate']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineSet']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineType']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['InsCode']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['DosageMode']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['Unit']],
            items[prescript_utils.INS_PRESCRIPT_COL_NO['Instruction']],
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
            items[prescript_utils.INS_TREAT_COL_NO['CaseKey']],
            items[prescript_utils.INS_TREAT_COL_NO['CaseDate']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineSet']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineType']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineKey']],
            items[prescript_utils.INS_TREAT_COL_NO['InsCode']],
            items[prescript_utils.INS_TREAT_COL_NO['MedicineName']],
        ]
        self.database.update_record(
            'prescript', fields, 'PrescriptKey', items[0], data)

    # 拷貝過去病歷的處方
    def copy_past_prescript(self, case_key, copy_from=None):
        self.copy_from = copy_from
        self._copy_past_medicine(case_key)
        self._copy_past_treat(case_key)

        self.ui.tableWidget_prescript.resizeRowsToContents()

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
        for row_no, row in zip(range(len(rows)), rows):
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])

    def _copy_past_treat(self, case_key):
        self.ui.tableWidget_treat.clearContents()
        self.ui.tableWidget_treat.setRowCount(1)
        self._set_treat_ui()
        sql = '''
            SELECT Treatment FROM cases WHERE 
                CaseKey = {0} 
        '''.format(case_key)
        row = self.database.select_record(sql)[0]
        treatment = string_utils.xstr(row['Treatment'])
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
    def _combo_box_treat_changed(self, copy_from=None):
        if self.combo_box_treatment.currentText() == '':
            self.ui.tableWidget_treat.setRowCount(0)
            self._set_treat_ui()
        elif self.combo_box_treatment.currentText() == '電針治療':
            if self.copy_from != '病歷拷貝':
                self._open_electric_acupuncture_dialog()

            self.copy_from = None
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

    def _open_treat_dictionary(self):
        self.parent.open_dictionary(self.medicine_set, '健保處置')

    def _prescript_item_changed(self, item):
        if self.ui.tableWidget_prescript.rowCount() <= 0:
            enabled = False
        else:
            enabled = True

        self.ui.toolButton_remove_medicine.setEnabled(enabled)
        self.ui.toolButton_show_costs.setEnabled(enabled)

        if item is None:
            return

        col_no = item.column()
        if col_no == prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']:
            self._calculate_total_dosage()
            self._calculate_total_costs()

    def _calculate_total_dosage(self):
        total_dosage = 0.0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            item = self.ui.tableWidget_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])
            if item is None:
                continue

            dosage = number_utils.get_float(item.text())
            total_dosage += dosage

        self.ui.label_total_dosage.setText('總量: {0}'.format(total_dosage))

    def _calculate_total_costs(self):
        total_costs = 0.0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            dosage_item = self.ui.tableWidget_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])
            if dosage_item is None:
                continue

            medicine_key_item = self.ui.tableWidget_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey'])
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

    def _show_costs(self):
        html = prescript_utils.get_costs_html(
            self.database, self.ui.tableWidget_prescript, prescript_utils.INS_PRESCRIPT_COL_NO
        )
        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'html', html
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

