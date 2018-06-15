#!/usr/bin/env python3
# 輸入處方 2018.06.15
#coding: utf-8

from PyQt5 import QtWidgets
from libs import ui_settings
from libs import system
from libs import strings


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

        self._set_ui()
        self._set_signal()
        if self.medicine_key is not None:
            self._edit_medicine()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_INPUT_DRUG, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()
        self.ui.lineEdit_medicine_name.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    # 設定 comboBox
    def _set_combo_box(self):
        sql = 'SELECT Unit FROM medicine GROUP BY Unit ORDER BY Unit'
        rows = self.database.select_record(sql)
        unit_list = []
        for row in rows:
            if row['Unit'] is None or str(row['Unit']).strip() == '':
                continue
            unit_list.append(str(row['Unit']).strip())

        ui_settings.set_combo_box(self.ui.comboBox_unit, unit_list)

        sql = 'SELECT MedicineMode FROM medicine GROUP BY MedicineMode ORDER BY MedicineMode'
        rows = self.database.select_record(sql)
        medicine_mode_list = []
        for row in rows:
            if row['MedicineMode'] is None or str(row['MedicineMode']).strip() == '':
                continue
            medicine_mode_list.append(str(row['MedicineMode']).strip())

        ui_settings.set_combo_box(self.ui.comboBox_medicine_mode, medicine_mode_list)

    def _edit_medicine(self):
        sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(self.medicine_key)
        row = self.database.select_record(sql)[0]
        self.ui.lineEdit_medicine_code.setText(row['MedicineCode'])
        self.ui.lineEdit_input_code.setText(row['InputCode'])
        self.ui.lineEdit_medicine_name.setText(row['MedicineName'])
        self.ui.comboBox_unit.setCurrentText(row['Unit'])
        self.ui.comboBox_medicine_mode.setCurrentText(row['MedicineMode'])
        self.ui.lineEdit_ins_code.setText(row['InsCode'])
        self.ui.lineEdit_dosage.setText(strings.xstr(row['Dosage']))
        self.ui.lineEdit_medicine_alias.setText(row['MedicineAlias'])
        self.ui.lineEdit_location.setText(row['Location'])
        self.ui.lineEdit_in_price.setText(strings.xstr(row['InPrice']))
        self.ui.lineEdit_sale_price.setText(strings.xstr(row['SalePrice']))
        self.ui.lineEdit_quantity.setText(strings.xstr(row['Quantity']))
        self.ui.lineEdit_safe_quantity.setText(strings.xstr(row['SafeQuantity']))
        self.ui.textEdit_description.setText(strings.get_str(row['Description'], 'utf8'))

    def accepted_button_clicked(self):
        if self.medicine_key is None:
            return

        fields = [
            'MedicineCode', 'InputCode', 'MedicineName', 'Unit', 'MedicineMode', 'InsCode',
            'Dosage', 'MedicineAlias', 'Location', 'InPrice', 'SalePrice', 'Quantity', 'SafeQuantity',
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
            self.ui.lineEdit_quantity.text(),
            self.ui.lineEdit_safe_quantity.text(),
            self.ui.textEdit_description.toPlainText(),
        ]

        self.database.update_record('medicine', fields, 'MedicineKey',
                                    self.medicine_key, data)
