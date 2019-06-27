#!/usr/bin/env python3
# 批價作業 2018.12.10
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import nhi_utils
from libs import date_utils
from libs import number_utils
from libs import case_utils
from libs import registration_utils
from libs import cshis_utils
from libs import personnel_utils
from printer import print_prescription
from printer import print_receipt

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 批價作業
class Cashier(QtWidgets.QMainWindow):
    program_name = '批價作業'

    # 初始化
    def __init__(self, parent=None, *args):
        super(Cashier, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()

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
        self.ui.action_print_prescription.setEnabled(False)
        self.ui.action_print_receipt.setEnabled(False)

        self.table_widget_charge_list.set_column_hidden([0, 1])

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_cashier)
        self.ui.action_save.triggered.connect(self._apply_charge)
        self.ui.action_save_without_print.triggered.connect(self._apply_charge)
        self.ui.action_print_prescription.triggered.connect(self._print_prescription)
        self.ui.action_print_receipt.triggered.connect(self._print_receipt)
        self.ui.action_open_medical_record.triggered.connect(self._open_medical_record)

        self.ui.radioButton_unpaid.clicked.connect(self.read_wait)
        self.ui.radioButton_paid.clicked.connect(self.read_wait)
        self.ui.radioButton_all.clicked.connect(self.read_wait)
        self.ui.tableWidget_charge_list.itemSelectionChanged.connect(self._charge_list_changed)
        self.ui.lineEdit_receipt_drug_share_fee.textChanged.connect(self._calculate_receipt_fee)
        self.ui.lineEdit_receipt_fee.textChanged.connect(self._calculate_receipt_fee)

        self.ui.tableWidget_charge_list.doubleClicked.connect(self._open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y':
            self.ui.action_open_medical_record.setEnabled(False)

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

        if payment == '未批價':
            action_enabled = False
        elif self.ui.tableWidget_charge_list.rowCount() > 0:
            action_enabled = True
        else:
            action_enabled = False

        self.ui.action_print_prescription.setEnabled(action_enabled)
        self.ui.action_print_receipt.setEnabled(action_enabled)

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
        if self.table_widget_charge_list.row_count() <= 0:
            self.ui.action_open_medical_record.setEnabled(False)
        else:
            self.ui.action_open_medical_record.setEnabled(True)

        self._set_permission()

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
        self.ui.action_save_without_print.setEnabled(enabled)
        self._show_medical_record()

    def _clear_charge_item(self):
        self.ui.textEdit_prescript.setHtml(None)
        self.ui.lineEdit_drug_share_fee.setText(None)
        self.ui.lineEdit_receipt_drug_share_fee.setText(None)
        self.ui.lineEdit_total_fee.setText(None)
        self.ui.lineEdit_receipt_fee.setText(None)
        self.ui.lineEdit_debt.setText(None)

    def _show_medical_record(self):
        case_key = self.table_widget_charge_list.field_value(1)
        if case_key in [None, '']:
            return

        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
        case_rows = self.database.select_record(sql)
        if len(case_rows) <= 0:
            return

        case_row = case_rows[0]
        html = case_utils.get_prescript_record(self.database, self.system_settings, case_key)
        self.ui.textEdit_prescript.setHtml(html)

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

        self._calculate_receipt_fee()

    def _apply_charge(self):
        sender_name = self.sender().objectName()


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
        if sender_name == 'action_save':
            self._print_receipt()

        self._write_ic_card()

        self.read_wait()

    def _calculate_receipt_fee(self):
        receipt_fee = number_utils.get_integer(self.ui.lineEdit_receipt_fee.text())
        total_fee = number_utils.get_integer(
            self.ui.lineEdit_total_fee.text()
        )

        if receipt_fee < total_fee:
            self.ui.lineEdit_debt.setText(
                string_utils.xstr(total_fee - receipt_fee)
            )
        else:
            self.ui.lineEdit_debt.setText(None)

    def _save_records(self):
        wait_key = self.table_widget_charge_list.field_value(0)
        case_key = self.table_widget_charge_list.field_value(1)

        if wait_key in [None, '']:
            return

        if case_key in [None, '']:
            return

        self.database.exec_sql('UPDATE wait SET ChargeDone = "True" WHERE WaitKey = {0}'.format(wait_key))

        sql = 'SELECT Cashier FROM cases WHERE CaseKey = {0}'.format(case_key)
        row = self.database.select_record(sql)[0]
        cashier = string_utils.xstr(row['Cashier'])
        if cashier == '':
            cashier = self.system_settings.field('使用者')

        fields = [
            'Register', 'Cashier', 'SDrugShareFee', 'ReceiptFee',
            'ChargeDone', 'ChargeDate', 'ChargePeriod',
        ]

        data = [
            self.system_settings.field('使用者'),
            cashier,
            self.ui.lineEdit_receipt_drug_share_fee.text(),
            self.ui.lineEdit_receipt_fee.text(),
            'True',
            date_utils.now_to_str(),
            registration_utils.get_period(self.system_settings),
        ]

        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

        debt = number_utils.get_integer(self.ui.lineEdit_debt.text())
        if debt > 0:
            self._save_debt(debt)

    def _save_debt(self, debt):
        case_key = self.table_widget_charge_list.field_value(1)
        rows = self.database.select_record('SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key))

        if len(rows) <= 0:
            return

        row = rows[0]
        fields = [
            'CaseKey', 'PatientKey', 'DebtType', 'Name', 'CaseDate', 'Period', 'Doctor', 'Fee'
        ]

        data = [
            row['CaseKey'],
            row['PatientKey'],
            '批價欠款',
            row['Name'],
            row['CaseDate'],
            row['Period'],
            row['Doctor'],
            debt,
        ]

        self.database.insert_record('debt', fields, data)


        fields = ['DebtFee']
        data = [debt]
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

    # 列印處方箋
    def _print_prescription(self):
        case_key = self.table_widget_charge_list.field_value(1)
        print_prescript = print_prescription.PrintPrescription(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_prescript.print()

        del print_prescript

    # 列印醫療收據
    def _print_receipt(self):
        sender_name = self.sender().objectName()
        if sender_name == 'action_print_receipt':
            print_type = '選擇列印'
        else:
            print_type = '系統設定'

        case_key = self.table_widget_charge_list.field_value(1)
        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, print_type)
        print_charge.print()

        del print_charge

    # 醫令寫入健保卡
    def _write_ic_card(self):
        case_key = self.table_widget_charge_list.field_value(1)
        if case_key is None:
            return

        sql = 'SELECT InsType, Card, XCard FROM cases WHERE CaseKey = {0}'.format(case_key)
        case_rows = self.database.select_record(sql)
        if len(case_rows) <= 0:
            return

        case_row = case_rows[0]
        ins_type = string_utils.xstr(case_row['InsType'])
        card = string_utils.xstr(case_row['Card'])
        xcard = string_utils.xstr(case_row['XCard'])

        if ((ins_type == '健保') and
                (self.system_settings.field('產生醫令簽章位置') == '批價') and
                (self.system_settings.field('使用讀卡機') == 'Y') and
                (card not in nhi_utils.ABNORMAL_CARD) and
                (xcard not in nhi_utils.ABNORMAL_CARD) and
                (card != '欠卡')):
            ic_card = cshis.CSHIS(self.database, self.system_settings)
            ic_card.write_ic_medical_record(case_key, cshis_utils.NORMAL_CARD)

    def _open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_charge_list.field_value(1)
        self.parent.open_medical_record(case_key, '病歷查詢')
