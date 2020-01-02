
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QInputDialog
import datetime

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import number_utils
from libs import nhi_utils
from libs import registration_utils
from libs import patient_utils
from libs import dialog_utils
from libs import massage_utils
from classes import table_widget


# 養生館購物
class MassagePurchase(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MassagePurchase, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.massage_case_key = args[2]
        self.call_from = args[3]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._set_medicine()
        self.ui.tableWidget_medicine_type.setCurrentCell(0, 0)
        if self.massage_case_key is not None:
            self._read_massage_record()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MASSAGE_PURCHASE, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_medicine_type = table_widget.TableWidget(
            self.ui.tableWidget_medicine_type, self.database
        )
        self.table_widget_medicine = table_widget.TableWidget(
            self.ui.tableWidget_medicine, self.database
        )
        self.table_widget_medicine.set_column_hidden([5, 6, 7, 8, 9])

        self.table_widget_massage_prescript = table_widget.TableWidget(
            self.ui.tableWidget_massage_prescript, self.database
        )
        self.table_widget_massage_prescript.set_column_hidden([0])

        self.table_widget_massage_payment = table_widget.TableWidget(
            self.ui.tableWidget_massage_payment, self.database
        )
        self.table_widget_massage_payment.set_column_hidden([0, 1])

        self.ui.dateEdit_purchase_date.setDate(datetime.datetime.now().date())
        self.ui.label_massage_customer_key.setEnabled(False)
        self.ui.lineEdit_massage_customer_key.setEnabled(False)
        self.ui.label_name.setEnabled(False)
        self.ui.lineEdit_name.setEnabled(False)
        self.ui.toolButton_select_massage_customer.setEnabled(False)

        self._set_table_width()
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_purchase)
        self.ui.action_save.triggered.connect(self._save_purchase)
        self.ui.tableWidget_medicine_type.itemSelectionChanged.connect(self._groups_changed)
        self.ui.tableWidget_medicine.clicked.connect(self._set_massage_prescript)
        self.ui.tableWidget_massage_prescript.itemChanged.connect(self._prescript_item_changed)
        self.ui.lineEdit_input_code.textChanged.connect(self._input_code_changed)
        self.ui.radioButton_1.clicked.connect(self._set_customer)
        self.ui.radioButton_2.clicked.connect(self._set_customer)
        self.ui.comboBox_cashier.currentTextChanged.connect(self._set_sales)
        self.ui.comboBox_massager.currentTextChanged.connect(self._set_sales)

        self.ui.lineEdit_massage_customer_key.textChanged.connect(self._customer_key_changed)
        self.ui.lineEdit_name.textChanged.connect(self._customer_name_changed)
        self.ui.lineEdit_massage_customer_key.returnPressed.connect(self._get_customer)
        self.ui.toolButton_select_massage_customer.clicked.connect(self._select_customer)
        self.ui.toolButton_add_payment.clicked.connect(self._add_payment)
        self.ui.toolButton_remove_payment.clicked.connect(self._remove_payment)
        self.ui.tableWidget_massage_payment.itemChanged.connect(self._payment_item_changed)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 250, 60, 60, 80, 80, 50]
        self.table_widget_massage_prescript.set_table_heading_width(width)

        width = [100, 100, 260, 100, 230]
        self.table_widget_massage_payment.set_table_heading_width(width)

    def _set_combo_box(self):
        sql = '''
            SELECT * FROM person
            WHERE
                Position NOT IN ("醫師", "支援醫師") 
        '''
        rows = self.database.select_record(sql)
        cashier_list = []
        for row in rows:
            cashier_list.append(string_utils.xstr(row['Name']))

        sql = '''
            SELECT * FROM person
            WHERE
                Position IN ("推拿師父") 
        '''
        rows = self.database.select_record(sql)
        massager_list = []
        for row in rows:
            massager_list.append(string_utils.xstr(row['Name']))

        ui_utils.set_combo_box(self.ui.comboBox_cashier, cashier_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_massager, massager_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)

        period = registration_utils.get_current_period(self.system_settings)
        self.ui.comboBox_period.setCurrentText(period)

        current_user = self.system_settings.field('使用者')
        if current_user in cashier_list:
            self.ui.comboBox_cashier.setCurrentText(current_user)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_purchase(self):
        self.close_all()
        self.close_tab()

    def _set_medicine(self):
        self._set_medicine_type()

    def _set_medicine_type(self):
        sql = '''
            SELECT * FROM dict_groups 
            WHERE 
                DictGroupsType = "藥品類別" AND
                DictGroupsName LIKE "養生館%"
            ORDER BY DictGroupsKey
        '''
        self.table_widget_medicine_type.set_db_data_without_heading(sql, 'DictGroupsName')

    def _groups_changed(self):
        self._read_medicine()
        self.ui.lineEdit_input_code.setText('')

    def _input_code_changed(self):
        input_code = self.ui.lineEdit_input_code.text()
        self._read_medicine(input_code)

    def _read_medicine(self, input_code=None):
        self.ui.tableWidget_medicine.clear()
        self.ui.tableWidget_medicine.setRowCount(0)

        try:
            groups = self.ui.tableWidget_medicine_type.selectedItems()[0].text()
        except IndexError:
            self.ui.tableWidget_medicine.setRowCount(0)
            return

        if input_code is not None and input_code != '':
            input_code_str = '''
                AND ((InputCode LIKE "{input_code}%") OR
                     (MedicineName LIKE "{input_code}%"))
            '''.format(
                input_code=input_code,
            )
        else:
            input_code_str = 'AND MedicineType = "{medicine_type}"'.format(
                medicine_type=groups,
            )

        sql = '''
            SELECT * FROM medicine
            WHERE
                MedicineName IS NOT NULL
                {input_code_str} 
            ORDER BY LENGTH(MedicineName), CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''.format(
            medicine_type=groups,
            input_code_str=input_code_str,
        )
        rows = self.database.select_record(sql)

        column_count = 5
        x = divmod(len(rows), column_count)
        row_count = x[0]
        if x[1] > 0:
            row_count += 1

        self.ui.tableWidget_medicine.setRowCount(row_count)

        for row_no in range(row_count):
            for col in range(column_count):
                rec_no = row_no * column_count + col
                if rec_no >= len(rows):
                    break

                sale_price = number_utils.get_integer(rows[rec_no]['SalePrice'])
                if sale_price <= 0:
                    sale_price = ''
                else:
                    sale_price = '${0}'.format(sale_price)

                item_name = string_utils.xstr(
                    '{medicine_name} ({unit}) {sale_price}'.format(
                        medicine_name=string_utils.xstr(rows[rec_no]['MedicineName']),
                        unit=string_utils.xstr(rows[rec_no]['Unit']),
                        medicine_type=string_utils.xstr(rows[rec_no]['MedicineType']),
                        sale_price=sale_price,
                    )
                )
                self.ui.tableWidget_medicine.setItem(
                    row_no, col,
                    QtWidgets.QTableWidgetItem(item_name)
                )
                self.ui.tableWidget_medicine.setItem(
                    row_no, col+column_count,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(rows[rec_no]['MedicineKey']))
                )

        self.ui.tableWidget_medicine.resizeRowsToContents()
        self.ui.tableWidget_medicine.setCurrentCell(0, 0)

    def _set_massage_prescript(self):
        current_row = self.ui.tableWidget_medicine.currentRow()
        current_col = self.ui.tableWidget_medicine.currentColumn()
        medicine_name = self.ui.tableWidget_medicine.item(current_row, current_col)
        if medicine_name is None:
            return

        medicine_key = self.ui.tableWidget_medicine.item(current_row, current_col+5).text()
        self._insert_massage_prescript_row(medicine_key)

    def _check_prescript_exists(self, row):
        exists = False
        in_medicine_key = string_utils.xstr(row['MedicineKey'])
        row_count = self.ui.tableWidget_massage_prescript.rowCount()

        for row_no in range(row_count):
            medicine_key = self.ui.tableWidget_massage_prescript.item(row_no, 0)
            if medicine_key is None:
                continue

            if in_medicine_key == medicine_key.text():
                quantity = self.ui.tableWidget_massage_prescript.item(row_no, 3)
                if quantity is not None:
                    quantity = number_utils.get_integer(quantity.text())
                else:
                    quantity = 0

                self.ui.tableWidget_massage_prescript.setItem(
                    row_no, 3,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(quantity + 1))
                )
                self.ui.tableWidget_massage_prescript.item(
                    row_no, 3).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
                exists = True
                break

        return exists

    def _insert_massage_prescript_row(self, medicine_key):
        sql = '''
            SELECT * FROM medicine
            WHERE
                MedicineKey = {0}
        '''.format(medicine_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        if self._check_prescript_exists(row):
            return

        row_no = self.ui.tableWidget_massage_prescript.rowCount()
        self.ui.tableWidget_massage_prescript.setFocus(True)
        self.ui.tableWidget_massage_prescript.insertRow(row_no)
        self.ui.tableWidget_massage_prescript.setCurrentCell(row_no, 4)

        massage_prescript_row = [
            row['MedicineKey'],
            row['MedicineName'],
            row['Unit'],
            1,
            number_utils.get_integer(row['SalePrice']),
            number_utils.get_integer(row['SalePrice']),
        ]
        self._set_massage_prescript_row(massage_prescript_row, row_no)

    def _set_massage_prescript_row(self, massage_prescript_row, row_no):
        for col_no in range(len(massage_prescript_row)):
            self.ui.tableWidget_massage_prescript.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(string_utils.xstr(massage_prescript_row[col_no]))
            )

            if col_no in [2]:
                self.ui.tableWidget_massage_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif col_no in [3, 4, 5]:
                self.ui.tableWidget_massage_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

            if col_no not in [3]:
                self.ui.tableWidget_massage_prescript.item(row_no, col_no).setFlags(
                    QtCore.Qt.ItemIsEnabled
                )

        button = QtWidgets.QPushButton(self.ui.tableWidget_massage_prescript)
        button.setIcon(QtGui.QIcon('./icons/cancel.svg'))
        button.setFlat(True)
        button.clicked.connect(self._remove_prescript_row)
        self.ui.tableWidget_massage_prescript.setCellWidget(row_no, 6, button)

        self._calculate_total()

    def _remove_prescript_row(self):
        current_row = self.ui.tableWidget_massage_prescript.currentRow()
        self.ui.tableWidget_massage_prescript.removeRow(current_row)

        self._calculate_total()

    def _prescript_item_changed(self, item):
        if item is None:
            return

        row_no = item.row()
        col_no = item.column()
        if col_no != 3:
            return

        sale_price = self.ui.tableWidget_massage_prescript.item(row_no, 4)
        if sale_price is None:
            return

        quantity = item.text()
        sale_price = sale_price.text()
        subtotal = number_utils.get_integer(quantity) * number_utils.get_integer(sale_price)

        self.ui.tableWidget_massage_prescript.setItem(
            row_no, 5,
            QtWidgets.QTableWidgetItem(string_utils.xstr(subtotal))
        )
        self.ui.tableWidget_massage_prescript.item(
            row_no, 5).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.ui.tableWidget_massage_prescript.item(row_no, 5).setFlags(
            QtCore.Qt.ItemIsEnabled
        )

        self._calculate_total()

    def _calculate_total(self):
        row_count = self.ui.tableWidget_massage_prescript.rowCount()

        total = 0
        for row_no in range(row_count):
            price = self.ui.tableWidget_massage_prescript.item(row_no, 5)
            if price is None:
                continue

            total += number_utils.get_integer(float(price.text()))

        self.ui.lineEdit_total.setText('{0}'.format(total))

    def _customer_key_changed(self):
        self.ui.action_save.setEnabled(True)
        massage_customer_key = self.ui.lineEdit_massage_customer_key.text()

        if massage_customer_key == '':
            self.ui.lineEdit_name.setText(None)

        if massage_customer_key.isdigit() and len(massage_customer_key) <= 6:
            self._set_line_edit_customer_data(massage_customer_key)
        else:
            self.ui.action_save.setEnabled(False)
            self.ui.lineEdit_name.setText('')

    def _select_customer(self):
        massage_customer_key = patient_utils.select_patient(
            self, self.database, self.system_settings, 'massage_customer', 'MassageCustomerKey', ''
        )

        self._set_line_edit_customer_data(massage_customer_key)

    def _customer_name_changed(self):
        self.ui.action_save.setEnabled(True)
        customer_name = self.ui.lineEdit_name.text()

        if customer_name == '':
            self.ui.action_save.setEnabled(False)

    def _get_customer(self):
        keyword = self.ui.lineEdit_massage_customer_key.text()

        massage_customer_key = patient_utils.get_patient_by_keyword(
            self, self.database, self.system_settings,
            'massage_customer', 'MassageCustomerKey', keyword
        )
        if massage_customer_key in ['', None]:
            return

        massage_customer_key = string_utils.xstr(massage_customer_key)
        self.ui.lineEdit_massage_customer_key.setText(massage_customer_key)
        self._set_line_edit_customer_data(massage_customer_key)

    def _set_line_edit_customer_data(self, massage_customer_key):
        if massage_customer_key in [None, '']:
            return

        sql = 'SELECT * FROM massage_customer WHERE MassageCustomerKey = {0}'.format(massage_customer_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            self.ui.lineEdit_name.setText('')
            return

        row = rows[0]
        self.ui.lineEdit_massage_customer_key.setText(string_utils.xstr(row['MassageCustomerKey']))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))

    def _set_customer(self):
        if self.ui.radioButton_1.isChecked():
            self.ui.lineEdit_massage_customer_key.setText('')
            self.ui.lineEdit_name.setText('')
            self.ui.action_save.setEnabled(True)
            enabled = False
        else:
            self.ui.action_save.setEnabled(False)
            enabled = True

        self.ui.label_massage_customer_key.setEnabled(enabled)
        self.ui.lineEdit_massage_customer_key.setEnabled(enabled)
        self.ui.label_name.setEnabled(enabled)
        self.ui.lineEdit_name.setEnabled(enabled)
        self.ui.toolButton_select_massage_customer.setEnabled(enabled)

        if self.ui.radioButton_2.isChecked():
            self.ui.lineEdit_massage_customer_key.setFocus()

    def _save_purchase(self):
        if self.massage_case_key is not None:
            self._update_records()
        else:
            self._insert_records()

        self.close_purchase()

    def _update_records(self):
        self._update_massage_cases()

        self.database.delete_record('massage_prescript', 'MassageCaseKey', self.massage_case_key)
        self.database.delete_record('massage_payment', 'MassageCaseKey', self.massage_case_key)
        self._insert_massage_prescript(self.massage_case_key)
        self._insert_massage_payment(self.massage_case_key)

    def _update_massage_cases(self):
        customer_key, name = self._get_customer_data()

        case_date = '{0} {1}'.format(
            self.ui.dateEdit_purchase_date.date().toString('yyyy-MM-dd'),
            datetime.datetime.now().time().strftime('%H:%M:%S')
        )
        period = self.ui.comboBox_period.currentText()

        fields = [
            'MassageCustomerKey', 'Name', 'CaseDate', 'FinishDate',
            'Period', 'InsType',
            'TreatType',
            'Cashier', 'Massager',
            'SelfTotalFee', 'TotalFee', 'ReceiptFee',
        ]

        data = [
            customer_key,
            name,
            case_date,
            case_date,
            period,
            '自費',
            '購買商品',
            self.ui.comboBox_cashier.currentText(),
            self.ui.comboBox_massager.currentText(),
            self.ui.lineEdit_total.text(),
            self.ui.lineEdit_total.text(),
            self.ui.lineEdit_total.text(),
        ]
        self.database.update_record('massage_cases', fields, 'MassageCaseKey', self.massage_case_key, data)

    def _insert_records(self):
        massage_case_key = self._insert_massage_cases()
        self._insert_massage_prescript(massage_case_key)
        self._insert_massage_payment(massage_case_key)

    def _get_customer_data(self):
        if self.ui.radioButton_1.isChecked():
            customer_key = 0
            name = '不記名顧客'
        else:
            customer_key = number_utils.get_integer(self.ui.lineEdit_massage_customer_key.text())
            name = self.ui.lineEdit_name.text()
            if name == '':
                name = '不記名顧客'

        return customer_key, name

    def _insert_massage_cases(self):
        customer_key, name = self._get_customer_data()
        case_date = '{0} {1}'.format(
            self.ui.dateEdit_purchase_date.date().toString('yyyy-MM-dd'),
            datetime.datetime.now().time().strftime('%H:%M:%S')
        )
        period = self.ui.comboBox_period.currentText()

        fields = [
            'MassageCustomerKey', 'Name', 'CaseDate', 'FinishDate',
            'Period', 'InsType',
            'TreatType',
            'Cashier', 'Massager',
            'SelfTotalFee', 'TotalFee', 'ReceiptFee',
        ]

        data = [
            customer_key,
            name,
            case_date,
            case_date,
            period,
            '自費',
            '購買商品',
            self.ui.comboBox_cashier.currentText(),
            self.ui.comboBox_massager.currentText(),
            self.ui.lineEdit_total.text(),
            self.ui.lineEdit_total.text(),
            self.ui.lineEdit_total.text(),
        ]

        massage_case_key = self.database.insert_record('massage_cases', fields, data)

        return massage_case_key

    def _insert_massage_prescript(self, massage_case_key):
        row_count = self.ui.tableWidget_massage_prescript.rowCount()

        fields = [
            'MassageCaseKey',
            'MedicineKey', 'MedicineName', 'Quantity', 'Unit', 'Price', 'Amount',
        ]
        for row_no in range(row_count):
            medicine_key = self.ui.tableWidget_massage_prescript.item(row_no, 0).text()
            medicine_name = self.ui.tableWidget_massage_prescript.item(row_no, 1).text()
            unit = self.ui.tableWidget_massage_prescript.item(row_no, 2).text()
            quantity = self.ui.tableWidget_massage_prescript.item(row_no, 3).text()
            sale_price = self.ui.tableWidget_massage_prescript.item(row_no, 4).text()
            amount = self.ui.tableWidget_massage_prescript.item(row_no, 5).text()

            data = [
                massage_case_key,
                medicine_key, medicine_name, quantity, unit, sale_price, amount,
            ]

            self.database.insert_record('massage_prescript', fields, data)

    def _insert_massage_payment(self, massage_case_key):
        fields = [
            'MassageCaseKey', 'PaymentType', 'Amount', 'Remark',
        ]
        for row_no in range(self.ui.tableWidget_massage_payment.rowCount()):
            data = [
                massage_case_key,
                self.ui.tableWidget_massage_payment.item(row_no, 2).text(),
                self.ui.tableWidget_massage_payment.item(row_no, 3).text(),
                self.ui.tableWidget_massage_payment.item(row_no, 4).text(),
            ]
            self.database.insert_record('massage_payment', fields, data)

    def _set_sales(self):
        if self.system_settings.field('自購藥銷售人員') != '單選':
            return

        if self.sender().objectName() == 'comboBox_cashier' and self.ui.comboBox_cashier.currentText() != '':
            self.ui.comboBox_doctor.setCurrentText(None)
            self.ui.comboBox_massager.setCurrentText(None)
        elif self.sender().objectName() == 'comboBox_doctor' and self.ui.comboBox_doctor.currentText() != '':
            self.ui.comboBox_cashier.setCurrentText(None)
            self.ui.comboBox_massager.setCurrentText(None)
        elif self.sender().objectName() == 'comboBox_massager' and self.ui.comboBox_massager.currentText() != '':
            self.ui.comboBox_cashier.setCurrentText(None)
            self.ui.comboBox_doctor.setCurrentText(None)

    def _add_payment(self):
        input_dialog = dialog_utils.get_dialog(
            '付款方式', '請選擇付款方式',
            None, QInputDialog.TextInput, 320, 200)
        input_dialog.setComboBoxItems(massage_utils.PAYMENT_ITEMS)
        ok = input_dialog.exec_()

        if not ok:
            return

        item = input_dialog.textValue()

        self.ui.tableWidget_massage_payment.setRowCount(
            self.ui.tableWidget_massage_payment.rowCount() + 1
        )
        massage_payment_row = [
            None,
            None,
            item,
            None,
            None,
        ]
        row_no = self.ui.tableWidget_massage_payment.rowCount() - 1
        self._set_massage_payment_row(massage_payment_row, row_no)

    def _set_massage_payment_row(self, massage_payment_row, row_no):
        for col_no in range(len(massage_payment_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, massage_payment_row[col_no])
            self.ui.tableWidget_massage_payment.setItem(row_no, col_no, item)
            if col_no in [3]:
                self.ui.tableWidget_massage_payment.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            if col_no not in [3, 4]:
                self.ui.tableWidget_massage_payment.item(row_no, col_no).setFlags(
                    QtCore.Qt.ItemIsEnabled
                )

        self._calculate_receipt_fee()

    def _remove_payment(self):
        self.ui.tableWidget_massage_payment.removeRow(self.ui.tableWidget_massage_payment.currentRow())
        self._calculate_receipt_fee()

    def _payment_item_changed(self):
        self._calculate_receipt_fee()

    def _calculate_receipt_fee(self):
        receipt_fee = 0
        for row_no in range(self.ui.tableWidget_massage_payment.rowCount()):
            item = self.ui.tableWidget_massage_payment.item(row_no, 3)
            if item is None:
                continue

            receipt_fee += number_utils.get_float(item.text())

        receipt_fee = number_utils.round_up(receipt_fee)
        self.ui.lineEdit_receipt_fee.setText(string_utils.xstr(receipt_fee))

    def _read_massage_record(self):
        self._read_massage_case()
        self._read_massage_prescript()
        self._read_massage_payment()

    def _read_massage_case(self):
        sql = '''
            SELECT * FROM massage_cases
            WHERE
                MassageCaseKey = {massage_case_key}
        '''.format(
            massage_case_key=self.massage_case_key,
        )
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        row = rows[0]

        self.ui.dateEdit_purchase_date.setDate(row['CaseDate'].date())
        self.ui.comboBox_period.setCurrentText(string_utils.xstr(row['Period']))
        massage_customer_key = row['MassageCustomerKey']
        if massage_customer_key > 0:
            self.ui.radioButton_2.setChecked(True)
            self._set_customer()
            self.ui.lineEdit_massage_customer_key.setText(string_utils.xstr(massage_customer_key))

        self.ui.comboBox_cashier.setCurrentText(string_utils.xstr(row['Cashier']))
        self.ui.comboBox_massager.setCurrentText(string_utils.xstr(row['Massager']))

    def _read_massage_prescript(self):
        sql = '''
            SELECT * FROM massage_prescript
            WHERE
                MassageCaseKey = {massage_case_key}
            ORDER BY MassagePrescriptKey
        '''.format(
            massage_case_key=self.massage_case_key,
        )

        self.table_widget_massage_prescript.set_db_data(sql, self._set_massage_prescript_table)

    def _set_massage_prescript_table(self, row_no, row):
        massage_prescript_row = [
            string_utils.xstr(row['MedicineKey']),
            string_utils.xstr(row['MedicineName']),
            string_utils.xstr(row['Unit']),
            number_utils.get_float(row['Quantity']),
            number_utils.get_float(row['Price']),
            number_utils.get_float(row['Amount']),
        ]
        self._set_massage_prescript_row(massage_prescript_row, row_no)

    def _read_massage_payment(self):
        sql = '''
            SELECT * FROM massage_payment
            WHERE
                MassageCaseKey = {massage_case_key}
            ORDER BY MassagePaymentKey
        '''.format(
            massage_case_key=self.massage_case_key,
        )

        self.table_widget_massage_payment.set_db_data(sql, self._set_massage_payment_table)

    def _set_massage_payment_table(self, row_no, row):
        massage_payment_row = [
            string_utils.xstr(row['MassagePaymentKey']),
            string_utils.xstr(row['MassageCaseKey']),
            string_utils.xstr(row['PaymentType']),
            number_utils.get_float(row['Amount']),
            string_utils.xstr(row['Remark']),
        ]
        self._set_massage_payment_row(massage_payment_row, row_no)
