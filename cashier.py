#!/usr/bin/env python3
# 批價作業 2018.12.10
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import nhi_utils
from libs import date_utils
from libs import number_utils
from libs import case_utils
from libs import registration_utils
from libs import cshis_utils
from libs import personnel_utils
from libs import charge_utils
from printer import print_prescription
from printer import print_receipt
from printer import print_misc

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
        self.allow_refresh_wait_list = True

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
        self.ui.action_print_misc.setEnabled(False)

        self.table_widget_charge_list.set_column_hidden([0, 1])

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_cashier)
        self.ui.action_save.triggered.connect(self._apply_charge)
        self.ui.action_save_without_print.triggered.connect(self._apply_charge)
        self.ui.action_print_prescription.triggered.connect(lambda: self._print_prescription(None))
        self.ui.action_print_receipt.triggered.connect(lambda: self._print_receipt(None))
        self.ui.action_print_misc.triggered.connect(lambda: self._print_misc(None))
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

        if self.ui.tableWidget_charge_list.rowCount() > 0:
            action_enabled = True
        else:
            action_enabled = False

        self.ui.action_print_prescription.setEnabled(action_enabled)
        self.ui.action_print_receipt.setEnabled(action_enabled)
        self.ui.action_print_misc.setEnabled(action_enabled)

    def _read_charge_list(self, charge_done_script=''):
        if charge_done_script == '未批價':
            charge_done_script = 'AND cases.ChargeDone = "False"'
        elif charge_done_script == '已批價':
            charge_done_script = 'AND cases.ChargeDone = "True"'
        else:
            charge_done_script = ''

        order_script = 'ORDER BY FIELD(cases.Period, {0}), cases.RegistNo'.format(
            str(nhi_utils.PERIOD)[1:-1]
        )  # 預設為診號排序
        if self.system_settings.field('看診排序') == '時間排序':
            order_script = 'ORDER BY cases.CaseDate'

        sql = '''
            SELECT wait.WaitKey, cases.*, patient.Gender, patient.Birthday, patient.DiscountType FROM wait
                LEFT JOIN patient ON patient.PatientKey = wait.PatientKey
                LEFT JOIN cases ON cases.CaseKey = wait.CaseKey
            WHERE
                cases.DoctorDone = "True" 
                {charge_done_script}
            {order_script}
        '''.format(
            charge_done_script=charge_done_script,
            order_script=order_script,
        )

        self.table_widget_charge_list.set_db_data(sql, self._set_table_data)
        self._charge_list_changed()
        if self.table_widget_charge_list.row_count() <= 0:
            enabled = False
        else:
            enabled = True

        self.ui.action_open_medical_record.setEnabled(enabled)
        self.ui.action_print_prescription.setEnabled(enabled)
        self.ui.action_print_receipt.setEnabled(enabled)
        self.ui.action_print_misc.setEnabled(enabled)

        self._set_permission()

    def _set_table_data(self, row_no, row):
        signature = case_utils.extract_security_xml(row['Security'], '醫令時間')
        ins_type = string_utils.xstr(row['InsType'])
        card = string_utils.xstr(row['Card'])
        xcard = string_utils.xstr(row['XCard'])

        if ins_type != '健保' or card in nhi_utils.ABNORMAL_CARD or xcard in nhi_utils.ABNORMAL_CARD:
            ic_wrote = '略'
        elif signature is None:
            ic_wrote = '否'
        else:
            ic_wrote = '是'

        age_year, age_month = date_utils.get_age(
            row['Birthday'], row['CaseDate'])
        if age_year is None:
            age = ''
        else:
            age = '{0}歲'.format(age_year)

        drug_share_fee = number_utils.get_integer(row['DrugShareFee'])
        drug_share_discount_fee = charge_utils.get_drug_share_discount_fee(
            self.database, string_utils.xstr(row['DiscountType'])
        )
        if drug_share_discount_fee is not None:
            drug_share_fee = drug_share_discount_fee

        charge_total = (number_utils.get_integer(drug_share_fee) +
                        number_utils.get_integer(row['TotalFee']))

        charge_status = '未批價'
        if row['ChargeDone'] == 'True':
            charge_status = '已批價'

        wait_rec = [
            string_utils.xstr(row['WaitKey']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['Room']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            age,
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(row['TotalFee']),
            string_utils.xstr(charge_total),
            charge_status,
            ic_wrote,
        ]

        for column in range(len(wait_rec)):
            self.ui.tableWidget_charge_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(wait_rec[column])
            )
            if column in [2, 3, 11, 12, 13]:
                self.ui.tableWidget_charge_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5, 14, 15]:
                self.ui.tableWidget_charge_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費' or number_utils.get_integer(row['TotalFee']) > 0:
                self.ui.tableWidget_charge_list.item(
                    row_no, column).setForeground(
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

        case_key = self.table_widget_charge_list.field_value(1)
        self._show_medical_record(case_key)

    def _clear_charge_item(self):
        self.ui.textEdit_prescript.setHtml(None)
        self.ui.lineEdit_drug_share_fee.setText(None)
        self.ui.lineEdit_receipt_drug_share_fee.setText(None)
        self.ui.lineEdit_total_fee.setText(None)
        self.ui.lineEdit_receipt_fee.setText(None)
        self.ui.lineEdit_debt.setText(None)
        self.ui.lineEdit_total.setText(None)

    def _show_medical_record(self, case_key):
        if case_key in [None, '']:
            return

        sql = '''
            SELECT cases.*, patient.DiscountType FROM cases 
                LEFT JOIN patient on patient.PatientKey = cases.PatientKey
            WHERE 
                CaseKey = {case_key}
        '''.format(
            case_key=case_key,
        )
        case_rows = self.database.select_record(sql)
        if len(case_rows) <= 0:
            return

        case_row = case_rows[0]
        if case_row['InsType'] == '健保':
            card = string_utils.xstr(case_row['Card'])
            if number_utils.get_integer(case_row['Continuance']) >= 1:
                card += '-' + string_utils.xstr(case_row['Continuance'])
            card = '<b>健保</b>: {0}'.format(card)
        else:
            card = '<b>自費</b>'

        medical_record = '<b>日期</b>: {case_date} {card} <b>醫師</b>:{doctor}<hr>'.format(
            case_date=string_utils.xstr(case_row['CaseDate'].date()),
            card=card,
            doctor=string_utils.xstr(case_row['Doctor']),
        )
        remark = case_row['Remark']
        if remark is not None and string_utils.xstr(remark) != '':
            medical_record += '<b>備註</b>: {0}<hr>'.format(string_utils.get_str(remark, 'utf8'))

        prescript_record = case_utils.get_prescript_record(self.database, self.system_settings, case_key)

        html = '''
            <html>
                <head>
                    <meta charset="UTF-8">
                </head>
                <body>
                    {medical_record}
                    {prescript_record}
                </body>
            </html>
        '''.format(
            medical_record=medical_record,
            prescript_record=prescript_record,
        )
        self.ui.textEdit_prescript.setHtml(html)

        drug_share_fee = number_utils.get_integer(case_row['DrugShareFee'])
        drug_share_discount_fee = charge_utils.get_drug_share_discount_fee(
            self.database, string_utils.xstr(case_row['DiscountType'])
        )
        if drug_share_discount_fee is not None:
            drug_share_fee = drug_share_discount_fee

        self.ui.lineEdit_drug_share_fee.setText(string_utils.xstr(drug_share_fee))
        self.ui.lineEdit_receipt_drug_share_fee.setText(string_utils.xstr(drug_share_fee))

        self.ui.lineEdit_total_fee.setText(string_utils.xstr(case_row['TotalFee']))
        self.ui.lineEdit_receipt_fee.setText(string_utils.xstr(case_row['ReceiptFee']))

        self.ui.lineEdit_total.setText(
            string_utils.xstr(
                number_utils.get_integer(drug_share_fee) +
                number_utils.get_integer(case_row['TotalFee'])
            )
        )

        if self.ui.radioButton_unpaid.isChecked():
            self.ui.lineEdit_receipt_drug_share_fee.setText(
                self.ui.lineEdit_drug_share_fee.text()
            )
            self.ui.lineEdit_receipt_fee.setText(
                self.ui.lineEdit_total_fee.text()
            )

        self._calculate_receipt_fee()

    def refresh_wait(self):
        if not self.allow_refresh_wait_list:
            return

        self.read_wait()

    def _apply_charge(self):
        self.allow_refresh_wait_list = False

        sender_name = self.sender().objectName()
        wait_key = self.table_widget_charge_list.field_value(0)
        case_key = self.table_widget_charge_list.field_value(1)
        patient_key = self.table_widget_charge_list.field_value(3)
        patient_name = self.table_widget_charge_list.field_value(4)

        debt = ''
        if number_utils.get_integer(self.ui.lineEdit_debt.text()) > 0:
            debt = '<br><font color="red"><b>此人有欠款{0}元</b></font>'.format(
                self.ui.lineEdit_debt.text())

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('批價存檔')
        msg_box.setText(
            "<font size='4' color='red'><b>確定將病患資料 {patient_name} 批價存檔?</b></font>".format(
                patient_name=patient_name,
            )
        )
        msg_box.setInformativeText("注意！批價存檔後, 此筆資料將歸檔至已批價名單!{0}".format(debt))
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        apply_charge = msg_box.exec_()
        if not apply_charge:
            self.allow_refresh_wait_list = True
            return

        ic_card = None
        need_write_ic_card = cshis_utils.need_write_ic_card(self.database, self.system_settings, case_key, '批價')
        if need_write_ic_card:
            ic_card = cshis.CSHIS(self.database, self.system_settings)
            if not ic_card.insert_correct_ic_card(patient_key):
                return

        self._save_records(wait_key, case_key)
        if sender_name == 'action_save':  # 批價列印
            self._print_prescription(case_key)
            self._print_receipt(case_key)
            self._print_misc(case_key)

        if need_write_ic_card and ic_card is not None:
            ic_card.write_ic_medical_record(case_key, cshis_utils.NORMAL_CARD)

        self.read_wait()
        self.allow_refresh_wait_list = True

    def _calculate_receipt_fee(self):
        receipt_drug_share_fee = number_utils.get_integer(self.ui.lineEdit_receipt_drug_share_fee.text())
        receipt_fee = number_utils.get_integer(self.ui.lineEdit_receipt_fee.text())

        total_receipt_fee = receipt_drug_share_fee + receipt_fee
        total_fee = number_utils.get_integer(self.ui.lineEdit_total.text())

        if total_receipt_fee < total_fee:
            self.ui.lineEdit_debt.setText(
                string_utils.xstr(total_fee - total_receipt_fee)
            )
        else:
            self.ui.lineEdit_debt.setText(None)

    def _save_records(self, wait_key, case_key):
        self.allow_refresh_wait_list = False
        if wait_key in ['', None]:
            return

        if case_key in ['', None]:
            return

        self.database.exec_sql('UPDATE wait SET ChargeDone = "True" WHERE WaitKey = {0}'.format(wait_key))

        s_drug_share_fee = number_utils.get_integer(self.ui.lineEdit_receipt_drug_share_fee.text())
        receipt_fee = number_utils.get_integer(self.ui.lineEdit_receipt_fee.text())

        fields = [
            'Cashier', 'SDrugShareFee', 'ReceiptFee',
            'ChargeDone', 'ChargeDate', 'ChargePeriod',
        ]
        data = [
            self.system_settings.field('使用者'),
            s_drug_share_fee,
            receipt_fee,
            'True',
            date_utils.now_to_str(),
            registration_utils.get_current_period(self.system_settings),
        ]
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

        debt = number_utils.get_integer(self.ui.lineEdit_debt.text())
        if debt > 0:
            self._save_debt(debt, case_key)

    def _save_debt(self, debt, case_key):
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
    def _print_prescription(self, case_key=None):
        sender_name = self.sender().objectName()
        if sender_name == 'action_print_prescription':
            print_type = '選擇列印'
        else:
            print_type = '系統設定'

        if case_key is None:
            case_key = self.table_widget_charge_list.field_value(1)

        print_prescript = print_prescription.PrintPrescription(
            self, self.database, self.system_settings, case_key, print_type)
        print_prescript.print()

        del print_prescript

    # 列印醫療收據
    def _print_receipt(self, case_key=None):
        sender_name = self.sender().objectName()
        if sender_name == 'action_print_receipt':
            print_type = '選擇列印'
        else:
            print_type = '系統設定'

        if case_key is None:
            case_key = self.table_widget_charge_list.field_value(1)

        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, print_type)
        print_charge.print()

        del print_charge

    # 列印其他收據
    def _print_misc(self, case_key=None):
        sender_name = self.sender().objectName()
        if sender_name == 'action_print_misc':
            print_type = '選擇列印'
        else:
            print_type = '系統設定'

        if case_key is None:
            case_key = self.table_widget_charge_list.field_value(1)

        print_other = print_misc.PrintMisc(
            self, self.database, self.system_settings, case_key, print_type)
        print_other.print()

        del print_other

    def _open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '調閱病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_charge_list.field_value(1)
        self.parent.open_medical_record(case_key, '病歷查詢')
