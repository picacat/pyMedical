#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton

from classes import table_widget
from dialog import dialog_input_medicine
from dialog import dialog_rich_text

from libs import ui_utils
from libs import db_utils
from libs import string_utils
from libs import nhi_utils
from libs import number_utils
from libs import prescript_utils
from libs import system_utils
from libs import case_utils
from libs import charge_utils
from libs import personnel_utils


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
        self.call_from = args[4]
        self.case_date = self.parent.medical_record['CaseDate']
        self.ui = None
        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        if self.case_key is not None:
            self._read_prescript()

        self._set_permission()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_SELF_PRESCRIPT_RECORD, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        self.ui.tableWidget_prescript.setDragEnabled(True)
        self.ui.tableWidget_prescript.setAcceptDrops(True)

        self.read_only_columns = [
            prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
            prescript_utils.SELF_PRESCRIPT_COL_NO['Info'],
        ]
        if personnel_utils.get_permission(self.database, '病歷資料', '修改單價', self.user_name) != 'Y':
            self.read_only_columns.append(
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price']
            )

        self._set_table_width()
        self._set_combo_box()
        self._set_discount_visible()

    def _set_discount_visible(self):
        if self.system_settings.field('自費折扣方式') == '個別折扣':
            return

        enabled = False
        self.ui.label_discount.setVisible(enabled)
        self.ui.spinBox_discount_rate.setVisible(enabled)
        self.ui.label_percent.setVisible(enabled)
        self.ui.lineEdit_discount_fee.setVisible(enabled)

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add_medicine.clicked.connect(self.append_null_medicine)
        self.ui.toolButton_remove_medicine.clicked.connect(self.remove_medicine)
        self.ui.toolButton_dictionary.clicked.connect(self._open_dictionary)
        self.ui.toolButton_show_costs.clicked.connect(self._show_costs)
        self.ui.toolButton_medicine_info.clicked.connect(self._show_medicine_description)
        self.ui.toolButton_copy_to_ins.clicked.connect(self._copy_to_ins_prescript)
        self.ui.toolButton_copy.clicked.connect(self._copy_prescript)
        self.ui.toolButton_clear_medicine.clicked.connect(lambda:self._clear_medicine(warning=True))

        self.ui.tableWidget_prescript.keyPressEvent = self._table_widget_prescript_key_press
        self.ui.tableWidget_prescript.itemChanged.connect(self._prescript_item_changed)
        self.ui.tableWidget_prescript.itemSelectionChanged.connect(self._prescript_item_selection_changed)
        self.ui.tableWidget_prescript.cellClicked.connect(self._prescript_cell_clicked)

        self.ui.comboBox_pres_days.currentTextChanged.connect(self.pres_days_changed)
        self.ui.tableWidget_prescript.dropEvent = self.prescript_drop_event
        self.ui.spinBox_discount_rate.valueChanged.connect(self._calculate_discount)
        self.ui.lineEdit_discount_fee.textChanged.connect(self._discount_fee_changed)

    def _set_permission(self):
        # if self.call_from == '醫師看診作業':
        #     return

        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '醫師看診作業', '病歷登錄', self.user_name) == 'Y':
            return

        if personnel_utils.get_permission(self.database, '病歷資料', '病歷修正', self.user_name) == 'Y':
            return

        self.ui.toolButton_add_medicine.setEnabled(False)
        self.ui.toolButton_remove_medicine.setEnabled(False)
        self.ui.toolButton_dictionary.setEnabled(False)
        self.ui.toolButton_show_costs.setEnabled(False)
        self.ui.toolButton_medicine_info.setEnabled(False)
        self.ui.toolButton_copy.setEnabled(False)
        self.ui.toolButton_clear_medicine.setEnabled(False)
        self.ui.toolButton_copy_to_ins.setEnabled(False)

        self.ui.comboBox_package.setEnabled(False)
        self.ui.comboBox_pres_days.setEnabled(False)
        self.ui.comboBox_instruction.setEnabled(False)

        self.ui.spinBox_discount_rate.setEnabled(False)

        self.ui.tableWidget_prescript.setEnabled(False)
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            for col_no in range(self.ui.tableWidget_prescript.columnCount()):
                item = self.ui.tableWidget_prescript.item(row_no, col_no)
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
            source_row, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']
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

        self._adjust_prescript_column(target_row)

        # medicine_key_item = prescript_row[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']]
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

        table_widget.setCurrentCell(move_row, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName'])

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_package, nhi_utils.PACKAGE, None)
        ui_utils.set_combo_box(self.ui.comboBox_pres_days, nhi_utils.SELF_PRESDAYS, None)
        ui_utils.set_instruction_combo_box(self.database, self.ui.comboBox_instruction)

    def _table_widget_prescript_key_press(self, event):
        system_utils.set_keyboard_layout('英文')

        key = event.key()
        current_row = self.ui.tableWidget_prescript.currentRow()
        current_column = self.ui.tableWidget_prescript.currentColumn()

        if key == QtCore.Qt.Key_Delete:
            self.remove_medicine()
        elif key == QtCore.Qt.Key_Up:
            if self.ui.tableWidget_prescript.item(
                    current_row, prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']) is None:
                self.ui.tableWidget_prescript.removeRow(current_row)
                return
            if current_column in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                self._set_dosage_format(current_row, current_column)
        elif key == QtCore.Qt.Key_Down:
            if (current_row == self.ui.tableWidget_prescript.rowCount() - 1 and
                    self.ui.tableWidget_prescript.item(
                        current_row, prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']) is not None):
                self.append_null_medicine()
            if current_column in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                self._set_dosage_format(current_row, current_column)
        elif key == QtCore.Qt.Key_Return or key == QtCore.Qt.Key_Enter:
            if current_column == prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']:
                self.open_medicine_dialog()
            elif current_column in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
            ]:
                self._set_dosage_format(current_row, current_column)
                if current_row < self.ui.tableWidget_prescript.rowCount() - 1:
                    if current_column == prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']:
                        self.ui.tableWidget_prescript.setCurrentCell(
                            current_row+1, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']
                        )
                    elif current_column == prescript_utils.SELF_PRESCRIPT_COL_NO['Price']:
                        self.ui.tableWidget_prescript.setCurrentCell(
                            current_row+1, prescript_utils.SELF_PRESCRIPT_COL_NO['Price']
                        )
        self._adjust_prescript_column(current_row)

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

        keyword = item.text()
        keyword = string_utils.replace_ascii_char(['\\', '"', '\''], keyword)
        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName like "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}") 
        '''.format(keyword)
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
                prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey'], medicine_key):
            return

        try:
            price = string_utils.get_formatted_str('單價', row['SalePrice'])
        except Exception:
            try:
                price = string_utils.get_formatted_str('單價', row['Price'])
            except Exception:
                price = string_utils.get_formatted_str('單價', None)

        try:
            amount = string_utils.get_formatted_str('單價', row['Amount'])
        except Exception:
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
            [prescript_utils.SELF_PRESCRIPT_COL_NO['Info'], info],
        ]

        self.set_prescript(prescript_row)
        db_utils.increment_hit_rate(self.database, 'medicine', 'MedicineKey', medicine_key)

    def set_prescript(self, row):
        row_no = self.ui.tableWidget_prescript.currentRow()
        for item in row:
            self.ui.tableWidget_prescript.setItem(
                row_no, item[0], QtWidgets.QTableWidgetItem(item[1])
            )

        self._adjust_prescript_column(row_no)

        # medicine_key = medical_row[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']][1]
        # database._add_prescript_info_button(row_no, medicine_key)
        self.ui.tableWidget_prescript.resizeRowsToContents()

    def _set_table_width(self):
        medicine_width = [
            70,
            100, 100, 100, 100, 100, 100, 100, 100, 100,
            270, 60, 50, 70, 90, 90, 10,
        ]
        self.table_widget_prescript.set_table_heading_width(medicine_width)

    def _read_prescript(self):
        self._read_dosage()
        self._read_medicine()
        self._calculate_total_dosage()
        self._calculate_total_costs()
        self._calculate_self_total_fee()

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

        row = row[0]
        self.ui.comboBox_package.setCurrentText(string_utils.xstr(row['Packages']))
        self.ui.comboBox_pres_days.setCurrentText(string_utils.xstr(row['Days']))
        self.ui.comboBox_instruction.setCurrentText(string_utils.xstr(row['Instruction']))

        self_total_fee = number_utils.get_integer(row['SelfTotalFee'])
        discount_rate = number_utils.get_integer(row['DiscountRate'])
        discount_fee = number_utils.get_integer(row['DiscountFee'])
        total_fee = number_utils.get_integer(row['TotalFee'])

        self.ui.spinBox_discount_rate.setValue(discount_rate)
        self.ui.lineEdit_discount_fee.setText(string_utils.xstr(discount_fee))
        self.ui.lineEdit_self_total_fee.setText(string_utils.xstr(self_total_fee))
        self.ui.lineEdit_total_fee.setText(string_utils.xstr(total_fee))
        # database.ui.label_self_total_fee.setText('自費合計: ${0:,}'.format(self_total_fee))
        # database.ui.label_total_fee.setText('應收金額: ${0:,}'.format(total_fee))

    def _read_medicine(self):
        sql = '''
            SELECT prescript.*, medicine.InPrice FROM prescript 
                LEFT JOIN medicine ON prescript.MedicineKey = medicine.MedicineKey
            WHERE 
                CaseKey = {case_key} AND 
                prescript.MedicineSet = {medicine_set}
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(
            case_key=self.case_key,
            medicine_set=self.medicine_set,
        )
        self.table_widget_prescript.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        medicine_key = row['MedicineKey']
        dosage = string_utils.get_formatted_str(self.system_settings.field('劑量形式'), row['Dosage'])
        price = string_utils.get_formatted_str('單價', row['Price'])
        amount = string_utils.get_formatted_str('單價', row['Amount'])
        in_price = number_utils.get_float(row['InPrice'])
        if in_price > 0:
            in_price_mark = '$'
        else:
            in_price_mark = ''

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
            in_price_mark,
        ]

        for col_no in range(len(prescript_row)):
            self.ui.tableWidget_prescript.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(prescript_row[col_no])
            )

        self._adjust_prescript_column(row_no)

        # database._add_prescript_info_button(row_no, medicine_key)

    def _add_prescript_info_button(self, row_no, medicine_key):
        description = prescript_utils.get_medicine_description(self.database, medicine_key)

        button = QtWidgets.QPushButton(self.ui.tableWidget_prescript)
        button.setIcon(QtGui.QIcon('./icons/gtk-info.svg'))
        button.setFlat(True)
        if description is None:
            button.setEnabled(False)

        button.clicked.connect(lambda : self._show_medicine_description(description))
        self.ui.tableWidget_prescript.setCellWidget(
            row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Info'], button)

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
        self._calculate_self_total_fee()

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

    # 刪除處方
    def _remove_sale_price(self):
        row_no = self.ui.tableWidget_prescript.currentRow()

        col_no = prescript_utils.SELF_PRESCRIPT_COL_NO['Price']
        self.ui.tableWidget_prescript.setItem(
            row_no, col_no,
            QtWidgets.QTableWidgetItem('0.0')
        )
        self._adjust_prescript_column(row_no)

        col_no = prescript_utils.SELF_PRESCRIPT_COL_NO['Amount']
        self.ui.tableWidget_prescript.setItem(
            row_no, col_no,
            QtWidgets.QTableWidgetItem('0.0')
        )
        self._adjust_prescript_column(row_no)

        self.parent.calculate_self_fees()
        self._calculate_total_dosage()
        self._calculate_total_costs()
        self._calculate_self_total_fee()

    def save_prescript(self):
        medicine_set = self.medicine_set
        if medicine_set >= 3:  # 有第三帖藥, 檢查前面的藥帖是否空白
            for i in range(medicine_set, 1, -1):
                medicine_set = i
                sql = '''
                    SELECT MedicineSet FROM prescript
                    WHERE
                        CaseKey = {case_key} AND
                        MedicineSet = {medicine_set}
                    LIMIT 1
                '''.format(
                    case_key=self.case_key,
                    medicine_set=medicine_set-1,
                )

                rows = self.database.select_record(sql)
                if len(rows) > 0:
                    break

        self._save_dosage(medicine_set)
        self._save_medicine(medicine_set)

    def _save_dosage(self, medicine_set):
        fields = [
            'CaseKey', 'MedicineSet', 'Packages', 'Days', 'Instruction',
            'SelfTotalFee', 'DiscountRate', 'DiscountFee', 'TotalFee',
        ]
        self_total_fee = self._get_self_total_fee()
        total_fee = self._get_total_fee()
        data = [
            string_utils.xstr(self.case_key),
            string_utils.xstr(medicine_set),
            self.ui.comboBox_package.currentText(),
            self.ui.comboBox_pres_days.currentText(),
            self.ui.comboBox_instruction.currentText(),
            self_total_fee,
            self.ui.spinBox_discount_rate.value(),
            self.ui.lineEdit_discount_fee.text(),
            total_fee,
        ]

        sql = '''
            DELETE FROM dosage
            WHERE
                CaseKey = {case_key} AND
                MedicineSet = {medicine_set}
        '''.format(
            case_key=self.case_key,
            medicine_set=medicine_set,
        )
        self.database.exec_sql(sql)
        self.database.insert_record('dosage', fields, data)

    def _save_medicine(self, medicine_set):
        prescript_data_set = []
        for i in range(self.ui.tableWidget_prescript.rowCount()):
            prescript_row = []
            for j in range(self.ui.tableWidget_prescript.columnCount()):
                try:
                    prescript_row.append(self.ui.tableWidget_prescript.item(i, j).text())
                except AttributeError:
                    prescript_row.append(None)

            prescript_data_set.append(prescript_row)

        self.delete_not_exists_prescript(prescript_data_set)

        prescript_no = 0  # 重編 PrescriptNo
        for items in prescript_data_set:
            if items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']] is None:
                continue

            if items[prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']] == '':
                items[prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']] = None

            prescript_no += 1
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptNo']] = str(prescript_no)

            if items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptKey']] == '-1':
                self.insert_prescript(items, medicine_set)
            else:
                self.update_prescript(items, medicine_set)

    # 刪除不在tableWidget內的處方
    def delete_not_exists_prescript(self, prescript_data_set):
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
    def insert_prescript(self, items, medicine_set=None):
        if medicine_set is None:
            medicine_set = items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineSet']]

        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate',
            'MedicineSet', 'MedicineType', 'MedicineKey', 'InsCode', 'DosageMode',
            'MedicineName', 'Dosage', 'Unit', 'Instruction',
            'Price', 'Amount',
        ]

        data = [
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['PrescriptNo']],
            self.case_key,
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['CaseDate']],
            medicine_set,
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
    def update_prescript(self, items, medicine_set=None):
        if medicine_set is None:
            medicine_set = items[prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineSet']]

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
            self.case_key,
            items[prescript_utils.SELF_PRESCRIPT_COL_NO['CaseDate']],
            medicine_set,
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
    def copy_past_prescript(self, case_key, medicine_set=None):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        if medicine_set is None:
            medicine_set = self.medicine_set

        pres_days = case_utils.get_pres_days(self.database, case_key, medicine_set)
        packages = case_utils.get_packages(self.database, case_key, medicine_set)
        instruction = case_utils.get_instruction(self.database, case_key, medicine_set)
        discount_rate = case_utils.get_discount_rate(self.database, case_key, medicine_set)

        medicine_type_script = ''
        if medicine_set == 1:
            medicine_type_script = ' AND MedicineType IN ("單方", "複方") '  # 拷貝健保至自費, 只讀取健保藥
        sql = '''
            SELECT * FROM prescript 
            WHERE 
                CaseKey = {case_key} AND 
                MedicineSet = {medicine_set} 
                {medicine_type_script}
            ORDER BY PrescriptKey
        '''.format(
            case_key=case_key,
            medicine_set=medicine_set,
            medicine_type_script=medicine_type_script,
        )
        rows = self.database.select_record(sql)
        for row_no, row in zip(range(len(rows)), rows):
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'])

        self.ui.comboBox_pres_days.setCurrentText(string_utils.xstr(pres_days))
        self.ui.comboBox_package.setCurrentText(string_utils.xstr(packages))
        self.ui.comboBox_instruction.setCurrentText(instruction)
        self.ui.spinBox_discount_rate.setValue(discount_rate)

        self.ui.tableWidget_prescript.resizeRowsToContents()

    # 藥日變更重新批價
    def pres_days_changed(self):
        self._calculate_self_total_fee()
        self.parent.calculate_self_fees()

    def _prescript_item_selection_changed(self):
        self.ui.toolButton_remove_medicine.setEnabled(True)
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
        self.ui.toolButton_dictionary.setEnabled(enabled)

        medicine_key_item = self.ui.tableWidget_prescript.item(
            self.ui.tableWidget_prescript.currentRow(),
            prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineKey']
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
        if col_no not in [
            prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
            prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
        ]:
            return

        row_no = item.row()
        self._calculate_total_price(row_no, col_no, item)
        self._adjust_prescript_column_align(row_no)
        self.parent.calculate_self_fees()

        self._calculate_total_dosage()
        self._calculate_total_costs()
        self._calculate_self_total_fee()

    # 拷貝過去病歷的處方
    def copy_host_prescript(self, database, case_key, medicine_set=None):
        self.ui.tableWidget_prescript.clearContents()
        self.ui.tableWidget_prescript.setRowCount(0)
        if medicine_set is None:
            medicine_set = self.medicine_set

        pres_days = case_utils.get_host_pres_days(database, case_key, medicine_set)
        packages = case_utils.get_host_packages(database, case_key, medicine_set)
        instruction = case_utils.get_host_instruction(database, case_key, medicine_set)

        medicine_type_script = ''
        if medicine_set == 1:
            medicine_type_script = ' AND MedicineType IN ("單方", "複方") '  # 拷貝健保至自費, 只讀取健保藥
        sql = '''
            SELECT * FROM prescript 
            WHERE 
                CaseKey = {case_key} AND 
                MedicineSet = {medicine_set} 
                {medicine_type_script}
            ORDER BY PrescriptKey
        '''.format(
            case_key=case_key,
            medicine_set=medicine_set,
            medicine_type_script=medicine_type_script,
        )
        rows = database.select_record(sql)
        for row_no, row in zip(range(len(rows)), rows):
            if row['MedicineName'] is None:
                continue

            self.append_null_medicine()
            self.append_prescript(row, row['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price'])
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'])

        self.ui.comboBox_pres_days.setCurrentText(string_utils.xstr(pres_days))
        self.ui.comboBox_package.setCurrentText(string_utils.xstr(packages))
        self.ui.comboBox_instruction.setCurrentText(instruction)

        self.ui.tableWidget_prescript.resizeRowsToContents()

    def _calculate_total_price(self, row_no, col_no, item):
        dosage = self.ui.tableWidget_prescript.item(
            row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']
        )
        sale_price = self.ui.tableWidget_prescript.item(
            row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price']
        )

        if col_no == prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']:
            dosage = item
        elif col_no == prescript_utils.SELF_PRESCRIPT_COL_NO['Price']:
            sale_price = item

        if dosage is None:
            dosage = 0
        else:
            dosage = dosage.text()

        if sale_price is None:
            sale_price = 0
        else:
            sale_price = sale_price.text()

        try:
            sale_price = number_utils.get_float(sale_price)
        except ValueError:
            sale_price = 0
        try:
            dosage = number_utils.get_float(dosage)
        except ValueError:
            dosage = 0

        subtotal = dosage * sale_price
        self.ui.tableWidget_prescript.setItem(
            row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
            QtWidgets.QTableWidgetItem(string_utils.get_formatted_str('單價', subtotal))
        )

    # 調整欄位對齊
    def _adjust_prescript_column(self, row_no):
        self._adjust_prescript_column_align(row_no)
        self._set_prescript_read_only_column(row_no)

    # 調整欄位對齊
    def _adjust_prescript_column_align(self, row_no):
        for col_no in range(self.ui.tableWidget_prescript.columnCount()):
            item = self.ui.tableWidget_prescript.item(row_no, col_no)
            if item is None:
                continue

            if col_no in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Price'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'],
            ]:
                item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif col_no in [
                prescript_utils.SELF_PRESCRIPT_COL_NO['Unit'],
                prescript_utils.SELF_PRESCRIPT_COL_NO['Info'],
            ]:
                item.setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

    # 調整欄位對齊
    def _set_prescript_read_only_column(self, row_no):
        self.read_only_columns.sort()
        for col_no in self.read_only_columns:
            item = self.ui.tableWidget_prescript.item(row_no, col_no)
            if item is None:
                continue

            item.setFlags(QtCore.Qt.ItemIsEnabled)

    def _calculate_total_dosage(self):
        total_dosage = 0.0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            medicine_name = self.ui.tableWidget_prescript.item(
                row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']
            )
            if medicine_name is not None and medicine_name.text() == '優待':
                continue

            item = self.ui.tableWidget_prescript.item(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])
            if item is None:
                continue

            try:
                dosage = number_utils.get_float(item.text())
            except ValueError:
                item.setText(None)
                continue

            total_dosage += dosage

        self.ui.label_total_dosage.setText('總量: {0:.1f}'.format(total_dosage))

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

        self.ui.label_total_costs.setText('({0:.1f})'.format(total_costs))

    def _calculate_self_total_fee(self):
        pres_days = number_utils.get_integer(self.ui.comboBox_pres_days.currentText())
        if pres_days <= 0:
            pres_days = 1

        self_total_fee = 0
        for row_no in range(self.ui.tableWidget_prescript.rowCount()):
            item = self.ui.tableWidget_prescript.item(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'])
            if item is None:
                continue

            try:
                amount = number_utils.get_float(item.text())
            except ValueError:
                item.setText(None)
                continue

            subtotal = charge_utils.get_subtotal_fee(amount, pres_days)
            self_total_fee += subtotal

        discount_fee = number_utils.get_integer(self.ui.lineEdit_discount_fee.text())
        total_fee = self_total_fee - discount_fee
        self.ui.lineEdit_self_total_fee.setText(string_utils.xstr(self_total_fee))
        self.ui.lineEdit_total_fee.setText(string_utils.xstr(total_fee))
        self._calculate_discount()

    def _get_self_total_fee(self):
        return number_utils.get_integer(self.ui.lineEdit_self_total_fee.text())

    def _get_total_fee(self):
        return number_utils.get_integer(self.ui.lineEdit_total_fee.text())

    def _open_dictionary(self):
        self.parent.open_dictionary(self.medicine_set, '自費處方')

    def _show_costs(self):
        pres_days = number_utils.get_integer(self.ui.comboBox_pres_days.currentText())
        if pres_days <= 0:
            pres_days = 1

        html = prescript_utils.get_costs_html(
            self.database, self.ui.tableWidget_prescript, pres_days,
            prescript_utils.SELF_PRESCRIPT_COL_NO
        )
        dialog = dialog_rich_text.DialogRichText(
            self, self.database, self.system_settings,
            'html', None, html
        )
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

    def _prescript_cell_clicked(self):
        system_utils.set_keyboard_layout('英文')

    def _calculate_discount(self):
        self_total_fee = self._get_self_total_fee()
        discount_fee = charge_utils.get_discount_fee(
            self.system_settings, self_total_fee, self.ui.spinBox_discount_rate.value()
        )

        self.ui.lineEdit_discount_fee.setText(string_utils.xstr(discount_fee))

    def _discount_fee_changed(self):
        self_total_fee = self._get_self_total_fee()
        discount_fee = number_utils.get_integer(self.ui.lineEdit_discount_fee.text())
        total_fee = self_total_fee - discount_fee

        # database.ui.label_total_fee.setText('應收金額: ${0:,}'.format(
        #     number_utils.get_integer(total_fee)
        # ))
        self.ui.lineEdit_total_fee.setText(string_utils.xstr(total_fee))
        self.parent.calculate_self_fees()

    # 拷貝自費處方至健保處方
    def _copy_to_ins_prescript(self):
        ins_tab = self.parent.tab_list[0]
        if ins_tab is None:
            return

        ins_tab.copy_from_self_prescript(self.ui.tableWidget_prescript)

    # 拷貝自費處方至新增的自費處方
    def _copy_prescript(self):
        new_tab = self.parent.add_prescript_tab()
        new_tab.copy_from_self_prescript(self.ui.tableWidget_prescript)

    def copy_from_ins_prescript(self, table_widget_ins_prescript):
        for row_no in range(table_widget_ins_prescript.rowCount()):
            row = dict()
            medicine_key_item = table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey'])
            if medicine_key_item is None:
                continue

            medicine_key = medicine_key_item.text()
            row['MedicineKey'] = medicine_key
            row['MedicineType'] = table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineType']).text()
            row['Price'] = prescript_utils.get_medicine_field(
                self.database, medicine_key, 'SalePrice'
            )
            row['Amount'] = None
            row['InsCode'] = table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['InsCode']).text()
            row['MedicineName'] = table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName']).text()
            row['Unit'] = table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Unit']).text()
            dosage = table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage']).text()

            self.append_null_medicine()
            self.append_prescript(row, dosage)
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])

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

            self.append_null_medicine()
            self.append_prescript(row, dosage)
            self._set_dosage_format(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage'])

