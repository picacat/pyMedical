#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QInputDialog, QMessageBox
from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import dialog_utils
from libs import number_utils
from libs import personnel_utils
from classes import table_widget
from dialog import dialog_input_drug


# 處方詞庫 2019.02.25
class DictDrug(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictDrug, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.dict_type = '藥品'

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._read_drug()
        self._set_permission()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_DRUG, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_dict_groups = table_widget.TableWidget(self.ui.tableWidget_dict_groups, self.database)
        self.table_widget_dict_groups.set_column_hidden([0, 1])
        self.table_widget_dict_drug = table_widget.TableWidget(self.ui.tableWidget_dict_drug, self.database)
        self.table_widget_dict_drug.set_column_hidden([0])
        self._set_table_width()

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '處方資料', '更改抽成', self.user_name) != 'Y':
            self.table_widget_dict_groups.set_column_hidden([3])
            self.table_widget_dict_drug.set_column_hidden([14])

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_dict_groups.itemSelectionChanged.connect(self.dict_groups_changed)
        self.ui.toolButton_add_dict_groups.clicked.connect(self._add_dict_groups)
        self.ui.toolButton_remove_dict_groups.clicked.connect(self._remove_dict_groups)
        self.ui.toolButton_edit_dict_groups.clicked.connect(self._edit_dict_groups)
        self.ui.tableWidget_dict_groups.doubleClicked.connect(self._edit_dict_groups)
        self.ui.toolButton_add_drug.clicked.connect(self._add_drug)
        self.ui.toolButton_remove_drug.clicked.connect(self._remove_drug)
        self.ui.toolButton_edit_drug.clicked.connect(self._edit_drug)
        self.ui.toolButton_copy_drug.clicked.connect(self._copy_drug)
        self.ui.tableWidget_dict_drug.doubleClicked.connect(self._edit_drug)
        self.ui.tableWidget_dict_drug.itemSelectionChanged.connect(self.dict_drug_changed)
        self.ui.lineEdit_search_drug.textChanged.connect(self._search_drug)
        self.ui.toolButton_up.clicked.connect(self._groups_order_up)
        self.ui.toolButton_down.clicked.connect(self._groups_order_down)

    # 設定欄位寬度
    def _set_table_width(self):
        dict_groups_width = [100, 50, 115, 60]
        self.table_widget_dict_groups.set_table_heading_width(dict_groups_width)

        dict_drug_width = [100, 100, 100, 70, 210, 90, 50, 50, 80, 80, 120, 80, 70, 70, 60, 65, 50]
        self.table_widget_dict_drug.set_table_heading_width(dict_drug_width)

    def _read_drug(self):
        self._read_dict_groups()
        self._check_dict_groups_order_no()

    def _check_dict_groups_order_no(self):
        index = 0
        for row_no in range(self.ui.tableWidget_dict_groups.rowCount()):
            order_no = self.ui.tableWidget_dict_groups.item(row_no, 1)
            if order_no is not None and order_no.text() != '':
                continue

            index += 1

            dict_groups_key = self.ui.tableWidget_dict_groups.item(row_no, 0).text()
            sql = '''
                UPDATE dict_groups
                SET
                    DictOrderNo = "{dict_order_no:0>4}"
                WHERE
                    DictGroupsKey = {dict_groups_key}
            '''.format(
                dict_order_no=index,
                dict_groups_key=dict_groups_key,
            )
            self.database.exec_sql(sql)

        self._read_dict_groups()

    def _read_dict_groups(self):
        sql = '''
            SELECT * FROM dict_groups 
            WHERE 
                DictGroupsType = "{0}類別" 
            ORDER BY DictOrderNo, DictGroupsKey
        '''.format(self.dict_type)
        self.table_widget_dict_groups.set_db_data(sql, self._set_dict_groups_data)

    def _set_dict_groups_data(self, row_no, row):
        if row['DictGroupsLevel2'] is None:
            percent = ''
        else:
            try:
                percent = '{0}%'.format(number_utils.get_integer(row['DictGroupsLevel2']))
            except ValueError:
                percent = string_utils.xstr(row['DictGroupsLevel2'])

        dict_groups_row = [
            string_utils.xstr(row['DictGroupsKey']),
            string_utils.xstr(row['DictOrderNo']),
            string_utils.xstr(row['DictGroupsName']),
            percent,
        ]

        for column in range(len(dict_groups_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, dict_groups_row[column])
            self.ui.tableWidget_dict_groups.setItem(
                row_no, column, item,
            )
            if column in [3]:
                self.ui.tableWidget_dict_groups.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def dict_groups_changed(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(2)
        self._read_dict_drug(dict_groups_type)
        self.ui.tableWidget_dict_groups.setFocus(True)

    def _read_dict_drug(self, dict_groups_type, keyword=None):
        if dict_groups_type is None:
            medicine_type_condition = ''
        else:
            medicine_type_condition = 'MedicineType = "{medicine_type}"'.format(
                medicine_type=dict_groups_type,
            )

        if keyword is None:
            keyword_condition = ''
        else:
            keyword_condition = '{keyword}'.format(keyword=keyword)

        if medicine_type_condition != '' and keyword_condition != '':
            keyword_condition = ' AND ' + keyword_condition

        sql = '''
            SELECT * FROM medicine 
            WHERE 
                {medicine_type_condition}
                {keyword_condition}
            ORDER BY MedicineCode, MedicineName
        '''.format(
            medicine_type_condition=medicine_type_condition,
            keyword_condition=keyword_condition,
        )

        self.table_widget_dict_drug.set_db_data(sql, self._set_dict_drug_data)
        medicine_key = self.table_widget_dict_drug.field_value(0)
        self._read_drug_description(medicine_key)

    def _set_dict_drug_data(self, row_no, row):
        dict_drug_row = [
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineCode']),
            string_utils.xstr(row['InputCode']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['Unit']),
            number_utils.get_float(row['Dosage']),
            string_utils.xstr(row['DoctorProject']),
            string_utils.xstr(row['Project']),
            string_utils.xstr(row['MedicineAlias']),
            string_utils.xstr(row['Location']),
            number_utils.get_float(row['InPrice']),
            number_utils.get_float(row['SalePrice']),
            number_utils.get_integer(row['Quantity']),
            number_utils.get_integer(row['SafeQuantity']),
            string_utils.xstr(row['Commission']),
        ]

        for column in range(len(dict_drug_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, dict_drug_row[column])
            self.ui.tableWidget_dict_drug.setItem(row_no, column, item)
            if column in [7, 12, 13, 14, 15, 16]:
                self.ui.tableWidget_dict_drug.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [6]:
                self.ui.tableWidget_dict_drug.item(row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    # 新增處方類別
    def _add_dict_groups(self):
        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入{0}類別'.format(self.dict_type),
            None, QInputDialog.TextInput, 320, 200)
        if not input_dialog.exec_():
            return

        dict_groups = input_dialog.textValue()
        if dict_groups == '':
            return

        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入「{0}類別」的抽成'.format(dict_groups),
            None, QInputDialog.TextInput, 320, 200)
        if not input_dialog.exec_():
            return

        dict_groups_percent = input_dialog.textValue().strip('%')

        sql = '''
            SELECT * FROM dict_groups
            WHERE
                DictGroupsType = "{0}類別" 
            ORDER BY DictOrderNo DESC LIMIT 1
        '''.format(self.dict_type)
        rows = self.database.select_record(sql)
        last_dict_order_no = number_utils.get_integer(rows[0]['DictOrderNo'])

        field = [
            'DictGroupsType', 'DictOrderNo', 'DictGroupsName', 'DictGroupsLevel2'
        ]

        data = [
            '{0}類別'.format(self.dict_type),
            last_dict_order_no+1,
            dict_groups,
            dict_groups_percent,
        ]
        self.database.insert_record('dict_groups', field, data)
        self._read_dict_groups()

    # 移除處方類別
    def _remove_dict_groups(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}類別資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除 [{0}] {1}類別?</b></font>'.format(
                self.table_widget_dict_groups.field_value(2), self.dict_type),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_groups.field_value(0)
        self.database.delete_record('dict_groups', 'DictGroupsKey', key)
        self.ui.tableWidget_dict_groups.removeRow(self.ui.tableWidget_dict_groups.currentRow())

    # 更改處方類別
    def _edit_dict_groups(self):
        old_groups = self.table_widget_dict_groups.field_value(2)

        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入{0}類別'.format(self.dict_type),
            old_groups,
            QInputDialog.TextInput, 320, 200)
        if not input_dialog.exec_():
            return

        dict_groups_name = input_dialog.textValue()
        if dict_groups_name == '':
            return

        old_percent = self.table_widget_dict_groups.field_value(3).strip('%')
        input_dialog = dialog_utils.get_dialog(
            '{0}類別'.format(self.dict_type), '請輸入「{0}類別」的抽成'.format(dict_groups_name),
            old_percent,
            QInputDialog.TextInput, 320, 200)
        if not input_dialog.exec_():
            return

        dict_groups_percent = input_dialog.textValue().strip('%')

        data = [
            dict_groups_name,
            dict_groups_percent,
        ]

        sql = '''
            UPDATE dict_groups set DictGroupsTopLevel = "{0}" WHERE 
            DictGroupsType = "{1}" and DictGroupsTopLevel = "{2}"
        '''.format(dict_groups_name, self.dict_type, old_groups)
        self.database.exec_sql(sql)

        fields = ['DictGroupsName', 'DictGroupsLevel2']
        self.database.update_record(
            'dict_groups', fields, 'DictGroupsKey',
            self.table_widget_dict_groups.field_value(0), data
        )

        sql = '''
            SELECT * FROM dict_groups
            WHERE
                DictGroupsKey = {0}
        '''.format(self.table_widget_dict_groups.field_value(0))
        row = self.database.select_record(sql)[0]
        self._set_dict_groups_data(self.ui.tableWidget_dict_groups.currentRow(), row)

        sql = '''
            UPDATE medicine
            SET
                MedicineType = "{dict_groups_name}"
            WHERE
                MedicineType = "{old_groups}"
        '''.format(
            dict_groups_name=dict_groups_name,
            old_groups=old_groups,
        )
        self.database.exec_sql(sql)

    # 新增處方
    def _add_drug(self):
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings)
        if dialog.exec_():
            medicine_key = self._save_drug(dialog)
            self._save_commission(dialog, medicine_key)

        dialog.close_all()
        dialog.deleteLater()

    def _save_drug(self, dialog):
        current_row = self.ui.tableWidget_dict_drug.rowCount()
        self.ui.tableWidget_dict_drug.insertRow(current_row)
        dict_groups_type = self.table_widget_dict_groups.field_value(2)
        fields = [
            'MedicineType', 'MedicineCode', 'InputCode', 'MedicineName', 'Unit', 'MedicineMode', 'InsCode',
            'Dosage', 'MedicineAlias', 'Location', 'InPrice', 'SalePrice', 'Commission',
            'Quantity', 'SafeQuantity',
            'Description',
        ]
        data = [
            dict_groups_type,
            dialog.ui.lineEdit_medicine_code.text(),
            dialog.ui.lineEdit_input_code.text(),
            dialog.ui.lineEdit_medicine_name.text(),
            dialog.ui.comboBox_unit.currentText(),
            dialog.ui.comboBox_medicine_mode.currentText(),
            dialog.ui.lineEdit_ins_code.text(),
            dialog.ui.lineEdit_dosage.text(),
            dialog.ui.lineEdit_medicine_alias.text(),
            dialog.ui.lineEdit_location.text(),
            dialog.ui.lineEdit_in_price.text(),
            dialog.ui.lineEdit_sale_price.text(),
            dialog.ui.lineEdit_commission.text(),
            dialog.ui.lineEdit_quantity.text(),
            dialog.ui.lineEdit_safe_quantity.text(),
            dialog.ui.textEdit_description.toPlainText(),
        ]
        string_utils.str_to_none(data)
        medicine_key = self.database.insert_record('medicine', fields, data)
        self._read_dict_drug(dict_groups_type)

        return medicine_key

    def _save_commission(self, dialog, medicine_key):
        fields = ['MedicineKey', 'Name', 'Commission', 'Remark']

        for row_no in range(dialog.ui.tableWidget_commission.rowCount()):
            name = dialog.ui.tableWidget_commission.item(row_no, 0).text()
            commission = dialog.ui.tableWidget_commission.item(row_no, 1).text()
            remark = dialog.ui.tableWidget_commission.item(row_no, 2).text()

            data = [medicine_key, name, commission, remark]
            self.database.insert_record('commission', fields, data)

    # 移除處方
    def _remove_drug(self):
        msg_box = dialog_utils.get_message_box(
            '刪除{0}資料'.format(self.dict_type), QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}: "{1}"?</b></font>'.format(
                self.dict_type, self.table_widget_dict_drug.field_value(4)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        key = self.table_widget_dict_drug.field_value(0)
        self.database.delete_record('medicine', 'MedicineKey', key)
        self.database.delete_record('commission', 'MedicineKey', key)
        self.ui.tableWidget_dict_drug.removeRow(self.ui.tableWidget_dict_drug.currentRow())

    # 更改處方
    def _edit_drug(self):
        key = self.table_widget_dict_drug.field_value(0)
        dialog = dialog_input_drug.DialogInputDrug(self, self.database, self.system_settings, key)
        dialog.exec_()
        dialog.close_all()
        dialog.deleteLater()

        sql = 'SELECT * FROM medicine WHERE MedicineKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_dict_drug_data(self.ui.tableWidget_dict_drug.currentRow(), row_data)
        self.dict_drug_changed()

    # 拷貝處方
    def _copy_drug(self):
        sql = '''
            SELECT * FROM dict_groups 
            WHERE 
                DictGroupsType = "{0}類別" 
            ORDER BY DictGroupsKey
        '''.format(self.dict_type)

        rows = self.database.select_record(sql)
        items = ()
        for row in rows:
            items += (string_utils.xstr(row['DictGroupsName']), )

        item, ok = QInputDialog.getItem(
            self, "拷貝處方詞庫", "請選擇拷貝到何處", items, 0, False
        )

        if not ok:
            return

        medicine_key = self.table_widget_dict_drug.field_value(0)
        sql = '''
            SELECT * FROM medicine
            WHERE
                MedicineKey = {medicine_key}
        '''.format(
            medicine_key=medicine_key,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        fields = [
            'MedicineType', 'MedicineMode', 'MedicineCode', 'InputCode', 'InsCode',
            'MedicineName', 'MedicineAlias', 'Unit', 'Dosage', 'Location',
            'SalePrice', 'InPrice', 'Charged', 'SafeQuantity', 'Description',
        ]
        data = [
            item,
            string_utils.xstr(row['MedicineMode']),
            string_utils.xstr(row['MedicineCode']),
            string_utils.xstr(row['InputCode']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['MedicineAlias']),
            string_utils.xstr(row['Unit']),
            string_utils.xstr(row['Dosage']),
            string_utils.xstr(row['Location']),
            string_utils.xstr(row['SalePrice']),
            string_utils.xstr(row['InPrice']),
            string_utils.xstr(row['Charged']),
            string_utils.xstr(row['SafeQuantity']),
            string_utils.get_str(row['Description'], 'utf8'),
        ]
        self.database.insert_record('medicine', fields, data)

        dict_groups_type = self.table_widget_dict_groups.field_value(1)
        if dict_groups_type == item:
            self._read_dict_drug(dict_groups_type)

    def dict_drug_changed(self):
        medicine_key = self.table_widget_dict_drug.field_value(0)
        self._read_drug_description(medicine_key)

    def _read_drug_description(self, medicine_key):
        self.ui.textEdit_description.setText('')

        sql = '''
            SELECT * FROM medicine WHERE MedicineKey = "{0}"
        '''.format(medicine_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        try:
            self.ui.textEdit_description.setText(string_utils.get_str(rows[0]['Description'], 'utf8'))
        except TypeError:
            pass

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

    def _search_drug(self):
        dict_groups_type = self.table_widget_dict_groups.field_value(2)
        keyword = self.ui.lineEdit_search_drug.text()

        if keyword == '':
            self._read_dict_drug(dict_groups_type)
        else:
            if self.ui.checkBox_find_all.isChecked():
                dict_groups_type = None

            script = '''
                (InputCode LIKE "{0}%" OR MedicineName LIKE "%{0}%")
            '''.format(keyword)

            self._read_dict_drug(dict_groups_type, script)

        self.ui.lineEdit_search_drug.setFocus(True)
        self.ui.lineEdit_search_drug.setCursorPosition(len(keyword))

    def _groups_order_up(self):
        current_row = self.ui.tableWidget_dict_groups.currentRow()
        if current_row == 0:
            return

        prior_dict_row = [
            self.ui.tableWidget_dict_groups.item(current_row-1, 0).text(),
            self.ui.tableWidget_dict_groups.item(current_row, 1).text(),
            self.ui.tableWidget_dict_groups.item(current_row-1, 2).text(),
        ]

        current_dict_row = [
            self.ui.tableWidget_dict_groups.item(current_row, 0).text(),
            self.ui.tableWidget_dict_groups.item(current_row-1, 1).text(),
            self.ui.tableWidget_dict_groups.item(current_row, 2).text(),
        ]

        self._update_dict_groups(prior_dict_row)
        self._update_dict_groups(current_dict_row)
        self._refresh_dict_groups_row(current_row-1, current_dict_row)
        self._refresh_dict_groups_row(current_row, prior_dict_row)

        self.ui.tableWidget_dict_groups.setCurrentCell(current_row-1, 1)

    def _groups_order_down(self):
        current_row = self.ui.tableWidget_dict_groups.currentRow()
        if current_row >= self.ui.tableWidget_dict_groups.rowCount() - 1:
            return

        next_dict_row = [
            self.ui.tableWidget_dict_groups.item(current_row+1, 0).text(),
            self.ui.tableWidget_dict_groups.item(current_row, 1).text(),
            self.ui.tableWidget_dict_groups.item(current_row+1, 2).text(),
        ]

        current_dict_row = [
            self.ui.tableWidget_dict_groups.item(current_row, 0).text(),
            self.ui.tableWidget_dict_groups.item(current_row+1, 1).text(),
            self.ui.tableWidget_dict_groups.item(current_row, 2).text(),
        ]

        self._update_dict_groups(next_dict_row)
        self._update_dict_groups(current_dict_row)
        self._refresh_dict_groups_row(current_row+1, current_dict_row)
        self._refresh_dict_groups_row(current_row, next_dict_row)

        self.ui.tableWidget_dict_groups.setCurrentCell(current_row+1, 1)

    def _update_dict_groups(self, dict_groups_row):
        self.database.exec_sql(
            'UPDATE dict_groups SET DictOrderNo = "{dict_order_no}" WHERE DictGroupsKey = {dict_groups_key}'.format(
                dict_order_no=dict_groups_row[1],
                dict_groups_key=dict_groups_row[0],
            )
        )

    def _refresh_dict_groups_row(self, row_no, dict_groups_row):
        for col_no in range(len(dict_groups_row)):
            self.ui.tableWidget_dict_groups.setItem(
                row_no, col_no, QtWidgets.QTableWidgetItem(dict_groups_row[col_no]),
            )

