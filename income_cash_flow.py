#!/usr/bin/env python3
# 掛號櫃台結帳 2018.11.15
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton

from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils
from libs import nhi_utils
from libs import personnel_utils


# 掛號櫃台結帳
class IncomeCashFlow(QtWidgets.QMainWindow):
    program_name = '掛號櫃台結帳'

    # 初始化
    def __init__(self, parent=None, *args):
        super(IncomeCashFlow, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.period = args[4]
        self.doctor = args[5]
        self.cashier = args[6]
        self.ui = None

        self.user_name = self.system_settings.field('使用者')
        self.problem_records = []

        self._set_ui()
        self._set_signal()
        self._set_permission()

        self.read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_income(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_INCOME_CASH_FLOW, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.table_widget_registration = table_widget.TableWidget(self.ui.tableWidget_registration, self.database)
        self.table_widget_registration.set_column_hidden([0])
        self.table_widget_charge = table_widget.TableWidget(self.ui.tableWidget_charge, self.database)
        self.table_widget_charge.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_registration.doubleClicked.connect(self.open_medical_record)
        self.ui.tableWidget_charge.doubleClicked.connect(self.open_medical_record)

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

    # 設定欄位寬度
    def _set_table_width(self):
        width = [
            100,
            130, 50, 75, 90, 50, 90, 100, 100, 80, 70, 90, 70, 70, 90, 90, 90, 90
        ]
        self.table_widget_registration.set_table_heading_width(width)

        width = [
            100,
            130, 50, 75, 90, 50, 90, 100, 100, 80, 50, 90, 90, 90, 90, 70, 90, 90
        ]
        self.table_widget_charge.set_table_heading_width(width)

    def open_medical_record(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(self.database, self.program_name, '進入病歷', self.user_name) != 'Y'):
            return

        sender_name = self.sender().objectName()

        if sender_name == 'tableWidget_registration':
            case_key = self.table_widget_registration.field_value(0)
        elif sender_name == 'tableWidget_charge':
            case_key = self.table_widget_charge.field_value(0)
        else:
            return

        if case_key == '':
            return

        self.parent.open_medical_record(case_key, '病歷查詢')

    # 開始統計現金交帳
    def read_data(self):
        self.problem_records = []
        self._read_registration_data()
        self._read_charge_data()
        self._calculate_total()
        if len(self.problem_records) > 0:
            self._display_problem_info()

    # 讀取健保卡基本資料
    def _display_problem_info(self):
        problem_list = ''
        for item_no, item in zip(range(len(self.problem_records)), self.problem_records):
            problem_list += '''
                <tr>
                    <td align=center>{sequence}</td>
                    <td>{name}</td>
                    <td align="right">{total_fee}</td>
                    <td align="right">{debt}</td>
                    <td align="right">{receipt_fee}</td>
                </tr>
            '''.format(
                sequence=item_no+1,
                name=item[0],
                total_fee=item[1],
                debt=item[2],
                receipt_fee=item[2],
            )

        html = '''
            <table align=center cellpadding="2" cellspacing="0" width="98%" style="border-width: 1px; border-style: solid;">
                <thead>
                    <tr bgcolor="LightGray">
                        <th style="text-align: center; padding: 8px">序</th>
                        <th style="padding: 8px">病患姓名</th>
                        <th style="padding: 8px">應收金額</th>
                        <th style="padding: 8px">欠款</th>
                        <th style="padding: 8px">實收金額</th>
                    </tr>
                </thead>
                    {problem_list}
                <tbody>
                </tbody>
            </table>
        '''.format(
            problem_list=problem_list,
        )

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('實收金額疑問')
        msg_box.setText(
            '''
            <font color="red"><h3>應收與實收金額不平衡, 名單如下:</h3></font>
            {html}
        '''.format(
                html=html,
            )
        )
        msg_box.setInformativeText('實收金額有問題')
        msg_box.addButton(QPushButton("確定"), QMessageBox.AcceptRole)
        msg_box.exec_()

    # 計算掛號收費
    def _read_registration_data(self):
        # income_date = database.start_date.split(' ')[0]
        # database.ui.label_registration.setText('掛號收費日期: {0}'.format(mb1))

        self._set_registration_fees()
        self._set_refund_fees()
        self._set_repayment_fees()

        self._calculate_registration_total()

    def _set_registration_fees(self):
        sql = '''
            SELECT 
                cases.*, debt.DebtType, debt.Fee, patient.DiscountType
            FROM cases
                LEFT JOIN debt ON cases.CaseKey = debt.CaseKey
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE 
                cases.CaseDate BETWEEN "{0}" AND "{1}" AND
                (cases.InsType = "健保" OR RegistFee > 0)
        '''.format(
            self.start_date, self.end_date
        )

        if self.period != '全部':
            sql += ' AND cases.Period = "{0}"'.format(self.period)
        if self.doctor != '全部':
            sql += ' AND cases.Doctor = "{0}"'.format(self.doctor)
        if self.cashier != '全部':
            sql += ' AND Register = "{0}"'.format(self.cashier)

        sql += ' ORDER BY cases.CaseDate, FIELD(cases.Period, {0})'.format(
            string_utils.xstr(nhi_utils.PERIOD)[1:-1])

        self.table_widget_registration.set_db_data(sql, self._set_registration_table_data)

    def _set_registration_table_data(self, row_no, row):
        case_key = number_utils.get_integer(row['CaseKey'])

        regist_fee = number_utils.get_integer(row['RegistFee'])
        diag_share_fee = number_utils.get_integer(row['SDiagShareFee'])
        deposit_fee = number_utils.get_integer(row['DepositFee'])

        if string_utils.xstr(row['DebtType']) == '掛號欠款':
            debt_fee = -number_utils.get_integer(row['Fee'])
        else:
            debt_fee = 0

        subtotal = regist_fee + diag_share_fee + deposit_fee + debt_fee

        card = case_utils.get_full_card(row['Card'], row['Continuance'])
        medical_record = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['DiscountType']),
            card,
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(deposit_fee),
            '0',
            string_utils.xstr(debt_fee),
            '0',
            string_utils.xstr(subtotal),
            string_utils.xstr(row['Register']),
        ]

        for col_no in range(len(medical_record)):
            self.ui.tableWidget_registration.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(medical_record[col_no])
            )
            if col_no in [3, 10, 11, 12, 13, 14, 15, 16]:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            if string_utils.xstr(row['InsType']) == '自費':
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('blue')
                )

    def _set_refund_fees(self):
        sql = '''
            SELECT 
                deposit.*, 
                cases.InsType, cases.Share, cases.Card, cases.TreatType, cases.Continuance, cases.RefundFee,
                patient.DiscountType
            FROM deposit 
                LEFT JOIN cases ON deposit.CaseKey = cases.CaseKey
                LEFT JOIN patient ON deposit.PatientKey = patient.PatientKey
            WHERE 
                ReturnDate BETWEEN "{0}" AND "{1}"
        '''.format(
            self.start_date, self.end_date
        )

        if self.period != '全部':
            sql += ' AND deposit.Period = "{0}"'.format(self.period)
        if self.cashier != '全部':
            sql += ' AND Refunder = "{0}"'.format(self.cashier)

        sql += ' ORDER BY DepositDate, FIELD(deposit.Period, {0})'.format(
            string_utils.xstr(nhi_utils.PERIOD)[1:-1])

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row_no = self.ui.tableWidget_registration.rowCount()
        for row in rows:
            self._set_refund_table_data(row_no, row)
            row_no += 1

    def _set_refund_table_data(self, row_no, row):
        self.ui.tableWidget_registration.setRowCount(row_no+1)
        case_key = number_utils.get_integer(row['CaseKey'])

        return_fee = -number_utils.get_integer(row['RefundFee'])
        subtotal = return_fee

        card = case_utils.get_full_card(row['Card'], row['Continuance'])
        medical_record = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['DepositDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['DiscountType']),
            card,
            '0',
            '0',
            '0',
            string_utils.xstr(return_fee),
            '0',
            '0',
            string_utils.xstr(subtotal),
            string_utils.xstr(row['Refunder']),
        ]

        for col_no in range(len(medical_record)):
            self.ui.tableWidget_registration.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(medical_record[col_no])
            )
            if col_no in [3, 10, 11, 12, 13, 14, 15, 16]:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if subtotal < 0:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('red')
                )

    def _set_repayment_fees(self):
        sql = '''
            SELECT 
                debt.*, 
                cases.InsType, cases.Share, cases.Card, cases.TreatType, cases.Continuance,
                patient.DiscountType
            FROM debt 
                LEFT JOIN cases ON debt.CaseKey = cases.CaseKey
                LEFT JOIN patient ON debt.PatientKey = patient.PatientKey
            WHERE 
                ReturnDate1 BETWEEN "{0}" AND "{1}"
        '''.format(
            self.start_date, self.end_date
        )

        if self.period != '全部':
            sql += ' AND debt.Period1 = "{0}"'.format(self.period)
        if self.cashier != '全部':
            sql += ' AND debt.Cashier1 = "{0}"'.format(self.cashier)

        sql += ' ORDER BY debt.CaseDate, FIELD(debt.Period1, {0})'.format(
            string_utils.xstr(nhi_utils.PERIOD)[1:-1])

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row_no = self.ui.tableWidget_registration.rowCount()
        for row in rows:
            self._set_repayment_table_data(row_no, row)
            row_no += 1

    def _set_repayment_table_data(self, row_no, row):
        self.ui.tableWidget_registration.setRowCount(row_no+1)
        case_key = number_utils.get_integer(row['CaseKey'])

        repayment = number_utils.get_integer(row['Fee1'])
        subtotal = repayment

        card = case_utils.get_full_card(row['Card'], row['Continuance'])
        medical_record = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['DiscountType']),
            card,
            '0',
            '0',
            '0',
            '0',
            '0',
            string_utils.xstr(repayment),
            string_utils.xstr(subtotal),
            string_utils.xstr(row['Cashier1']),
        ]

        for col_no in range(len(medical_record)):
            self.ui.tableWidget_registration.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(medical_record[col_no])
            )
            if col_no in [3, 10, 11, 12, 13, 14, 15, 16]:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_registration.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _calculate_registration_total(self):
        row_count = self.ui.tableWidget_registration.rowCount()
        regist_fee, diag_share_fee, deposit_fee, refund_fee, debt_fee, repayment, subtotal = 0, 0, 0, 0, 0, 0, 0
        for row_no in range(row_count):
            regist_fee += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 10).text())
            diag_share_fee += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 11).text())
            deposit_fee += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 12).text())
            refund_fee += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 13).text())
            debt_fee += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 14).text())
            repayment += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 15).text())
            subtotal += number_utils.get_integer(self.ui.tableWidget_registration.item(row_no, 16).text())

        total_record = [
            None, None, None, None,
            '合計',
            None, None, None, None, None,
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(deposit_fee),
            string_utils.xstr(refund_fee),
            string_utils.xstr(debt_fee),
            string_utils.xstr(repayment),
            string_utils.xstr(subtotal),
        ]

        self.ui.tableWidget_registration.setRowCount(row_count+1)

        font = QtGui.QFont()
        font.setBold(True)
        for col_no in range(len(total_record)):
            self.ui.tableWidget_registration.setItem(
                row_count, col_no,
                QtWidgets.QTableWidgetItem(total_record[col_no])
            )
            if col_no in [10, 11, 12, 13, 14, 15, 16]:
                self.ui.tableWidget_registration.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_registration.item(row_count, col_no).setFont(font)

    # 計算批價收費
    def _read_charge_data(self):
        # income_date = database.start_date.split(' ')[0]
        # database.ui.label_charge.setText('批價收費日期: {0}'.format(income_date))

        self._set_charge_fees()
        self._calculate_charge_total()

    def _set_charge_fees(self):
        if self.system_settings.field('櫃台結帳班別') == '掛號班別':
            date_field = 'CaseDate'
            period_field = 'Period'
        else:
            date_field = 'ChargeDate'
            period_field = 'ChargePeriod'

        sql = '''
            SELECT 
                cases.*, debt.DebtType, debt.Fee, patient.DiscountType
            FROM cases
                LEFT JOIN debt ON cases.CaseKey = debt.CaseKey
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE 
                cases.{date_field} BETWEEN "{start_date}" AND "{end_date}" AND 
                ChargeDone = "True"
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            date_field=date_field,
        )

        if self.period != '全部':
            sql += ' AND cases.{period_field} = "{period}"'.format(
                period_field=period_field,
                period=self.period,
            )
        if self.doctor != '全部':
            sql += ' AND cases.Doctor = "{0}"'.format(self.doctor)
        if self.cashier != '全部':
            sql += ' AND cases.Cashier = "{0}"'.format(self.cashier)

        sql += ' ORDER BY cases.CaseDate, FIELD(cases.{period_field}, {period})'.format(
            period_field=period_field,
            period=string_utils.xstr(nhi_utils.PERIOD)[1:-1],
        )

        self.table_widget_charge.set_db_data(sql, self._set_charge_table_data)

    def _set_charge_table_data(self, row_no, row):
        case_key = number_utils.get_integer(row['CaseKey'])
        pres_days = case_utils.get_pres_days(self.database, case_key)

        drug_share_fee = number_utils.get_integer(row['SDrugShareFee'])
        if string_utils.xstr(row['DebtType']) == '批價欠款':
            debt_fee = -number_utils.get_integer(row['Fee'])
        else:
            debt_fee = 0

        receipt_fee = number_utils.get_integer(row['ReceiptFee'])
        total_fee = number_utils.get_integer(row['TotalFee'])
        subtotal = drug_share_fee + receipt_fee

        name = string_utils.xstr(row['Name'])
        card = case_utils.get_full_card(row['Card'], row['Continuance'])
        medical_record = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            name,
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['DiscountType']),
            card,
            string_utils.xstr(pres_days),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(total_fee),
            string_utils.xstr(receipt_fee),
            string_utils.xstr(debt_fee),
            string_utils.xstr(subtotal),
            string_utils.xstr(row['Cashier']),
        ]

        for col_no in range(len(medical_record)):
            self.ui.tableWidget_charge.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(medical_record[col_no])
            )
            if col_no in [3, 10, 12, 13, 14, 15, 16]:
                self.ui.tableWidget_charge.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_charge.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if total_fee > 0:
                self.ui.tableWidget_charge.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('blue')
                )
            if string_utils.xstr(row['TreatType']) == '自購':
                self.ui.tableWidget_charge.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('darkgreen')
                )
            if total_fee + debt_fee != receipt_fee:
                self.ui.tableWidget_charge.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('red')
                )

        if debt_fee < 0:
            self.ui.tableWidget_charge.item(
                row_no, 15).setForeground(
                QtGui.QColor('red')
            )
        if total_fee + debt_fee != receipt_fee:
            self.problem_records.append(
                [name, total_fee, debt_fee, receipt_fee]
            )

    def _calculate_charge_total(self):
        row_count = self.ui.tableWidget_charge.rowCount()
        drug_share_fee, debt_fee, total_fee, receipt_fee, subtotal = 0, 0, 0, 0, 0
        for row_no in range(row_count):
            drug_share_fee += number_utils.get_integer(self.ui.tableWidget_charge.item(row_no, 12).text())
            total_fee += number_utils.get_integer(self.ui.tableWidget_charge.item(row_no, 13).text())
            receipt_fee += number_utils.get_integer(self.ui.tableWidget_charge.item(row_no, 14).text())
            debt_fee += number_utils.get_integer(self.ui.tableWidget_charge.item(row_no, 15).text())
            subtotal += number_utils.get_integer(self.ui.tableWidget_charge.item(row_no, 16).text())

        total_record = [
            None, None, None, None,
            '合計',
            None, None, None, None, None, None, None,
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(total_fee),
            string_utils.xstr(receipt_fee),
            string_utils.xstr(debt_fee),
            string_utils.xstr(subtotal),
        ]

        self.ui.tableWidget_charge.setRowCount(row_count+1)

        font = QtGui.QFont()
        font.setBold(True)
        for col_no in range(len(total_record)):
            self.ui.tableWidget_charge.setItem(
                row_count, col_no,
                QtWidgets.QTableWidgetItem(total_record[col_no])
            )
            if col_no in [12, 13, 14, 15, 16]:
                self.ui.tableWidget_charge.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            self.ui.tableWidget_charge.item(row_count, col_no).setFont(font)

    def _calculate_total(self):
        self.ui.tableWidget_total.setRowCount(0)

        total_fee = (
                number_utils.get_integer(self.ui.tableWidget_registration.item(
                    self.ui.tableWidget_registration.rowCount()-1, 16).text()) +
                number_utils.get_integer(self.ui.tableWidget_charge.item(
                    self.ui.tableWidget_charge.rowCount()-1, 16).text())
        )

        total_rows = [
            ['掛號費', self.ui.tableWidget_registration.item(self.ui.tableWidget_registration.rowCount()-1, 10).text()],
            ['門診負擔', self.ui.tableWidget_registration.item(self.ui.tableWidget_registration.rowCount()-1, 11).text()],
            ['藥品負擔', self.ui.tableWidget_charge.item(self.ui.tableWidget_charge.rowCount()-1, 12).text()],
            ['欠卡費', self.ui.tableWidget_registration.item(self.ui.tableWidget_registration.rowCount()-1, 12).text()],
            ['還卡費', self.ui.tableWidget_registration.item(self.ui.tableWidget_registration.rowCount()-1, 13).text()],
            ['自費還款', self.ui.tableWidget_registration.item(self.ui.tableWidget_registration.rowCount()-1, 15).text()],
            ['自費應收', self.ui.tableWidget_charge.item(self.ui.tableWidget_charge.rowCount()-1, 13).text()],
            ['自費實收', self.ui.tableWidget_charge.item(self.ui.tableWidget_charge.rowCount()-1, 14).text()],
            ['掛號欠款', self.ui.tableWidget_registration.item(self.ui.tableWidget_registration.rowCount()-1, 14).text()],
            ['批價欠款', self.ui.tableWidget_charge.item(self.ui.tableWidget_charge.rowCount()-1, 15).text()],
            ['實收現金', string_utils.xstr(total_fee)],
        ]

        for row_no, row in zip(range(len(total_rows)), total_rows):
            self.ui.tableWidget_total.setRowCount(row_no+1)
            for col_no in range(len(row)):
                self.ui.tableWidget_total.setItem(
                    row_no, col_no,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(row[col_no]))
                )
                if col_no in [1]:
                    self.ui.tableWidget_total.item(
                        row_no, col_no).setTextAlignment(
                        QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                    )
                if row_no in [4, 8, 9]:
                    self.ui.tableWidget_total.item(
                        row_no, col_no).setForeground(
                        QtGui.QColor('red')
                    )

