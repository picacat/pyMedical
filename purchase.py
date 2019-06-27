
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
import datetime

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import nhi_utils
from libs import registration_utils
from classes import table_widget
from dialog import dialog_medical_record_picker
from dialog import dialog_select_patient


# 櫃台購藥
class Purchase(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Purchase, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.call_from = args[2]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._set_medicine()
        self.ui.tableWidget_medicine_type.setCurrentCell(0, 0)

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_PURCHASE, self)
        self.table_widget_medicine_type = table_widget.TableWidget(
            self.ui.tableWidget_medicine_type, self.database
        )
        self.table_widget_medicine = table_widget.TableWidget(
            self.ui.tableWidget_medicine, self.database
        )
        self.table_widget_prescript = table_widget.TableWidget(
            self.ui.tableWidget_prescript, self.database
        )
        self.ui.dateEdit_purchase_date.setDate(datetime.datetime.now().date())
        self.ui.label_patient_key.setEnabled(False)
        self.ui.lineEdit_patient_key.setEnabled(False)
        self.ui.label_name.setEnabled(False)
        self.ui.lineEdit_name.setEnabled(False)
        self.ui.toolButton_patient_list.setEnabled(False)
        self.ui.toolButton_find_patient.setEnabled(False)

        self._set_table_width()
        self._set_combo_box()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_purchase)
        self.ui.action_save.triggered.connect(self._save_purchase)
        self.ui.toolButton_patient_list.clicked.connect(self._patient_picker)
        self.ui.toolButton_find_patient.clicked.connect(self._select_patient)
        self.ui.tableWidget_medicine_type.itemSelectionChanged.connect(self._groups_changed)
        self.ui.tableWidget_medicine.clicked.connect(self._set_prescript)
        self.ui.tableWidget_prescript.itemChanged.connect(self._prescript_item_changed)
        self.ui.lineEdit_input_code.textChanged.connect(self._input_code_changed)
        self.ui.lineEdit_patient_key.textChanged.connect(self._patient_key_changed)
        self.ui.lineEdit_discount.textChanged.connect(self._discount_changed)
        self.ui.radioButton_1.clicked.connect(self._set_patient)
        self.ui.radioButton_2.clicked.connect(self._set_patient)
        self.ui.comboBox_cashier.currentTextChanged.connect(self._set_sales)
        self.ui.comboBox_doctor.currentTextChanged.connect(self._set_sales)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 80, 260, 60, 60, 80, 80, 80]
        self.table_widget_prescript.set_table_heading_width(width)
        self.table_widget_prescript.set_column_hidden([0, 1])
        self.table_widget_medicine.set_column_hidden([5, 6, 7, 8, 9])

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
                Position IN ("醫師", "支援醫師") 
        '''
        rows = self.database.select_record(sql)
        doctor_list = []
        for row in rows:
            doctor_list.append(string_utils.xstr(row['Name']))

        ui_utils.set_combo_box(self.ui.comboBox_cashier, cashier_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_doctor, doctor_list, None)
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)

        period = registration_utils.get_period(self.system_settings)
        self.ui.comboBox_period.setCurrentText(period)

        current_user = self.system_settings.field('使用者')
        if current_user in cashier_list:
            self.ui.comboBox_cashier.setCurrentText(current_user)
        elif current_user in doctor_list:
            self.ui.comboBox_doctor.setCurrentText(current_user)

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
                DictGroupsType = "藥品類別" 
            ORDER BY DictGroupsKey
        '''
        rows = self.database.select_record(sql)

        row_count = len(rows)
        column_count = self.ui.tableWidget_medicine.columnCount()
        total_row = int(row_count / column_count)
        if row_count % column_count > 0:
            total_row += 1

        for row_no in range(0, total_row):
            self.ui.tableWidget_medicine_type.setRowCount(
                self.ui.tableWidget_medicine_type.rowCount() + 1
            )
            for col_no in range(0, column_count):
                index = (row_no * column_count) + col_no
                if index >= row_count:
                    break

                self.ui.tableWidget_medicine_type.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem(rows[index]['DictGroupsName'])
                )

        # self.ui.tableWidget_medicine_type.setColumnCount(row_count)
        #
        # for col in range(0, row_count):
        #     self.ui.tableWidget_medicine_type.setItem(
        #         0, col,
        #         QtWidgets.QTableWidgetItem(rows[col]['DictGroupsName'])
        #     )
        #
        # self.ui.tableWidget_medicine_type.setCurrentCell(0, 4)

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

    def _set_prescript(self):
        current_row = self.ui.tableWidget_medicine.currentRow()
        current_col = self.ui.tableWidget_medicine.currentColumn()
        medicine_name = self.ui.tableWidget_medicine.item(current_row, current_col)
        if medicine_name is None:
            return

        medicine_key = self.ui.tableWidget_medicine.item(current_row, current_col+5).text()
        self._insert_prescript_row(medicine_key)

    def _check_prescript_exists(self, row):
        exists = False
        in_medicine_key = string_utils.xstr(row['MedicineKey'])
        row_count = self.ui.tableWidget_prescript.rowCount()

        for row_no in range(row_count):
            medicine_key = self.ui.tableWidget_prescript.item(row_no, 0)
            if medicine_key is None:
                continue

            if in_medicine_key == medicine_key.text():
                quantity = self.ui.tableWidget_prescript.item(row_no, 4)
                if quantity is not None:
                    quantity = number_utils.get_integer(quantity.text())
                else:
                    quantity = 0

                self.ui.tableWidget_prescript.setItem(
                    row_no, 4,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(quantity + 1))
                )
                self.ui.tableWidget_prescript.item(
                    row_no, 4).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
                exists = True
                break

        return exists

    def _insert_prescript_row(self, medicine_key):
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

        row_no = self.ui.tableWidget_prescript.rowCount()
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(row_no)
        self.ui.tableWidget_prescript.setCurrentCell(row_no, 4)

        prescript_row = [
            row['MedicineKey'],
            row['MedicineType'],
            row['MedicineName'],
            row['Unit'],
            1,
            number_utils.get_integer(row['SalePrice']),
            number_utils.get_integer(row['SalePrice']),
        ]
        for col_no in range(len(prescript_row)):
            self.ui.tableWidget_prescript.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(string_utils.xstr(prescript_row[col_no]))
            )

            if col_no in [3]:
                self.ui.tableWidget_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif col_no in [4, 5, 6]:
                self.ui.tableWidget_prescript.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

            if col_no not in [4]:
                self.ui.tableWidget_prescript.item(row_no, col_no).setFlags(
                    QtCore.Qt.ItemIsEnabled
                )

        button = QtWidgets.QPushButton(self.ui.tableWidget_prescript)
        # button.setText('刪除')
        button.setIcon(QtGui.QIcon('./icons/gtk-delete.svg'))
        button.setFlat(True)
        button.clicked.connect(self._remove_prescript_row)
        self.ui.tableWidget_prescript.setCellWidget(row_no, 7, button)

        self._calculate_total()

    def _remove_prescript_row(self):
        current_row = self.ui.tableWidget_prescript.currentRow()
        self.ui.tableWidget_prescript.removeRow(current_row)

        self._calculate_total()

    def _prescript_item_changed(self, item):
        if item is None:
            return

        row_no = item.row()
        col_no = item.column()
        if col_no != 4:
            return

        sale_price = self.ui.tableWidget_prescript.item(row_no, 5)
        if sale_price is None:
            return

        quantity = item.text()
        sale_price = sale_price.text()
        subtotal = number_utils.get_integer(quantity) * number_utils.get_integer(sale_price)

        self.ui.tableWidget_prescript.setItem(
            row_no, 6,
            QtWidgets.QTableWidgetItem(string_utils.xstr(subtotal))
        )
        self.ui.tableWidget_prescript.item(
            row_no, 6).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.ui.tableWidget_prescript.item(row_no, 6).setFlags(
            QtCore.Qt.ItemIsEnabled
        )

        self._calculate_total()

    def _calculate_total(self):
        row_count = self.ui.tableWidget_prescript.rowCount()

        subtotal = 0
        for row_no in range(row_count):
            price = self.ui.tableWidget_prescript.item(row_no, 6)
            if price is None:
                continue

            subtotal += number_utils.get_integer(float(price.text()))

        discount = number_utils.get_integer(self.ui.lineEdit_discount.text())
        total = subtotal - discount

        self.ui.lineEdit_subtotal.setText('{0}'.format(subtotal))
        self.ui.lineEdit_total.setText('{0}'.format(total))

    def _discount_changed(self):
        subtotal = number_utils.get_integer(self.ui.lineEdit_subtotal.text())
        discount = number_utils.get_integer(self.ui.lineEdit_discount.text())
        total = subtotal - discount

        self.ui.lineEdit_total.setText('{0}'.format(total))

    def _patient_key_changed(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        if patient_key == '':
            self.ui.lineEdit_name.setText('')
            return

        sql = '''
            SELECT * FROM patient
            WHERE
                PatientKey = {0}
        '''.format(patient_key)
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        self.ui.lineEdit_name.setText(string_utils.xstr(rows[0]['Name']))

    def _set_patient(self):
        if self.ui.radioButton_1.isChecked():
            self.ui.lineEdit_patient_key.setText('')
            self.ui.lineEdit_name.setText('')
            enabled = False
        else:
            enabled = True

        self.ui.label_patient_key.setEnabled(enabled)
        self.ui.lineEdit_patient_key.setEnabled(enabled)
        self.ui.label_name.setEnabled(enabled)
        self.ui.lineEdit_name.setEnabled(enabled)
        self.ui.toolButton_patient_list.setEnabled(enabled)
        self.ui.toolButton_find_patient.setEnabled(enabled)

    def _save_purchase(self):
        case_key, case_date = self._save_medical_record()
        self._save_prescript(case_key, case_date)
        self._save_wait(case_key, case_date)

        self.close_purchase()

    def _get_patient_data(self):
        if self.ui.radioButton_1.isChecked():
            patient_key = 0
            name = '自購藥'
        else:
            patient_key = number_utils.get_integer(self.ui.lineEdit_patient_key.text())
            name = self.ui.lineEdit_name.text()
            if name == '':
                name = '自購藥'

        return patient_key, name

    def _save_medical_record(self):
        patient_key, name = self._get_patient_data()
        case_date = '{0} {1}'.format(
            self.ui.dateEdit_purchase_date.date().toString('yyyy-MM-dd'),
            datetime.datetime.now().time().strftime('%H:%M:%S')
        )
        doctor_done = 'True'
        period = self.ui.comboBox_period.currentText()

        charge_date = None
        charge_period = None
        charge_done = 'False'

        if self.system_settings.field('自動完成批價作業') == 'Y':
            charge_date = case_date
            charge_period = period
            charge_done = 'True'

        fields = [
            'PatientKey', 'Name', 'CaseDate', 'DoctorDate',
            'Period', 'InsType',
            'TreatType',
            'Register', 'Cashier', 'Doctor',
            'SDrugFee', 'SelfTotalFee', 'DiscountFee', 'TotalFee', 'ReceiptFee',
            'DoctorDone',
            'ChargeDate', 'ChargePeriod', 'ChargeDone',
        ]

        data = [
            patient_key,
            name,
            case_date,
            case_date,
            period,
            '自費',
            '自購',
            self.system_settings.field('使用者'),
            self.ui.comboBox_cashier.currentText(),
            self.ui.comboBox_doctor.currentText(),
            self.ui.lineEdit_subtotal.text(),
            self.ui.lineEdit_subtotal.text(),
            self.ui.lineEdit_discount.text(),
            self.ui.lineEdit_total.text(),
            self.ui.lineEdit_total.text(),
            doctor_done,
            charge_date,
            charge_period,
            charge_done,
        ]

        case_key = self.database.insert_record('cases', fields, data)

        return case_key, case_date

    def _save_prescript(self, case_key, case_date):
        row_count = self.ui.tableWidget_prescript.rowCount()
        medicine_set = 2

        fields = [
            'PrescriptNo', 'CaseKey', 'CaseDate', 'MedicineSet', 'MedicineType',
            'MedicineKey', 'MedicineName', 'Dosage', 'Unit', 'Price', 'Amount',
        ]
        for row_no in range(row_count):
            prescript_no = row_no + 1
            medicine_key = self.ui.tableWidget_prescript.item(row_no, 0).text()
            medicine_type = self.ui.tableWidget_prescript.item(row_no, 1).text()
            medicine_name = self.ui.tableWidget_prescript.item(row_no, 2).text()
            unit = self.ui.tableWidget_prescript.item(row_no, 3).text()
            quantity = self.ui.tableWidget_prescript.item(row_no, 4).text()
            sale_price = self.ui.tableWidget_prescript.item(row_no, 5).text()
            amount = self.ui.tableWidget_prescript.item(row_no, 6).text()

            data = [
                prescript_no, case_key, case_date, medicine_set, medicine_type,
                medicine_key, medicine_name, quantity, unit, sale_price, amount,
            ]

            self.database.insert_record('prescript', fields, data)

    def _save_wait(self, case_key, case_date):
        patient_key, name = self._get_patient_data()
        charge_done = 'False'
        if self.system_settings.field('自動完成批價作業') == 'Y':
            charge_done = 'True'

        fields = [
            'CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
            'TreatType', 'InsType', 'Period',
            'Room', 'RegistNo', 'DoctorDone', 'ChargeDone',
        ]

        data = [
            case_key,
            case_date,
            patient_key,
            name,
            '複診',
            '一般門診',
            '自購',
            '自費',
            self.ui.comboBox_period.currentText(),
            1,
            0,
            'True',
            charge_done,
        ]

        self.database.insert_record('wait', fields, data)

    def _patient_picker(self):
        case_date = self.ui.dateEdit_purchase_date.date().toString('yyyy-MM-dd')

        dialog = dialog_medical_record_picker.DialogMedicalRecordPicker(
            self, self.database, self.system_settings, case_date,
        )
        result = dialog.exec_()
        if not result:
            return

        patient_key = dialog.get_patient_key()
        self.ui.lineEdit_patient_key.setText(string_utils.xstr(patient_key))

        dialog.deleteLater()

    def _select_patient(self):
        patient_key = self.ui.lineEdit_patient_key.text()
        dialog = dialog_select_patient.DialogSelectPatient(
            self, self.database, self.system_settings, ''
        )
        if dialog.exec_():
            patient_key = dialog.get_patient_key()

        self.ui.lineEdit_patient_key.setText(patient_key)

        dialog.deleteLater()

    def _set_sales(self):
        if self.sender().objectName() == 'comboBox_cashier' and self.ui.comboBox_cashier.currentText() != '':
            self.ui.comboBox_doctor.setCurrentText(None)
        elif self.sender().objectName() == 'comboBox_doctor' and self.ui.comboBox_doctor.currentText() != '':
            self.ui.comboBox_cashier.setCurrentText(None)
