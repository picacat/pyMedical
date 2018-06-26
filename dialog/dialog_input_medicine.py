#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from classes import table_widget
from libs import ui_settings
from libs import system
from libs import strings


# 主視窗
class DialogInputMedicine(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputMedicine, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.medicine_type = args[2]
        self.table_widget_prescript = args[3]
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
            if self.medicine_type == '健保藥品':
                self.add_medicine()
            elif self.medicine_type == '健保處置':
                self.add_treat()

    def add_medicine(self):
        prescript_rec = [
            [0, '-1'],
            [1, self.table_widget_medicine.field_value(2)],
            [3, self.table_widget_medicine.field_value(3)],
            [4, None],
            [5, str(self.table_widget_prescript.currentRow()+1)],
            [6, str(self.parent.case_key)],
            [7, str(self.parent.case_date)],
            [8, '1'],
            [9, self.table_widget_medicine.field_value(1)],
            [10, self.table_widget_medicine.field_value(0)],
            [11, self.table_widget_medicine.field_value(5)],
            [12, self.system_settings.field('劑量模式')],
        ]

        self.parent.set_prescript(prescript_rec)
        self.parent.set_default_pres_days()
        self.parent.append_null_medicine()

    def add_treat(self):
        treat_rec = [
            [0, '-1'],
            [1, self.table_widget_medicine.field_value(2)],
            [2, str(self.parent.case_key)],
            [3, str(self.parent.case_date)],
            [4, '1'],
            [5, self.table_widget_medicine.field_value(1)],
            [6, self.table_widget_medicine.field_value(0)],
            [7, self.table_widget_medicine.field_value(5)],
        ]

        self.parent.set_treat(treat_rec)
        self.parent.append_null_treat()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_DIALOG_INPUT_MEDICINE, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system.set_css(self)
        system.set_theme(self.ui, self.system_settings)

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
        self.ui.tableWidget_medicine.doubleClicked.connect(self.accepted_button_clicked)

    # 設定欄位寬度
    def _set_table_width(self):
        medicine_width = [100, 60, 240, 60, 80, 120]
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
            medicine_type = 'AND (MedicineType = "單方" OR MedicineType = "複方" OR MedicineType = "成方")'
        elif self.medicine_type == '健保處置':
            medicine_type = 'AND (MedicineType = "穴道" OR MedicineType = "處置" OR MedicineType = "成方")'
        else:
            medicine_type = ''

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName LIKE "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}")
            {1}
            ORDER BY FIELD(MedicineType, "單方", "複方", "成方"), LENGTH(MedicineName), 
            CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''.format(self.input_code, medicine_type)
        self.table_widget_medicine.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, rec_no, rec):
        if self.medicine_type == '健保藥品':
            remark = strings.xstr(rec['InsCode'])
        else:
            remark = None
        medicine_rec = [
            strings.xstr(rec['MedicineKey']),
            strings.xstr(rec['MedicineType']),
            strings.xstr(rec['MedicineName']),
            strings.xstr(rec['Unit']),
            strings.xstr(rec['SalePrice']),
            remark
        ]

        for column in range(0, self.ui.tableWidget_medicine.columnCount()):
            self.ui.tableWidget_medicine.setItem(rec_no, column, QtWidgets.QTableWidgetItem(medicine_rec[column]))
            if column in [3]:
                self.ui.tableWidget_medicine.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
