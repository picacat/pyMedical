#!/usr/bin/env python3
# 輸入處方 2018.06.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import personnel_utils
from dialog import dialog_commission


# 主視窗
class DialogInputDrug(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputDrug, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        try:
            self.medicine_key = args[2]
        except IndexError:
            self.medicine_key = None

        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        if self.medicine_key is not None:
            self._edit_medicine()
            self._edit_commission()

        self._set_permission()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INPUT_DRUG, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()
        self.ui.lineEdit_medicine_name.setFocus()
        self.ui.lineEdit_medicine_code.setMaxLength(15)
        self.table_widget_commission = table_widget.TableWidget(self.ui.tableWidget_commission, self.database)
        self._set_table_width()

    def _set_table_width(self):
        width = [150, 120, 350]
        self.table_widget_commission.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.toolButton_add_commission.clicked.connect(self._add_commission)
        self.ui.toolButton_remove_commission.clicked.connect(self._remove_commission)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '處方資料', '更改抽成', self.user_name) != 'Y':
            self.ui.lineEdit_commission.setVisible(False)
            self.ui.label_commission.setVisible(False)
            self.ui.label_commission_hint.setVisible(False)
            self.ui.groupBox_commission.setVisible(False)

    # 設定 comboBox
    def _set_combo_box(self):
        sql = 'SELECT Unit FROM medicine GROUP BY Unit ORDER BY Unit'
        rows = self.database.select_record(sql)
        unit_list = [None, ]
        for row in rows:
            if row['Unit'] is None or str(row['Unit']).strip() == '':
                continue
            unit_list.append(str(row['Unit']).strip())

        ui_utils.set_combo_box(self.ui.comboBox_unit, unit_list)

        sql = '''
            SELECT MedicineMode FROM medicine WHERE
            (MedicineType != "穴道" AND MedicineType != "處置")
            GROUP BY MedicineMode ORDER BY MedicineMode
        '''
        rows = self.database.select_record(sql)
        medicine_mode_list = [None, ]
        for row in rows:
            if row['MedicineMode'] is None or str(row['MedicineMode']).strip() == '':
                continue
            medicine_mode_list.append(str(row['MedicineMode']).strip())

        ui_utils.set_combo_box(self.ui.comboBox_medicine_mode, medicine_mode_list)

    def _edit_medicine(self):
        sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(self.medicine_key)
        row = self.database.select_record(sql)[0]
        self.ui.lineEdit_medicine_code.setText(row['MedicineCode'])
        self.ui.lineEdit_input_code.setText(row['InputCode'])
        self.ui.lineEdit_medicine_name.setText(row['MedicineName'])
        self.ui.comboBox_unit.setCurrentText(row['Unit'])
        self.ui.comboBox_medicine_mode.setCurrentText(row['MedicineMode'])
        self.ui.lineEdit_ins_code.setText(row['InsCode'])
        self.ui.lineEdit_dosage.setText(string_utils.xstr(row['Dosage']))
        self.ui.lineEdit_medicine_alias.setText(row['MedicineAlias'])
        self.ui.lineEdit_location.setText(row['Location'])
        self.ui.lineEdit_in_price.setText(string_utils.xstr(row['InPrice']))
        self.ui.lineEdit_sale_price.setText(string_utils.xstr(row['SalePrice']))
        self.ui.lineEdit_quantity.setText(string_utils.xstr(row['Quantity']))
        self.ui.lineEdit_safe_quantity.setText(string_utils.xstr(row['SafeQuantity']))
        self.ui.lineEdit_commission.setText(string_utils.xstr(row['Commission']))
        try:
            self.ui.textEdit_description.setPlainText(string_utils.get_str(row['Description'], 'utf8'))
        except TypeError:
            pass

    def _edit_commission(self):
        sql = '''
            SELECT * FROM commission
            WHERE
                MedicineKey = {medicine_key}
            ORDER BY CommissionKey
        '''.format(
            medicine_key=self.medicine_key,
        )

        self.table_widget_commission.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        commission_row = [
           string_utils.xstr(row['Name']),
           string_utils.xstr(row['Commission']),
           string_utils.xstr(row['Remark']),
        ]

        for column in range(len(commission_row)):
            self.ui.tableWidget_commission.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(commission_row[column])
            )
            if column in [1]:
                self.ui.tableWidget_commission.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def accepted_button_clicked(self):
        if self.medicine_key is None:
            return

        self._save_medicine()
        self._save_commission()

    def _save_medicine(self):
        fields = [
            'MedicineCode', 'InputCode', 'MedicineName', 'Unit', 'MedicineMode', 'InsCode',
            'Dosage', 'MedicineAlias', 'Location', 'InPrice', 'SalePrice', 'Commission',
            'Quantity', 'SafeQuantity',
            'Description',
        ]
        data = [
            self.ui.lineEdit_medicine_code.text(),
            self.ui.lineEdit_input_code.text(),
            self.ui.lineEdit_medicine_name.text(),
            self.ui.comboBox_unit.currentText(),
            self.ui.comboBox_medicine_mode.currentText(),
            self.ui.lineEdit_ins_code.text(),
            self.ui.lineEdit_dosage.text(),
            self.ui.lineEdit_medicine_alias.text(),
            self.ui.lineEdit_location.text(),
            self.ui.lineEdit_in_price.text(),
            self.ui.lineEdit_sale_price.text(),
            self.ui.lineEdit_commission.text(),
            self.ui.lineEdit_quantity.text(),
            self.ui.lineEdit_safe_quantity.text(),
            self.ui.textEdit_description.toPlainText(),
        ]

        self.database.update_record('medicine', fields, 'MedicineKey',
                                    self.medicine_key, data)

    def _save_commission(self):
        self.database.exec_sql('DELETE FROM commission WHERE MedicineKey = {0}'.format(self.medicine_key))
        fields = ['MedicineKey', 'Name', 'Commission', 'Remark']

        for row_no in range(self.ui.tableWidget_commission.rowCount()):
            name = self.ui.tableWidget_commission.item(row_no, 0).text()
            commission = self.ui.tableWidget_commission.item(row_no, 1).text()
            remark = self.ui.tableWidget_commission.item(row_no, 2).text()

            data = [self.medicine_key, name, commission, remark]

            self.database.insert_record('commission', fields, data)

    def _add_commission(self):
        person_list = personnel_utils.get_personnel(self.database, '全部')
        for row_no in range(self.ui.tableWidget_commission.rowCount()):
            name = self.ui.tableWidget_commission.item(row_no, 0).text()
            person_list.remove(name)

        dialog = dialog_commission.DialogCommission(self, self.database, self.system_settings, person_list)
        if not dialog.exec_():
            dialog.deleteLater()
            return

        name = dialog.ui.comboBox_person.currentText()
        commission = dialog.ui.lineEdit_commission.text()
        remark = dialog.ui.lineEdit_remark.text()
        dialog.deleteLater()

        row_no = self.ui.tableWidget_commission.rowCount()
        self.ui.tableWidget_commission.insertRow(row_no)

        row = [name, commission, remark]
        for column in range(len(row)):
            self.ui.tableWidget_commission.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(string_utils.xstr(row[column]))
            )
            if column in [1]:
                self.ui.tableWidget_commission.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _remove_commission(self):
        current_row = self.ui.tableWidget_commission.currentRow()
        self.ui.tableWidget_commission.removeRow(current_row)
