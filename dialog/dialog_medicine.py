#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils


# 主視窗
class DialogMedicine(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicine, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.table_widget_prescript = args[2]
        self.medicine_set = args[3]

        self.settings = QSettings('__settings.ini', QSettings.IniFormat)
        self.ui = None
        self.dict_type = '藥品'

        self._set_ui()
        self._set_signal()
        self._set_table_width()
        self._read_data()
        self.lineEdit_input_code.setFocus(True)

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def closeEvent(self, a0: QtGui.QCloseEvent):
        self.settings.setValue("dialog_medicine_size", self.size())
        self.settings.setValue("dialog_medicine_pos", self.pos())

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICINE, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        system_utils.set_theme(self.ui, self.system_settings)

        self.ui.resize(self.settings.value("dialog_medicine_size", QSize(635, 802)))
        self.ui.move(self.settings.value("dialog_medicine_pos", QPoint(226, 147)))

        self.table_widget_dict_groups = table_widget.TableWidget(self.ui.tableWidget_dict_groups, self.database)
        self.table_widget_medicine = table_widget.TableWidget(self.ui.tableWidget_medicine, self.database)

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText('關閉')

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_groups.itemSelectionChanged.connect(self.dict_groups_changed)
        self.ui.tableWidget_medicine.clicked.connect(self.medicine_double_clicked)
        self.ui.lineEdit_input_code.textChanged.connect(self.input_code_changed)
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.buttonBox.rejected.connect(self.rejected_button_clicked)
        self.ui.toolButton_1.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_2.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_3.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_4.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_5.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_6.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_7.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_8.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_9.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_10.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_11.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_12.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_13.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_14.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_15.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_16.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_17.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_18.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_19.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_20.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_21.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_22.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_23.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_24.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_25.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_26.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_27.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_28.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_29.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_30.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_31.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_32.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_33.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_34.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_35.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_36.clicked.connect(self.phonetic_button_clicked)
        self.ui.toolButton_37.clicked.connect(self.phonetic_button_clicked)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_groups_width = [100, 80]
        medicine_width = [100, 200, 90, 50, 80, 100]
        self.table_widget_dict_groups.set_table_heading_width(dict_groups_width)
        self.table_widget_medicine.set_table_heading_width(medicine_width)
        self.table_widget_dict_groups.set_column_hidden([0])
        self.table_widget_medicine.set_column_hidden([0, 5])

    def accepted_button_clicked(self):
        self.close()

    def rejected_button_clicked(self):
        self.close()

    def reject(self):
        self.close()

    def _read_data(self):
        self._read_dict_groups()

    def _read_dict_groups(self):
        sql = 'SELECT * FROM dict_groups WHERE DictGroupsType = "{0}類別" ORDER BY DictGroupsKey'.format(self.dict_type)
        self.table_widget_dict_groups.set_db_data(sql, self._set_dict_groups_data)

    def _set_dict_groups_data(self, rec_no, rec):
        dict_groups_rec = [
            string_utils.xstr(rec['DictGroupsKey']),
            string_utils.xstr(rec['DictGroupsName']),
        ]

        for column in range(0, self.ui.tableWidget_dict_groups.columnCount()):
            self.ui.tableWidget_dict_groups.setItem(rec_no, column, QtWidgets.QTableWidgetItem(dict_groups_rec[column]))

    def dict_groups_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        self._read_medicine(dict_groups_type)
        self.ui.tableWidget_dict_groups.setFocus(True)

    def _read_medicine(self, dict_groups_type, input_code=None):
        input_code_str = ''
        if input_code is not None:
            input_code_str = 'AND ((MedicineName LIKE "%{0}%") OR (InputCode LIKE "{0}%")) '.format(input_code)

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineType = "{0}") {1}
            ORDER BY LENGTH(MedicineName), CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''.format(dict_groups_type, input_code_str)
        self.table_widget_medicine.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, rec_no, rec):
        medicine_rec = [
            string_utils.xstr(rec['MedicineKey']),
            string_utils.xstr(rec['MedicineName']),
            string_utils.xstr(rec['InsCode']),
            string_utils.xstr(rec['Unit']),
            string_utils.xstr(rec['SalePrice']),
            string_utils.xstr(rec['MedicineType']),
        ]

        for column in range(0, self.ui.tableWidget_medicine.columnCount()):
            self.ui.tableWidget_medicine.setItem(rec_no, column, QtWidgets.QTableWidgetItem(medicine_rec[column]))
            if column in [4]:
                self.ui.tableWidget_medicine.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [3]:
                self.ui.tableWidget_medicine.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

    def phonetic_button_clicked(self):
        input_code = str(self.ui.lineEdit_input_code.text()).strip()
        input_code += self.sender().text()
        self.ui.lineEdit_input_code.setText(input_code)

    def input_code_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        input_code = str(self.ui.lineEdit_input_code.text()).strip()
        if input_code == '':
            return

        input_code = string_utils.phonetic_to_str(input_code)
        self._read_medicine(dict_groups_type, input_code)
        self.ui.lineEdit_input_code.setFocus(True)
        self.ui.lineEdit_input_code.setCursorPosition(len(input_code))

    def medicine_double_clicked(self):
        self.parent.tab_list[0].append_null_medicine()
        self.add_medicine()
        self.ui.lineEdit_input_code.setText(None)
        self.ui.lineEdit_input_code.setFocus(True)

    def add_medicine(self):
        prescript_rec = [
            [0, '-1'],
            [1, self.table_widget_medicine.field_value(1)],
            [3, self.table_widget_medicine.field_value(3)],
            [4, None],
            [5, str(self.table_widget_prescript.currentRow()+1)],
            [6, str(self.parent.tab_list[0].case_key)],
            [7, str(self.parent.tab_list[0].case_date)],
            [8, self.medicine_set],
            [9, self.table_widget_medicine.field_value(5)],
            [10, self.table_widget_medicine.field_value(0)],
            [11, self.table_widget_medicine.field_value(2)],
            [12, self.system_settings.field('劑量模式')],
        ]

        self.parent.tab_list[0].set_prescript(prescript_rec)
        self.parent.tab_list[0].set_default_pres_days()
