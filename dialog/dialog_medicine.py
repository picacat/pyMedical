#!/usr/bin/env python3
# 處方詞庫-滑鼠輸入 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QSettings, QSize, QPoint
from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import number_utils


# 處方詞庫-滑鼠輸入
class DialogMedicine(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicine, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.table_widget_prescript = args[2]
        self.medicine_set = args[3]
        self.dict_type = args[4]  # 藥品, 處置

        self.settings = QSettings('__settings.ini', QSettings.IniFormat)
        self.ui = None

        self._set_ui()
        self._set_signal()
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
        # database.setFixedSize(database.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)

        self.ui.resize(self.settings.value("dialog_medicine_size", QSize(635, 802)))
        self.ui.move(self.settings.value("dialog_medicine_pos", QPoint(226, 147)))

        self.table_widget_dict_groups = table_widget.TableWidget(self.ui.tableWidget_dict_groups, self.database)
        self.table_widget_medicine = table_widget.TableWidget(self.ui.tableWidget_medicine, self.database)

        self.table_widget_dict_groups.set_column_hidden([0])
        self.table_widget_medicine.set_column_hidden([0, 1])

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText('關閉')
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_groups.itemSelectionChanged.connect(self.dict_groups_changed)
        self.ui.tableWidget_medicine.clicked.connect(self._add_prescript)
        self.ui.lineEdit_input_code.textChanged.connect(self.input_code_changed)
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.buttonBox.rejected.connect(self.rejected_button_clicked)

        for tool_button in self.findChildren(QtWidgets.QToolButton):
            tool_button.clicked.connect(self.phonetic_button_clicked)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_groups_width = [100, 100]
        medicine_width = [100, 100, 200, 90, 50, 80]
        self.table_widget_dict_groups.set_table_heading_width(dict_groups_width)
        self.table_widget_medicine.set_table_heading_width(medicine_width)

    def accepted_button_clicked(self):
        self.close()

    def rejected_button_clicked(self):
        self.close()

    def reject(self):
        self.close()

    def _read_data(self):
        self._read_dict_groups()

    # 健保藥品, 藥品, 處置
    def _read_dict_groups(self):
        if self.dict_type == '處置':
            sql = '''
                SELECT * FROM dict_groups 
                WHERE 
                    (DictGroupsType = "處置類別" AND DictGroupsName IN ("穴道", "處置"))
                ORDER BY DictOrderNo, DictGroupsKey
            '''
        elif self.dict_type == '健保藥品':
            sql = '''
                SELECT * FROM dict_groups 
                WHERE 
                    (DictGroupsType = "健保藥品類別") OR 
                    (DictGroupsType = "成方類別")
                ORDER BY DictOrderNo, DictGroupsKey
            '''
        elif self.dict_type == '成方':
            sql = '''
                SELECT * FROM dict_groups 
                WHERE 
                    DictGroupsType = "藥品類別" OR
                    DictGroupsType = "處置類別"
                ORDER BY DictOrderNo, DictGroupsKey
            '''
        elif self.dict_type == '養生館':
            sql = '''
            SELECT * FROM dict_groups 
            WHERE 
                DictGroupsName LIKE "養生館%"
            ORDER BY DictOrderNo, DictGroupsKey
        '''
        else:  # 自費處方
            sql = '''
                SELECT * FROM dict_groups 
                WHERE 
                    DictGroupsType = "藥品類別" OR
                    (DictGroupsType = "處置類別" AND DictGroupsName IN ("穴道", "處置")) OR
                    DictGroupsType = "成方類別" OR
                    (DictGroupsType = "藥品類別" AND 
                     DictGroupsName NOT IN ("單方", "複方", "水藥", "外用", "高貴"))
                GROUP BY DictGroupsName
                ORDER BY 
                    FIELD(DictGroupsName, "成方", "處置", "穴道", "高貴", "外用", "水藥", "複方", "單方") DESC,
                    DictOrderNo
            '''.format(self.dict_type)

        self.table_widget_dict_groups.set_db_data(sql, self._set_dict_groups_data)

    def _set_dict_groups_data(self, rec_no, rec):
        dict_groups_rec = [
            string_utils.xstr(rec['DictGroupsKey']),
            string_utils.xstr(rec['DictGroupsName']),
        ]

        for column in range(len(dict_groups_rec)):
            self.ui.tableWidget_dict_groups.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(dict_groups_rec[column])
            )

    def dict_groups_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        self._read_medicine(dict_groups_type)
        self.ui.tableWidget_dict_groups.setFocus(True)

    def _read_medicine(self, dict_groups_type, input_code=None):
        input_code_str = ''
        order_type = '''
            ORDER BY LENGTH(MedicineName), CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''
        if input_code is not None:
            input_code_str = 'AND ((MedicineName LIKE "%{0}%") OR (InputCode LIKE "{0}%")) '.format(input_code)
            if self.system_settings.field('詞庫排序') == '點擊率':
                order_type = 'ORDER BY HitRate DESC'

        sql = '''
            SELECT * FROM medicine 
            WHERE 
                (MedicineType = "{medicine_type}")
                {input_code}
                {order_type}
        '''.format(
            medicine_type=dict_groups_type,
            input_code=input_code_str,
            order_type=order_type,
        )

        self.table_widget_medicine.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        price = string_utils.get_formatted_str('單價', row['SalePrice'])

        medicine_row = [
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['Unit']),
            price,
        ]

        for column in range(len(medicine_row)):
            self.ui.tableWidget_medicine.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medicine_row[column])
            )

            align = QtCore.Qt.AlignLeft
            if column in [4]:
                align = QtCore.Qt.AlignCenter
            elif column in [5]:
                align = QtCore.Qt.AlignRight

            self.ui.tableWidget_medicine.item(row_no, column).setTextAlignment(align | QtCore.Qt.AlignVCenter)

    def phonetic_button_clicked(self):
        input_code = str(self.ui.lineEdit_input_code.text()).strip()
        input_code += self.sender().text()
        self.ui.lineEdit_input_code.setText(input_code)

    def input_code_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        input_code = str(self.ui.lineEdit_input_code.text()).strip()
        if input_code == '':
            self._read_medicine(dict_groups_type)
            self.ui.lineEdit_input_code.setFocus(True)
            return

        input_code = string_utils.phonetic_to_str(input_code)
        self._read_medicine(dict_groups_type, input_code)
        self.ui.lineEdit_input_code.setFocus(True)
        self.ui.lineEdit_input_code.setCursorPosition(len(input_code))

    def _add_prescript(self):
        if self.dict_type == '成方':
            self._add_compound()
        else:
            self._add_medicine()

    def _add_compound(self):
        row = self._get_medicine_row()
        self.parent.add_ref_compound(row)

        self.ui.lineEdit_input_code.setText(None)
        self.ui.lineEdit_input_code.setFocus(True)

    def _add_medicine(self):
        medicine_type = self.table_widget_medicine.field_value(1)

        if self.dict_type == '養生館':
            self._add_massage_prescript()
        elif medicine_type == '成方':
            self._extract_compound()
        elif medicine_type in ['穴道', '處置']:
            self._add_treat()
        else:
            self._add_drug()

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

            medicine_row = rows[0]
            row = {
                'MedicineType': string_utils.xstr(medicine_row['MedicineType']),
                'MedicineKey': string_utils.xstr(medicine_row['MedicineKey']),
                'InsCode': string_utils.xstr(medicine_row['InsCode']),
                'MedicineName': string_utils.xstr(medicine_row['MedicineName']),
                'Unit': string_utils.xstr(medicine_row['Unit']),
                'Quantity': string_utils.xstr(compound_row['Quantity']),
                'Price': string_utils.xstr(medicine_row['SalePrice']),
                'Amount': None,
            }

            medicine_type = row['MedicineType']
            if medicine_type in ['穴道', '處置']:
                self._set_treatment(medicine_type)
                self._add_treat(row)
            else:
                self._add_drug(row)

    def _set_treatment(self, medicine_type):
        if self.parent.tab_list[0].combo_box_treatment.currentText() != '':
            return

        medicine_type_dict = {'穴道': '針灸治療', '處置': '傷科治療'}
        treatment = medicine_type_dict[medicine_type]

        self.parent.tab_list[0].combo_box_treatment.setCurrentText(treatment)

    def _add_drug(self, row=None):
        tab_no = self.medicine_set - 1
        self.parent.tab_list[tab_no].append_null_medicine()

        if row is None:
            row = self._get_medicine_row()

        self.parent.tab_list[tab_no].append_prescript(row, row['Quantity'])

        self.ui.lineEdit_input_code.setText(None)
        self.ui.lineEdit_input_code.setFocus(True)

    def _add_treat(self, row=None):
        tab_no = self.medicine_set - 1
        if self.medicine_set >= 2:
            self.parent.tab_list[tab_no].append_null_medicine()
        else:
            self.parent.tab_list[tab_no].append_null_treat()

        if row is None:
            row = self._get_medicine_row()

        self._set_treatment(row['MedicineType'])

        if self.medicine_set >= 2:
            self.parent.tab_list[tab_no].append_prescript(row)
        else:
            self.parent.tab_list[tab_no].append_treat(row)

        self.ui.lineEdit_input_code.setText(None)
        self.ui.lineEdit_input_code.setFocus(True)

    def _get_medicine_row(self):
        row = {
            'MedicineType': self.table_widget_medicine.field_value(1),
            'MedicineKey': self.table_widget_medicine.field_value(0),
            'InsCode': self.table_widget_medicine.field_value(3),
            'MedicineName': self.table_widget_medicine.field_value(2),
            'Unit': self.table_widget_medicine.field_value(4),
            'Quantity': None,
            'Price': self.table_widget_medicine.field_value(5),
            'Amount': None
        }

        return row

    def _add_massage_prescript(self):
        self.table_widget_prescript.setRowCount(
            self.table_widget_prescript.rowCount() + 1
        )
        data = [
            None,
            None,
            self.table_widget_medicine.field_value(0),
            self.table_widget_medicine.field_value(2),
            1,
            self.table_widget_medicine.field_value(4),
            number_utils.get_float(self.table_widget_medicine.field_value(5)),
            number_utils.get_float(self.table_widget_medicine.field_value(5)),
            None,
        ]
        row_no = self.table_widget_prescript.rowCount() - 1
        for col_no in range(len(data)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, data[col_no])
            self.table_widget_prescript.setItem(row_no, col_no, item)
            if col_no in [4, 6, 7]:
                self.table_widget_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [5]:
                self.table_widget_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        self.parent.calculate_total_fee()
