
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import prescript_utils
from libs import db_utils
from libs import system_utils
from libs import case_utils
from libs import personnel_utils

from classes import table_widget
from dialog import dialog_input_medicine
from dialog import dialog_electric_acupuncture
from dialog import dialog_rich_text
from dialog import dialog_acupuncture_point


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
        self.call_from = args[4]
        self.case_date = self.parent.medical_record['CaseDate']
        self.copy_from = None
        self.ui = None

        self.signal_off = True
        self._set_ui()
        self._set_signal()
        self._read_cases()
        self._read_prescript()
        self.signal_off = False

        self.user_name = self.system_settings.field('使用者')
        self._set_permission()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INS_PRESCRIPT_RECORD, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.table_widget_treat = table_widget.TableWidget(self.ui.tableWidget_treat, self.database)
        self.table_widget_treat.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7])

        self.ui.tableWidget_prescript.setDragEnabled(True)
        self.ui.tableWidget_prescript.setAcceptDrops(True)
        self.ui.tableWidget_treat.setDragEnabled(True)
        self.ui.tableWidget_treat.setAcceptDrops(True)

        self._set_table_width()
        self._set_combo_box()
        self.set_treat_ui()

    def set_treat_ui(self):
        self.combo_box_treatment = QtWidgets.QComboBox()
        ui_utils.set_combo_box(self.combo_box_treatment, nhi_utils.INS_TREAT, None)
        self.ui.tableWidget_treat.setRowCount(1)
        self.ui.tableWidget_treat.setCellWidget(
            0, prescript_utils.INS_TREAT_COL_NO['MedicineName'], self.combo_box_treatment
        )
        self.combo_box_treatment.currentTextChanged.connect(self._combo_box_treat_changed)

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_package, nhi_utils.PACKAGE, None)
        ui_utils.set_combo_box(self.ui.comboBox_pres_days, nhi_utils.PRESDAYS, None)
        ui_utils.set_instruction_combo_box(self.database, self.ui.comboBox_instruction)

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self.append_null_medicine)
        self.ui.toolButton_remove_medicine.clicked.connect(self.remove_medicine)
        self.ui.toolButton_add_treat.clicked.connect(self.append_null_treat)
        self.ui.toolButton_remove_treat.clicked.connect(self.remove_treat)
        self.ui.toolButton_dictionary.clicked.connect(self._open_dictionary)
        self.ui.toolButton_treat_dictionary.clicked.connect(self._open_treat_dictionary)
        self.ui.toolButton_acupuncture_point.clicked.connect(self._show_acupuncture_point)
        self.ui.toolButton_show_costs.clicked.connect(self._show_costs)
        self.ui.toolButton_medicine_info.clicked.connect(self._show_medicine_description)
        self.ui.toolButton_clear_medical_record.clicked.connect(self._clear_medical_record)
        self.ui.toolButton_copy.clicked.connect(self._copy_prescript)
        self.ui.toolButton_clear_medicine.clicked.connect(lambda:self._clear_medicine(warning=True))
        self.ui.toolButton_clear_treat.clicked.connect(lambda:self._clear_treat(warning=True))

        self.ui.comboBox_pres_days.currentTextChanged.connect(self.pres_days_changed)
        self.ui.tableWidget_prescript.itemChanged.connect(self._prescript_item_changed)
        self.ui.tableWidget_prescript.itemSelectionChanged.connect(self._prescript_item_selection_changed)

        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press
        self.ui.tableWidget_treat.keyPressEvent = self._table_widget_treat_key_press
        self.ui.tableWidget_prescript.cellClicked.connect(self._prescript_cell_clicked)
        self.ui.tableWidget_treat.cellClicked.connect(self._prescript_cell_clicked)
        self.ui.tableWidget_prescript.dropEvent = self.prescript_drop_event
        self.ui.tableWidget_treat.dropEvent = self.treat_drop_event

        self.ui.checkBox_pharmacy.clicked.connect(self._set_pharmacy)

    def _set_permission(self):
        # if self.call_from == '醫師看診作業':
        #     return

        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '醫師看診作業', '病歷登錄', self.user_name) == 'Y':
            return

        if personnel_utils.get_permission(self.database, '病歷資料', '病歷修正', self.user_name) == 'Y':
            return

        self.ui.toolButton_clear_medical_record.setEnabled(False)
        self.ui.toolButton_add_medicine.setEnabled(False)
        self.ui.toolButton_remove_medicine.setEnabled(False)
        self.ui.toolButton_clear_medicine.setEnabled(False)
        self.ui.toolButton_copy.setEnabled(False)
        self.ui.toolButton_dictionary.setEnabled(False)
        self.ui.toolButton_show_costs.setEnabled(False)
        self.ui.toolButton_medicine_info.setEnabled(False)

        self.ui.comboBox_package.setEnabled(False)
        self.ui.comboBox_pres_days.setEnabled(False)
        self.ui.comboBox_instruction.setEnabled(False)

        self.ui.toolButton_add_treat.setEnabled(False)
        self.ui.toolButton_remove_treat.setEnabled(False)
        self.ui.toolButton_clear_treat.setEnabled(False)
        self.ui.toolButton_treat_dictionary.setEnabled(False)
        self.ui.toolButton_acupuncture_point.setEnabled(False)

        self.ui.tableWidget_prescript.setEnabled(False)
        self.ui.tableWidget_treat.setEnabled(False)

        self.ui.checkBox_pharmacy.setEnabled(False)

        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            for col_no in range(self.ui.tableWidget_prescript.columnCount()):
                item = self.ui.tableWidget_prescript.item(row_no, col_no)
                if item is None:
                    continue

                item.setForeground(QtGui.QColor('black'))

        for row_no in range(self.ui.tableWidget_treat.rowCount()):
            for col_no in range(self.ui.tableWidget_treat.columnCount()):
                item = self.ui.tableWidget_treat.item(row_no, col_no)
                if item is None:
                    continue

                item.setForeground(QtGui.QColor('black'))

    def prescript_drop_event(self, event):
        table_widget = event.source()

        source_row = table_widget.currentRow()
        target_item = table_widget.itemAt(event.pos())

        if target_item is None:
            target_row = table_widget.rowCount()
        else:
            target_row = target_item.row()

        medicine_name = table_widget.item(
            source_row, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']
        )
        if medicine_name is None:
            return

        medicine_name = medicine_name.text()
        if medicine_name == '':
            return

        # msg_box = QMessageBox()
        # msg_box.setIcon(QMessageBox.Warning)
        # msg_box.setWindowTitle('移動處方資料')
        # msg_box.setText("<font size='4' color='red'><b>確定移動{0}?</b></font>".format(medicine_name))
        # msg_box.setInformativeText("注意！處方移動後, 將無法回復!")
        # msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        # msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        # drag_record = msg_box.exec_()
        # if not drag_record:
        #     return

        prescript_row = []
        for col_no in range(table_widget.columnCount()):
            prescript_row.append(table_widget.item(source_row, col_no))

        table_widget.insertRow(target_row)
        for col_no in range(len(prescript_row)):
            table_widget.setItem(
                target_row, col_no,
                QtWidgets.QTableWidgetItem(prescript_row[col_no])
            )
            self._adjust_prescript_align(target_row, col_no)

        # medicine_key_item = prescript_row[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey']]
        # if medicine_key_item is not None:
        #     database._add_prescript_info_button(target_row, medicine_key_item.text())

        if target_row > source_row:
            remove_row = source_row
        else:
            remove_row = source_row + 1

        table_widget.removeRow(remove_row)
        table_widget.resizeRowsToContents()

        if target_row < source_row:
            move_row = target_row
        else:
            move_row = target_row - 1

        table_widget.setCurrentCell(move_row, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName'])

    def treat_drop_event(self, event):
        table_widget = event.source()

        source_row = table_widget.currentRow()
        target_item = table_widget.itemAt(event.pos())

        if target_item is None:
            target_row = table_widget.rowCount()
        else:
            target_row = target_item.row()

        treat_name = table_widget.item(
            source_row, prescript_utils.INS_TREAT_COL_NO['MedicineName']
        )

        if treat_name is None:
            return

        treat_name = treat_name.text()
        if treat_name == '':
            return

        # msg_box = QMessageBox()
        # msg_box.setIcon(QMessageBox.Warning)
        # msg_box.setWindowTitle('移動處置資料')
        # msg_box.setText("<font size='4' color='red'><b>確定移動{0}?</b></font>".format(treat_name))
        # msg_box.setInformativeText("注意！處置移動後, 將無法回復!")
        # msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        # msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        # drag_record = msg_box.exec_()
        # if not drag_record:
        #     return

        treat_row = []
        for col_no in range(table_widget.columnCount()):
            treat_row.append(table_widget.item(source_row, col_no))

        table_widget.insertRow(target_row)
        for col_no in range(len(treat_row)):
            table_widget.setItem(
                target_row, col_no,
                QtWidgets.QTableWidgetItem(treat_row[col_no])
            )

        if target_row > source_row:
            remove_row = source_row
        else:
            remove_row = source_row + 1

        table_widget.removeRow(remove_row)
        table_widget.resizeRowsToContents()

        if target_row < source_row:
            move_row = target_row
        else:
            move_row = target_row - 1

        table_widget.setCurrentCell(move_row, prescript_utils.INS_TREAT_COL_NO['MedicineName'])

    def _table_widget_prescript_key_press(self, event):
        system_utils.set_keyboard_layout('英文')

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
                self._check_total_dosage(current_row)
        elif key == QtCore.Qt.Key_Down:
            if current_row == self.ui.tableWidget_prescript.rowCount() - 1 and \
                    self.ui.tableWidget_prescript.item(
                        current_row, prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']) is not None:
                self.append_null_medicine()

            if self.ui.tableWidget_prescript.currentColumn() == prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']:
                self._set_dosage_format(current_row, self.ui.tableWidget_prescript.currentColumn())
                self._check_total_dosage(current_row)
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
                self._check_total_dosage(current_row)

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

        keyword = item.text()
        keyword = string_utils.replace_ascii_char(['\\', '"', '\''], keyword)

        medicine_type = 'AND (MedicineType NOT IN ("水藥", "外用", "高貴", "穴道", "處置", "檢驗"))'
        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
            {1}
        '''.format(keyword, medicine_type)
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
                keyword,
            )
            dialog.exec_()
            dialog.deleteLater()

    def _table_widget_treat_key_press(self, event):
        system_utils.set_keyboard_layout('英文')

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

        keyword = item.text()
        keyword = string_utils.replace_ascii_char(['\\', '"', '\''], keyword)

        medicine_type_script = ''
        if self.combo_box_treatment.currentText() in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type_script = 'AND (MedicineType IN ("穴道"))'
        elif self.combo_box_treatment.currentText() in nhi_utils.MASSAGE_TREAT:
            medicine_type_script = 'AND (MedicineType IN ("處置"))'

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{keyword}%" OR 
             InputCode LIKE "{keyword}%" OR 
             MedicineCode = "{keyword}" OR 
             InsCode = "{keyword}") 
            {medicine_type_script}
        '''.format(
            keyword=keyword,
            medicine_type_script=medicine_type_script,
        )
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
                keyword,
            )
            dialog.exec_()
            dialog.deleteLater()

    def append_prescript(self, row, dosage=None):
        medicine_key = string_utils.xstr(row['MedicineKey'])
        in_price = prescript_utils.get_medicine_field(
            self.database, medicine_key, 'InPrice'
        )
        if in_price is not None and in_price > 0:
            info = '$'
        else:
            info = ''

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
            [prescript_utils.INS_PRESCRIPT_COL_NO['Info'], info],
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

            if item[0] in [
                prescript_utils.INS_PRESCRIPT_COL_NO['Unit'],
                prescript_utils.INS_PRESCRIPT_COL_NO['Instruction'],
                prescript_utils.INS_PRESCRIPT_COL_NO['Info'],
            ]:
                self.ui.tableWidget_prescript.item(row_no, item[0]).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            elif item[0] in [prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']]:
                self.ui.tableWidget_prescript.item(row_no, item[0]).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        ins_code = row[prescript_utils.INS_PRESCRIPT_COL_NO['InsCode']][1]
        if ins_code == '':
            for column in range(self.ui.tableWidget_prescript.columnCount()):
                item = self.ui.tableWidget_prescript.item(row_no, column)
                if item is not None:
                    item.setForeground(QtGui.QColor('blue'))

        # medicine_key = medical_row[prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey']][1]
        # database._add_prescript_info_button(row_no, medicine_key)
        self.ui.tableWidget_prescript.resizeRowsToContents()

    def append_treat(self, row):
        medicine_type = string_utils.xstr(row['MedicineType'])
        medicine_key = string_utils.xstr(row['MedicineKey'])
        medicine_name = string_utils.xstr(row['MedicineName'])
        if prescript_utils.check_prescript_duplicates(
                self.ui.tableWidget_treat,
                medicine_type,
                prescript_utils.INS_TREAT_COL_NO['MedicineName'], medicine_name):
            return

        treat_row = [
            [prescript_utils.INS_TREAT_COL_NO['PrescriptKey'], '-1'],
            [prescript_utils.INS_TREAT_COL_NO['CaseKey'], string_utils.xstr(self.case_key)],
            [prescript_utils.INS_TREAT_COL_NO['CaseDate'], string_utils.xstr(self.case_date)],
            [prescript_utils.INS_TREAT_COL_NO['MedicineSet'], string_utils.xstr(self.medicine_set)],
            [prescript_utils.INS_TREAT_COL_NO['MedicineType'], medicine_type],
            [prescript_utils.INS_TREAT_COL_NO['MedicineKey'], medicine_key],
            [prescript_utils.INS_TREAT_COL_NO['InsCode'], string_utils.xstr(row['InsCode'])],
            [prescript_utils.INS_TREAT_COL_NO['BackupMedicineName'], medicine_name],
            [prescript_utils.INS_TREAT_COL_NO['MedicineName'], medicine_name],
        ]

        self.set_treat(treat_row)
        db_utils.increment_hit_rate(self.database, 'medicine', 'MedicineKey', medicine_key)

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
            270, 60, 50, 60, 10,
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
            SELECT PharmacyType, Treatment, DoctorDone FROM cases WHERE 
            (CaseKey = {0})
        """.format(self.case_key)
        row = self.database.select_record(sql)[0]
        self.treatment = row['Treatment']

        if row['DoctorDone'] == 'True':
            self.ui.toolButton_clear_medical_record.setEnabled(False)

        if string_utils.xstr(row['PharmacyType']) == '申報':
            self.ui.checkBox_pharmacy.setChecked(True)

    def _read_prescript(self):
        self._read_dosage()
        self._read_medicine()
        self._read_treat()

        prescript_utils.get_total_dosage(self.ui.tableWidget_prescript)
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
        if len(medicine_groups) <= 0:
            return

        sql = '''
            SELECT prescript.*, medicine.InPrice FROM prescript 
                LEFT JOIN medicine ON prescript.MedicineKey = medicine.MedicineKey
            WHERE 
                (CaseKey = {case_key}) AND (MedicineSet = {medicine_set}) AND
                (prescript.MedicineType in {medicine_groups})
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(
            case_key=self.case_key,
            medicine_set=self.medicine_set,
            medicine_groups=tuple(medicine_groups)
        )
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        medicine_key = row['MedicineKey']
        dosage = string_utils.xstr(row['Dosage'])
        ins_code = string_utils.xstr(row['InsCode'])
        in_price = number_utils.get_float(row['InPrice'])
        if in_price > 0:
            in_price_mark = '$'
        else:
            in_price_mark = ''

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
            ins_code,
            string_utils.xstr(row['DosageMode']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['MedicineName']),
            dosage,
            string_utils.xstr(row['Unit']),
            string_utils.xstr(row['Instruction']),
            in_price_mark,
        ]

        for col_no in range(len(prescript_row)):
            self.ui.tableWidget_prescript.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(prescript_row[col_no])
            )

            self._adjust_prescript_align(row_no, col_no)
            if ins_code == '':
                self.ui.tableWidget_prescript.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('blue')
                )

        # database._add_prescript_info_button(row_no, medicine_key)

    def _adjust_prescript_align(self, row_no, col_no):
        if col_no in [prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']]:
            self.ui.tableWidget_prescript.item(
                row_no, col_no).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
        elif col_no in [
            prescript_utils.INS_PRESCRIPT_COL_NO['Unit'],
            prescript_utils.INS_PRESCRIPT_COL_NO['Instruction'],
            prescript_utils.INS_PRESCRIPT_COL_NO['Info'],
        ]:
            self.ui.tableWidget_prescript.item(
                row_no, col_no).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )

    def _add_prescript_info_button(self, row_no, medicine_key):
        description = prescript_utils.get_medicine_description(self.database, medicine_key)

        button = QtWidgets.QPushButton()
        button.setIcon(QtGui.QIcon('./icons/gtk-info.svg'))
        button.setFlat(True)
        if description is None:
            button.setEnabled(False)

        button.clicked.connect(lambda : self._show_medicine_description(description))

        self.ui.tableWidget_prescript.setCellWidget(
            row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Info'], button)

    def _show_medicine_description(self):
        medicine_key_item = self.ui.tableWidget_prescript.item(
            self.ui.tableWidget_prescript.currentRow(),
            prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']
        )
        if medicine_key_item is None:
            return

        medicine_key = medicine_key_item.text()
        description = prescript_utils.get_medicine_description(self.database, medicine_key)
        if description is None:
            return

        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'rich_text', medicine_key, description
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

    def _read_treat(self):
        self.combo_box_treatment.setCurrentText('')
        if self.treatment is not None or str(self.treatment).strip() != '':
            self.combo_box_treatment.setCurrentText(self.treatment)

        medicine_groups = nhi_utils.get_medicine_type(self.database, '處置類別')
        if len(medicine_groups) <= 0:
            return

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

        self._set_total_dosage()
        self._set_total_cost()

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
            DELETE FROM dosage
            WHERE
                CaseKey = {case_key} AND
                MedicineSet = {medicine_set}
        '''.format(
            case_key=self.case_key,
            medicine_set=self.medicine_set,
        )
        self.database.exec_sql(sql)
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
        medicine_type_list = nhi_utils.get_medicine_type(self.database, medicine_type)
        if len(medicine_type_list) <= 0:
            return

        prescript_key_list = []
        for items in prescript_data_set:
            prescript_key_list.append(items[prescript_utils.INS_PRESCRIPT_COL_NO['PrescriptKey']])

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
            self.case_key,
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
            self.case_key,
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

        self.ui.tableWidget_prescript.resizeRowsToContents()

    def _copy_past_medicine(self, case_key):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        sql = '''
            SELECT * FROM prescript 
            WHERE 
                CaseKey = {case_key} AND 
                MedicineSet = {medicine_set} AND
                MedicineType NOT IN ("穴道", "處置", "檢驗")
            ORDER BY PrescriptKey
        '''.format(
            case_key=case_key,
            medicine_set=self.medicine_set,
        )
        rows = self.database.select_record(sql)
        for row_no, row in zip(range(len(rows)), rows):
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])

        self._copy_past_medicine_dosage(case_key)

    def _copy_past_medicine_dosage(self, case_key):
        pres_days = case_utils.get_pres_days(self.database, case_key, self.medicine_set)
        packages = case_utils.get_packages(self.database, case_key, self.medicine_set)
        instruction = case_utils.get_instruction(self.database, case_key, self.medicine_set)

        self.ui.comboBox_pres_days.setCurrentText(string_utils.xstr(pres_days))
        self.ui.comboBox_package.setCurrentText(string_utils.xstr(packages))
        self.ui.comboBox_instruction.setCurrentText(string_utils.xstr(instruction))

    # 拷貝過去病歷的處方
    def copy_past_treat(self, case_key, copy_from=None):
        self.copy_from = copy_from
        self._copy_past_treat(case_key)

        self.ui.tableWidget_treat.resizeRowsToContents()

    def _copy_past_treat(self, case_key):
        self.ui.tableWidget_treat.clearContents()
        self.ui.tableWidget_treat.setRowCount(1)
        self.set_treat_ui()
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

    # 拷貝過去病歷的處方
    def copy_host_prescript(self, database, case_key, copy_from=None):
        self.copy_from = copy_from
        self._copy_host_medicine(database, case_key)
        self.ui.tableWidget_prescript.resizeRowsToContents()

        pres_days = case_utils.get_host_pres_days(database, case_key)
        packages = case_utils.get_host_packages(database, case_key)
        instruction = case_utils.get_host_instruction(database, case_key)
        self.ui.comboBox_pres_days.setCurrentText(string_utils.xstr(pres_days))
        self.ui.comboBox_package.setCurrentText(string_utils.xstr(packages))
        self.ui.comboBox_instruction.setCurrentText(instruction)

    def _copy_host_medicine(self, database, case_key):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        sql = '''
            SELECT * FROM prescript 
            WHERE 
                CaseKey = {case_key} AND 
                MedicineSet = {medicine_set} AND
                MedicineType NOT IN ("穴道", "處置", "檢驗")
            ORDER BY PrescriptKey
        '''.format(
            case_key=case_key,
            medicine_set=self.medicine_set,
        )
        rows = database.select_record(sql)
        for row_no, row in zip(range(len(rows)), rows):
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])

    # 拷貝過去病歷的處方
    def copy_host_treat(self, database, case_key, copy_from=None):
        self.copy_from = copy_from
        self._copy_host_treat(database, case_key)

        self.ui.tableWidget_treat.resizeRowsToContents()

    def _copy_host_treat(self, database, case_key):
        self.ui.tableWidget_treat.clearContents()
        self.ui.tableWidget_treat.setRowCount(1)
        self.set_treat_ui()
        sql = '''
            SELECT Treatment FROM cases WHERE 
                CaseKey = {0} 
        '''.format(case_key)
        row = database.select_record(sql)[0]
        treatment = string_utils.xstr(row['Treatment'])
        self.combo_box_treatment.setCurrentText(treatment)

        sql = '''
            SELECT * FROM prescript WHERE 
                CaseKey = {0} AND 
                MedicineType IN ("穴道", "處置") AND 
                MedicineSet = {1} ORDER BY PrescriptKey
        '''.format(case_key, self.medicine_set)
        rows = database.select_record(sql)
        for row in rows:
            if row['MedicineName'] is None:
                continue

            self.append_null_treat()
            self.append_treat(row)

    # 處置內容變更
    def _combo_box_treat_changed(self):
        system_utils.set_keyboard_layout('英文')

        treatment = self.combo_box_treatment.currentText()

        if treatment == '':
            self.ui.tableWidget_treat.setRowCount(0)
            self.set_treat_ui()
        elif treatment == '電針治療':
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
            elif treat_type in ['乳癌照護', '肝癌照護', '肺癌照護', '大腸癌照護']:
                ins_care.set_cancer_treat(treatment)

    # 藥日變更重新批價
    def pres_days_changed(self):
        self._set_ins_care_pres_days()
        self.parent.calculate_ins_fees()

        treat_type = self.parent.tab_registration.ui.comboBox_treat_type.currentText()
        if treat_type in ['乳癌照護', '肝癌照護', '肺癌', '大腸癌'] and self.ui.comboBox_pres_days.currentText() == '':
            self.ui.comboBox_pres_days.setCurrentText('7')  # 至少七天藥

        self.ui.comboBox_pres_days.setFocus(True)

    def _set_ins_care_pres_days(self):
        treat_type = self.parent.tab_registration.ui.comboBox_treat_type.currentText()
        if treat_type not in ['乳癌照護', '肝癌照護', '肺癌', '大腸癌']:
            return

        pres_days = number_utils.get_integer(self.ui.comboBox_pres_days.currentText())

        medicine_set = 11
        ins_care = self.parent.tab_list[medicine_set]
        if ins_care is not None:
            if treat_type in ['乳癌照護', '肝癌照護', '肺癌照護', '大腸癌照護']:
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

    def _prescript_cell_clicked(self):
        system_utils.set_keyboard_layout('英文')

    def _prescript_item_selection_changed(self):
        self.ui.toolButton_remove_medicine.setEnabled(True)
        self.ui.toolButton_clear_medicine.setEnabled(True)
        self.ui.toolButton_dictionary.setEnabled(True)
        self.ui.toolButton_medicine_info.setEnabled(True)

        if (self.call_from != '醫師看診作業' and
                self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, '病歷資料', '病歷修正', self.user_name) != 'Y'):
            enabled = False
        elif self.ui.tableWidget_prescript.rowCount() <= 0:
            enabled = False
        else:
            enabled = True

        self.ui.toolButton_remove_medicine.setEnabled(enabled)
        self.ui.toolButton_clear_medicine.setEnabled(enabled)
        self.ui.toolButton_dictionary.setEnabled(enabled)

        medicine_key_item = self.ui.tableWidget_prescript.item(
            self.ui.tableWidget_prescript.currentRow(),
            prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey']
        )
        if medicine_key_item is None:
            return

        description = prescript_utils.get_medicine_description(self.database, medicine_key_item.text())
        if description is None:
            self.ui.toolButton_medicine_info.setEnabled(False)

    def _prescript_item_changed(self, item):
        if item is None:
            return

        col_no = item.column()
        if col_no == prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']:
            self._set_total_dosage()
            self._set_total_cost()

    def _set_total_dosage(self):
        total_dosage = prescript_utils.get_total_dosage(self.ui.tableWidget_prescript)
        self.ui.label_total_dosage.setText('總量: {0:.1f}'.format(total_dosage))

    def _set_total_cost(self):
        total_costs = self._calculate_total_costs()
        self.ui.label_total_costs.setText('({0:.1f})'.format(total_costs))

    def _check_total_dosage(self, current_row=None):
        if current_row is None:
            current_row = self.ui.tableWidget_prescript.currentRow()

        total_dosage = prescript_utils.get_total_dosage(self.ui.tableWidget_prescript)
        dosage_limitation = number_utils.get_integer(self.system_settings.field('劑量上限'))
        if dosage_limitation is None or dosage_limitation <= 0:  # 未設定, 不檢查
            return True

        if total_dosage <= dosage_limitation:  # 未超過劑量上限
            return True

        col_no = prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']
        self.ui.tableWidget_prescript.setCurrentCell(current_row, col_no)
        self.ui.tableWidget_prescript.setItem(
            current_row, col_no, QtWidgets.QTableWidgetItem('')
        )
        self._set_dosage_format(current_row, col_no)

        system_utils.show_message_box(
            QtWidgets.QMessageBox.Critical,
            '劑量檢查',
            '<font size="4" color="red"><b>給藥超過系統設定{dosage_limitation}克的劑量上限, 請重新調整劑量.</b></font>'.format(
                dosage_limitation=dosage_limitation,
            ),
            '請重新調整劑量, 或更改系統設定的劑量上限.'
        )
        total_dosage = prescript_utils.get_total_dosage(self.ui.tableWidget_prescript)
        self.ui.label_total_dosage.setText('總量: {0:.1f}'.format(total_dosage))

        return False

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
            try:
                dosage = number_utils.get_float(dosage_item.text())
            except ValueError:
                dosage = 0

            total_costs += dosage * cost

        return total_costs

    def _show_costs(self):
        pres_days = number_utils.get_integer(self.ui.comboBox_pres_days.currentText())
        if pres_days <= 0:
            pres_days = 1

        html = prescript_utils.get_costs_html(
            self.database, self.ui.tableWidget_prescript, pres_days,
            prescript_utils.INS_PRESCRIPT_COL_NO
        )
        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'html', None, html
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

    def _clear_medical_record(self):
        self.parent.clear_medical_record()

        if self.parent.clear_medical_record_option:
            self._clear_medicine()
            self._clear_treat()

            self.parent.ui.textEdit_symptom.setFocus()

    def _clear_medicine(self, warning=False):
        if self.ui.tableWidget_prescript.rowCount() <= 0:
            return

        if warning:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('清除處方資料')
            msg_box.setText("<font size='4' color='red'><b>確定清除全部的處方?</b></font>")
            msg_box.setInformativeText("注意！處方清除後, 將無法回復!")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            clear_medicine = msg_box.exec_()
            if clear_medicine:
                return

        self.ui.tableWidget_prescript.setRowCount(0)
        self.ui.comboBox_package.setCurrentText(None)
        self.ui.comboBox_pres_days.setCurrentText(None)
        self.ui.comboBox_instruction.setCurrentText(None)
        self.ui.toolButton_add_medicine.animateClick()

    def _clear_treat(self, warning=False):
        if self.combo_box_treatment.currentText() == '':
            return

        if warning:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('清除處置資料')
            msg_box.setText("<font size='4' color='red'><b>確定清除全部的處置?</b></font>")
            msg_box.setInformativeText("注意！處置清除後, 將無法回復!")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            clear_treat = msg_box.exec_()
            if clear_treat:
                return

        self.combo_box_treatment.setCurrentText('')

    def _show_acupuncture_point(self):
        dialog = dialog_acupuncture_point.DialogAcupuncturePoint(
            self, self.database,
            self.system_settings,
        )
        if not dialog.exec_():
            dialog.deleteLater()
            return

        acupuncture_point_list = dialog.acupuncture_point_list
        dialog.deleteLater()

        if len(acupuncture_point_list) <= 0:
            return

        self.combo_box_treatment.setCurrentText('針灸治療')
        row = {}
        row['MedicineType'] = '穴道'
        row['MedicineKey'] = None
        row['InsCode'] = None

        for acupuncture_point in acupuncture_point_list:
            row['MedicineName'] = acupuncture_point
            self.append_null_treat()
            self.append_treat(row)

    # 拷貝健保處方至自費處方
    def _copy_prescript(self):
        new_tab = self.parent.add_prescript_tab()
        new_tab.copy_from_ins_prescript(self.ui.tableWidget_prescript)

    def copy_from_self_prescript(self, table_widget_self_prescript):
        for row_no in range(table_widget_self_prescript.rowCount()):
            row = dict()
            medicine_key_item = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey'])
            if medicine_key_item is None:
                continue

            medicine_key = medicine_key_item.text()
            row['MedicineKey'] = medicine_key
            row['MedicineType'] = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineType']).text()
            row['Price'] = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price']).text()
            row['Amount'] = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']).text()
            row['InsCode'] = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['InsCode']).text()
            row['MedicineName'] = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']).text()
            row['Unit'] = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Unit']).text()
            dosage = table_widget_self_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']).text()

            if row['InsCode'] == '':
                row['InsCode'] = prescript_utils.get_medicine_field(
                    self.database, medicine_key, 'InsCode'
                )

            self.append_null_medicine()
            self.append_prescript(row, dosage)
            self._set_dosage_format(row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])

        self.ui.tableWidget_prescript.setCurrentCell(
            self.ui.tableWidget_prescript.rowCount()-1, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']
        )
        self.parent.tabWidget_prescript.setCurrentIndex(0)

    def _set_pharmacy(self):
        if self.ui.checkBox_pharmacy.isChecked():
            pharmacy_type = '申報'
        else:
            pharmacy_type = '不申報'

        self.parent.tab_registration.comboBox_pharmacy_type.setCurrentText(pharmacy_type)
        self.parent.calculate_ins_fees()
