#!/usr/bin/env python3
# 處方詞庫-鍵盤輸入 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import prescript_utils


# 處方詞庫-鍵盤輸入
class DialogInputMedicine(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputMedicine, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.dict_type = args[2]
        self.medicine_set = args[3]
        self.table_widget_prescript = args[4]
        self.previous_medicine_name = args[5]
        self.input_code = args[6]

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
            self.table_widget_prescript.currentItem().setText(self.previous_medicine_name)
        else:
            if self.dict_type == '健保處置':
                self._add_treat()
            else:
                self._add_prescript()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INPUT_MEDICINE, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
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
        if self.dict_type == '健保藥品':
            # medicine_type = 'AND (MedicineType in ("單方", "複方", "成方"))'
            medicine_type = 'AND (MedicineType NOT IN ("水藥", "外用", "高貴", "穴道", "處置", "檢驗"))'
        elif self.dict_type == '所有藥品':
            medicine_type = 'AND (MedicineType in ("單方", "複方", "水藥", "外用", "高貴", "成方"))'
        elif self.dict_type == '健保處置':
            if self.parent.combo_box_treatment.currentText() in nhi_utils.ACUPUNCTURE_TREAT:
                medicine_type = 'AND (MedicineType in ("穴道"))'
            elif self.parent.combo_box_treatment.currentText() in nhi_utils.MASSAGE_TREAT:
                medicine_type = 'AND (MedicineType in ("處置"))'
            else:
                medicine_type = 'AND (MedicineType in ("穴道", "處置", "成方"))'
        else:
            medicine_type = ''

        order_type = '''
            ORDER BY FIELD(MedicineType, "單方", "複方", "水藥", "外用", "高貴", "穴道", "處置", "成方"),
                LENGTH(MedicineName),
                CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''
        if self.system_settings.field('詞庫排序') == '點擊率':
            order_type = 'ORDER BY HitRate DESC'

        sql = '''
            SELECT * FROM medicine WHERE 
            (MedicineName LIKE "{0}%" OR InputCode LIKE "{0}%" OR MedicineCode = "{0}" OR InsCode = "{0}")
            {1}
            {2}
        '''.format(self.input_code, medicine_type, order_type)
        self.table_widget_medicine.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        if self.dict_type == '健保藥品':
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

            self.ui.tableWidget_medicine.item(row_no, column).setTextAlignment(
                align | QtCore.Qt.AlignVCenter
            )

    # 輸入藥品
    def _add_prescript(self):
        medicine_type = self.table_widget_medicine.field_value(1)
        if medicine_type == '成方':
            self._extract_compound()
        else:
            self._add_medicine()

    # 解開成方
    def _extract_compound(self):
        medicine_key = self.table_widget_medicine.field_value(0)
        sql = '''
            SELECT * FROM refcompound
            WHERE
                CompoundKey = {0}
            ORDER BY RefCompoundKey
        '''.format(medicine_key)

        compound_rows = self.database.select_record(sql)
        if len(compound_rows) <= 0:
            return

        for compound_row in compound_rows:
            medicine_key = string_utils.xstr(compound_row['MedicineKey'])
            if medicine_key == '':
                continue

            sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(medicine_key)
            rows = self.database.select_record(sql)
            if len(rows) <= 0:
                continue

            prescript_row = rows[0]
            row = {
                'MedicineType': string_utils.xstr(prescript_row['MedicineType']),
                'MedicineKey': string_utils.xstr(prescript_row['MedicineKey']),
                'InsCode': string_utils.xstr(prescript_row['InsCode']),
                'MedicineName': string_utils.xstr(prescript_row['MedicineName']),
                'Unit': string_utils.xstr(prescript_row['Unit']),
                'Quantity': string_utils.xstr(compound_row['Quantity']),
                'Price': string_utils.xstr(prescript_row['SalePrice']),
                'Amount': None,
            }

            medicine_type = row['MedicineType']
            if medicine_type in ['穴道', '處置']:
                self._set_treatment(medicine_type)
                self._add_treat(row)

                current_row = self.parent.ui.tableWidget_prescript.currentRow()
                if self.parent.ui.tableWidget_prescript.item(current_row, 6) is None:  # medicine key
                    self.parent.ui.tableWidget_prescript.removeRow(current_row)
            else:
                self._add_medicine(row)

    # 輸入藥品
    def _add_medicine(self, row=None):
        if row is None:
            row = self._get_medicine_row()

        self.parent.append_prescript(row, row['Quantity'])
        self.parent.append_null_medicine()

    def _set_treatment(self, medicine_type):
        if self.parent.combo_box_treatment.currentText() != '':
            return

        medicine_type_dict = {'穴道': '針灸治療', '處置': '傷科治療'}
        treatment = medicine_type_dict[medicine_type]

        self.parent.combo_box_treatment.setCurrentText(treatment)

    # 輸入處置
    def _add_treat(self, row=None):
        if row is None:
            row = self._get_medicine_row()

        self.parent.append_treat(row)
        self.parent.append_null_treat()

    def _get_medicine_row(self):
        row = {
            'MedicineType': self.table_widget_medicine.field_value(1),
            'MedicineKey': self.table_widget_medicine.field_value(0),
            'InsCode': self.table_widget_medicine.field_value(5),
            'MedicineName': self.table_widget_medicine.field_value(2),
            'Unit': self.table_widget_medicine.field_value(3),
            'Quantity': None,
            'Price': self.table_widget_medicine.field_value(4),
            'Amount': None
        }

        return row

