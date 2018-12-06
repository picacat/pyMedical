#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import prescript_utils


# 主視窗
class DialogInputMedicine(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputMedicine, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.medicine_type = args[2]
        self.medicine_set = args[3]
        self.table_widget_prescript = args[4]
        self.input_code = self.table_widget_prescript.currentItem().text()

        self.settings = QSettings('__settings.ini', QSettings.IniFormat)
        self.ui = None
        self.medicine_key = None

        self._set_ui()
        self._set_signal()
        self._set_table_width()
        self.read_dictionary()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.settings.setValue("dialog_medicine_size", self.size())
        self.settings.setValue("dialog_medicine_pos", self.pos())
        if self.medicine_key is None:
            self.table_widget_prescript.currentItem().setText(self.input_code)
        else:
            if self.medicine_type == '健保處置':
                self.add_treat()
            else:
                self.add_medicine()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INPUT_MEDICINE, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        system_utils.set_theme(self.ui, self.system_settings)

        self.ui.resize(self.settings.value("dialog_medicine_size", QSize(635, 802)))
        self.ui.move(self.settings.value("dialog_medicine_pos", QPoint(205, 220)))

        self.table_widget_medicine = table_widget.TableWidget(self.ui.tableWidget_medicine, self.database)
        self.table_widget_medicine.set_column_hidden([0])

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Save).setText('選取')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText('關閉')

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.buttonBox.rejected.connect(self.rejected_button_clicked)
        self.ui.tableWidget_medicine.clicked.connect(self.accepted_button_clicked)

    # 設定欄位寬度
    def _set_table_width(self):
        medicine_width = [100, 60, 240, 60, 80, 110]
        self.table_widget_medicine.set_table_heading_width(medicine_width)

    def accepted_button_clicked(self):
        self.medicine_key = self.table_widget_medicine.field_value(0)
        self.close()

    def rejected_button_clicked(self):
        self.medicine_key = None
        self.close()

    def reject(self):
        self.medicine_key = None
        self.close()

    def read_dictionary(self):
        if self.medicine_type == '健保藥品':
            medicine_type = 'AND (MedicineType in ("單方", "複方", "成方"))'
        elif self.medicine_type == '所有藥品':
            medicine_type = 'AND (MedicineType in ("單方", "複方", "水藥", "外用", "高貴", "成方"))'
        elif self.medicine_type == '健保處置':
            if self.parent.combo_box_treatment.currentText() in nhi_utils.ACUPUNCTURE_TREAT:
                medicine_type = 'AND (MedicineType in ("穴道", "成方"))'
            elif self.parent.combo_box_treatment.currentText() in nhi_utils.MASSAGE_TREAT:
                medicine_type = 'AND (MedicineType in ("處置", "成方"))'
            else:
                medicine_type = 'AND (MedicineType in ("穴道", "處置", "成方"))'
        else:
            medicine_type = ''

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName LIKE "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}")
            {1}
            ORDER BY FIELD(MedicineType, "單方", "複方", "水藥", "外用", "高貴", "穴道", "處置", "成方"), 
                     LENGTH(MedicineName), 
            CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''.format(self.input_code, medicine_type)
        self.table_widget_medicine.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        if self.medicine_type == '健保藥品':
            remark = string_utils.xstr(row['InsCode'])
        else:
            remark = None

        medicine_row = [
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['Unit']),
            string_utils.get_formatted_str('單價', row['SalePrice']),
            remark
        ]

        for column in range(len(medicine_row)):
            self.ui.tableWidget_medicine.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medicine_row[column])
            )
            align = QtCore.Qt.AlignLeft
            if column in [3]:
                align = QtCore.Qt.AlignCenter
            elif column in [4]:
                align = QtCore.Qt.AlignRight

            self.ui.tableWidget_medicine.item(row_no, column).setTextAlignment(align | QtCore.Qt.AlignVCenter)

    def add_medicine(self):
        in_medicine_key = self.table_widget_medicine.field_value(0)
        if prescript_utils.check_prescript_exist(
                self.parent.ui.tableWidget_prescript, 6, in_medicine_key):
            return

        prescript_row = [
            [0, '-1'],
            [1, string_utils.xstr(self.table_widget_prescript.currentRow()+1)],
            [2, string_utils.xstr(self.parent.case_key)],
            [3, string_utils.xstr(self.parent.case_date)],
            [4, string_utils.xstr(self.medicine_set)],
            [5, self.table_widget_medicine.field_value(1)],
            [6, self.table_widget_medicine.field_value(0)],
            [7, self.table_widget_medicine.field_value(5)],
            [8, self.system_settings.field('劑量模式')],
            [9, self.table_widget_medicine.field_value(2)],
            [10, None],
            [11, self.table_widget_medicine.field_value(3)],
            [12, None],
            [13, self.table_widget_medicine.field_value(4)],
            [14, None],
        ]

        self.parent.set_prescript(prescript_row)
        if self.medicine_set == 1:
            self.parent.set_default_pres_days()

        self.parent.append_null_medicine()

    def add_treat(self):
        in_medicine_key = self.table_widget_medicine.field_value(0)
        if prescript_utils.check_prescript_exist(
                self.parent.ui.tableWidget_treat, 5, in_medicine_key):
            return

        treat_rec = [
            [0, '-1'],
            [1, string_utils.xstr(self.parent.case_key)],
            [2, string_utils.xstr(self.parent.case_date)],
            [3, string_utils.xstr(self.medicine_set)],
            [4, self.table_widget_medicine.field_value(1)],
            [5, self.table_widget_medicine.field_value(0)],
            [6, self.table_widget_medicine.field_value(5)],
            [7, self.table_widget_medicine.field_value(2)],
        ]

        self.parent.set_treat(treat_rec)
        self.parent.append_null_treat()

