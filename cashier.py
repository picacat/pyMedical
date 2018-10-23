#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys

from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import date_utils
from libs import number_utils
from libs import case_utils
from classes import table_widget


# 主視窗
class Cashier(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Cashier, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_charge_list('未批價')

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CASHIER, self)
        self.table_widget_charge_list = table_widget.TableWidget(
            self.ui.tableWidget_charge_list, self.database
        )
        self.table_widget_charge_list.set_column_hidden([0, 1])

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_cashier)
        self.ui.action_save.triggered.connect(self._apply_charge)
        self.ui.radioButton_unpaid.clicked.connect(self.read_wait)
        self.ui.radioButton_paid.clicked.connect(self.read_wait)
        self.ui.radioButton_all.clicked.connect(self.read_wait)
        self.ui.tableWidget_charge_list.itemSelectionChanged.connect(self._charge_list_changed)
        self.ui.lineEdit_receipt_drug_share_fee.textChanged.connect(self._calculate_receipt_fee)
        self.ui.lineEdit_receipt_fee.textChanged.connect(self._calculate_receipt_fee)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_cashier(self):
        self.close_all()
        self.close_tab()

    def read_wait(self):
        if self.ui.radioButton_unpaid.isChecked():
            payment = '未批價'
        elif self.ui.radioButton_paid.isChecked():
            payment = '已批價'
        else:
            payment = ''

        self._read_charge_list(payment)

    def _read_charge_list(self, payment=''):
        if payment == '未批價':
            payment = 'AND wait.ChargeDone = "False"'
        elif payment == '已批價':
            payment = 'AND wait.ChargeDone = "True"'
        else:
            payment = ''

        sort = 'ORDER BY FIELD(wait.Period, {0}), wait.RegistNo'.format(
            str(nhi_utils.PERIOD)[1:-1]
        )  # 預設為診號排序
        if self.system_settings.field('看診排序') == '時間排序':
            sort = 'ORDER BY wait.CaseDate'

        sql = '''
            SELECT wait.*, cases.*, patient.Gender, patient.Birthday FROM wait
                LEFT JOIN patient ON patient.PatientKey = wait.PatientKey
                LEFT JOIN cases ON cases.CaseKey = wait.CaseKey
            WHERE
                wait.DoctorDone = "True" 
                {0}
            {1}
        '''.format(payment, sort)

        self.table_widget_charge_list.set_db_data(sql, self._set_table_data)
        self._charge_list_changed()

    def _set_table_data(self, rec_no, rec):
        age_year, age_month = date_utils.get_age(
            rec['Birthday'], rec['CaseDate'])
        if age_year is None:
            age = ''
        else:
            age = '{0}歲'.format(age_year)

        charge_total = (number_utils.get_integer(rec['DrugShareFee']) +
                        number_utils.get_integer(rec['TotalFee']))

        charge_status = '未批價'
        if rec['ChargeDone'] == 'True':
            charge_status = '已批價'

        wait_rec = [
            string_utils.xstr(rec['WaitKey']),
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Gender']),
            age,
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['InsType']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['DrugShareFee']),
            string_utils.xstr(rec['TotalFee']),
            string_utils.xstr(charge_total),
            charge_status,
        ]

        for column in range(len(wait_rec)):
            self.ui.tableWidget_charge_list.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(wait_rec[column])
            )
            if column in [2, 9, 10, 11]:
                self.ui.tableWidget_charge_list.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [4]:
                self.ui.tableWidget_charge_list.item(
                    rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if rec['InsType'] == '自費' or number_utils.get_integer(rec['TotalFee']) > 0:
                self.ui.tableWidget_charge_list.item(
                    rec_no, column).setForeground(
                    QtGui.QColor('blue')
                )

    def _charge_list_changed(self):
        if self.ui.radioButton_unpaid.isChecked():
            enabled = True
        else:
            enabled = False

        if self.ui.tableWidget_charge_list.rowCount() <= 0:
            enabled = False
            self._clear_charge_item()

        self.ui.action_save.setEnabled(enabled)
        self._show_medical_record()

    def _clear_charge_item(self):
        self.ui.textEdit_prescript.setHtml(None)
        self.ui.lineEdit_drug_share_fee.setText(None)
        self.ui.lineEdit_receipt_drug_share_fee.setText(None)
        self.ui.lineEdit_total_fee.setText(None)
        self.ui.lineEdit_receipt_fee.setText(None)
        self.ui.lineEdit_amount.setText(None)
        self.ui.lineEdit_receipt_amount.setText(None)
        self.ui.lineEdit_debt.setText(None)

    def _show_medical_record(self):
        case_key = self.table_widget_charge_list.field_value(1)
        if case_key is None:
            return

        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
        case_rows = self.database.select_record(sql)
        if len(case_rows) <= 0:
            return

        case_row = case_rows[0]

        sql = 'SELECT * FROM prescript WHERE CaseKey = {0}'.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return '<br><center>未開藥</center><br>'

        all_prescript = ''
        for i in range(1, case_utils.MAX_MEDICINE_SET):
            sql = '''
                SELECT * FROM prescript WHERE CaseKey = {0} AND
                MedicineSet = {1}
                ORDER BY PrescriptNo
            '''.format(case_key, i)
            rows = self.database.select_record(sql)

            if len(rows) <= 0:
                if i == 1:
                    continue
                else:
                    break

            prescript_data = ''
            sequence = 0
            for row in rows:
                if row['MedicineName'] is None:
                    continue

                sequence += 1

                dosage = ''
                if row['Dosage'] is not None and row['Dosage'] > 0:
                    dosage = string_utils.xstr(row['Dosage']) + string_utils.xstr(row['Unit'])

                prescript_data += '''
                    <tr>
                        <td align="center">{0}</td>
                        <td style="padding-left: 12px">{1}</td>
                        <td style="padding-right: 12px" align="right">{2}</td>
                        <td style="padding-left: 12px" align="left">{3}</td>
                    </tr>
                '''.format(
                    sequence,
                    string_utils.xstr(row['MedicineName']),
                    dosage,
                    string_utils.xstr(row['Instruction']),
                )

            if i == 1:
                sql = '''
                    SELECT * FROM dosage WHERE
                    CaseKey = {0} AND MedicineSet = 1 
                '''.format(case_key)
                dosage_rows = self.database.select_record(sql)
                dosage_row = dosage_rows[0] if len(dosage_rows) > 0 else None
                if dosage_row is not None:
                    medicine_title = '健保處方-------{0}包{1}天份, {2}服用'.format(
                        number_utils.get_integer(dosage_row['Packages']),
                        number_utils.get_integer(dosage_row['Days']),
                        string_utils.xstr(dosage_row['Instruction'])
                    )
                else:
                    medicine_title = '健保處方'
            else:
                medicine_title = '自費處方{0}'.format(i-1)

            prescript_data = '''
                <table border="1" width="100%">
                    <thead>
                        <tr>
                            <th width="10%">序號</th>
                            <th width="50%" style="padding-left: 12px" align="left">{0}</th>
                            <th width="20%" style="padding-right: 12px" align="right">劑量</th>
                            <th width="20%" style="padding-left: 12px" align="left">服用方式</th>
                        </tr>
                    <thead>
                    <tbody>
                        {1}
                    <tbody>
                </table><br>
            '''.format(medicine_title, prescript_data)
            all_prescript += prescript_data

        self.ui.textEdit_prescript.setHtml(all_prescript)

        self.ui.lineEdit_drug_share_fee.setText(string_utils.xstr(case_row['DrugShareFee']))
        self.ui.lineEdit_receipt_drug_share_fee.setText(string_utils.xstr(case_row['SDrugShareFee']))

        self.ui.lineEdit_total_fee.setText(string_utils.xstr(case_row['TotalFee']))
        self.ui.lineEdit_receipt_fee.setText(string_utils.xstr(case_row['ReceiptFee']))

        if self.ui.radioButton_unpaid.isChecked():
            self.ui.lineEdit_receipt_drug_share_fee.setText(
                self.ui.lineEdit_drug_share_fee.text()
            )
            self.ui.lineEdit_receipt_fee.setText(
                self.ui.lineEdit_total_fee.text()
            )

        self.ui.lineEdit_amount.setText(
            string_utils.xstr(
                number_utils.get_integer(case_row['DrugShareFee']) +
                number_utils.get_integer(case_row['TotalFee'])
            )
        )
        self.ui.lineEdit_receipt_amount.setText(self.ui.lineEdit_amount.text())

        self._calculate_receipt_fee()

    def _apply_charge(self):
        debt = ''
        if number_utils.get_integer(self.ui.lineEdit_debt.text()) > 0:
            debt = '<br><font color="red"><b>此人有欠款{0}元</b></font>'.format(
                self.ui.lineEdit_debt.text())

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('批價存檔')
        msg_box.setText(
            "<font size='4' color='red'><b>確定將病患資料 {0} 批價存檔?</b></font>".format(
                self.table_widget_charge_list.field_value(3)
            )
        )
        msg_box.setInformativeText("注意！批價存檔後, 此筆資料將歸檔至已批價名單!{0}".format(debt))
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        apply_charge = msg_box.exec_()
        if not apply_charge:
            return

        self._save_records()

    def _calculate_receipt_fee(self):
        receipt_drug_share = number_utils.get_integer(
            self.ui.lineEdit_receipt_drug_share_fee.text()
        )
        receipt_fee = number_utils.get_integer(self.ui.lineEdit_receipt_fee.text())
        total_receipt_fee = receipt_drug_share + receipt_fee
        amount = number_utils.get_integer(
            self.ui.lineEdit_amount.text()
        )

        self.ui.lineEdit_receipt_amount.setText(string_utils.xstr(total_receipt_fee))

        if total_receipt_fee < amount:
            self.ui.lineEdit_debt.setText(
                string_utils.xstr(amount - total_receipt_fee)
            )
        else:
            self.ui.lineEdit_debt.setText(None)

    def _save_records(self):
        wait_key = self.table_widget_charge_list.field_value(0)
        case_key = self.table_widget_charge_list.field_value(1)

        self.database.exec_sql('UPDATE wait SET ChargeDone = "True" WHERE WaitKey = {0}'.format(wait_key))

        fields = [
            'Cashier', 'SDrugShareFee', 'ReceiptFee', 'ChargeDone',
        ]

        data = [
            self.system_settings.field('使用者'),
            self.ui.lineEdit_receipt_drug_share_fee.text(),
            self.ui.lineEdit_receipt_fee.text(),
            'True'
        ]

        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

        debt = number_utils.get_integer(self.ui.lineEdit_debt.text())
        if debt > 0:
            self._save_debt(debt)

        self.read_wait()

    def _save_debt(self, debt):
        case_key = self.table_widget_charge_list.field_value(1)
        rows = self.database.select_record('SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key))

        if len(rows) <= 0:
            return

        row = rows[0]
        fields = [
            'CaseKey', 'PatientKey', 'Name', 'CaseDate', 'Period', 'Doctor', 'Fee'
        ]

        data = [
            row['CaseKey'], row['PatientKey'], row['Name'], row['CaseDate'],
            row['Period'], row['Doctor'],
            debt,
        ]

        self.database.insert_record('debt', fields, data)


        fields = ['DebtFee']
        data = [debt]
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)
