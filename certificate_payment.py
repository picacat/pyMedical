#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
import datetime

from classes import table_widget
from dialog import dialog_certificate_payment
from dialog import dialog_certificate_query

from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import dialog_utils
from libs import printer_utils


# 醫療費用證明 2018.12.27
class CertificatePayment(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CertificatePayment, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_certificate()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CERTIFICATE_PAYMENT, self)

        self.table_widget_certificate_list = table_widget.TableWidget(
            self.ui.tableWidget_certificate_list, self.database)
        self.table_widget_certificate_list.set_column_hidden([0, 1])

        self.table_widget_certificate_items = table_widget.TableWidget(
            self.ui.tableWidget_certificate_items, self.database)
        self.table_widget_certificate_items.set_column_hidden([0])

        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_certificate_payment)
        self.ui.action_add_certificate.triggered.connect(self._add_certificate)
        self.ui.action_remove_certificate.triggered.connect(self._remove_certificate)
        self.ui.action_print_certificate.triggered.connect(self._print_certificate)
        self.ui.action_query_certificate.triggered.connect(self._query_certificate)
        self.ui.tableWidget_certificate_list.itemSelectionChanged.connect(self._table_item_changed)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_certificate_payment(self):
        self.close_all()
        self.close_tab()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 100, 120, 80, 90, 50, 90, 120, 120, 65, 65]
        self.table_widget_certificate_list.set_table_heading_width(width)

    def _read_certificate(self, sql=None):
        if sql is None:
            start_date = datetime.datetime.now().strftime("%Y-01-01 00:00:00")

            sql = '''
                SELECT certificate.*, cases.ChargeDone FROM certificate
                    LEFT JOIN cases ON cases.CaseKey = certificate.CaseKey
                WHERE
                    CertificateDate >= "{0}" AND
                    CertificateType = "收費證明"
                ORDER BY CertificateKey DESC
            '''.format(start_date)

        self.table_widget_certificate_list.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        charge_done = ''
        if string_utils.xstr(row['ChargeDone']) == 'True':
            charge_done = '是'

        certificate_record = [
            string_utils.xstr(row['CertificateKey']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CertificateDate']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['StartDate']),
            string_utils.xstr(row['EndDate']),
            string_utils.xstr(row['CertificateFee']),
            charge_done,
        ]

        for column in range(len(certificate_record)):
            self.ui.tableWidget_certificate_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(certificate_record[column])
            )
            if column in [3, 9]:
                self.ui.tableWidget_certificate_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5, 10]:
                self.ui.tableWidget_certificate_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _table_item_changed(self):
        certificate_key = self.table_widget_certificate_list.field_value(0)
        if certificate_key is None:
            return

        sql = '''
            SELECT certificate_items.*, cases.Doctor FROM certificate_items 
                LEFT JOIN cases ON certificate_items.CaseKey = cases.CaseKey
            WHERE 
                CertificateKey = {0} 
            ORDER BY CaseDate
        '''.format(certificate_key)
        self.table_widget_certificate_items.set_db_data(sql, self._set_certificate_items_data, set_focus=False)
        self._calculate_items_total()

    def _set_certificate_items_data(self, row_no, row):
        cash_total = (
                number_utils.get_integer(row['RegistFee']) +
                number_utils.get_integer(row['SDiagShareFee']) +
                number_utils.get_integer(row['SDrugShareFee'])
        )
        payment = cash_total + number_utils.get_integer(row['TotalFee'])

        certificate_items_record = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(number_utils.get_integer(row['RegistFee'])),
            string_utils.xstr(number_utils.get_integer(row['SDiagShareFee'])),
            string_utils.xstr(number_utils.get_integer(row['SDrugShareFee'])),
            string_utils.xstr(cash_total),
            string_utils.xstr(number_utils.get_integer(row['InsApplyFee'])),
            string_utils.xstr(number_utils.get_integer(row['TotalFee'])),
            string_utils.xstr(payment),
            string_utils.xstr(row['Doctor']),
        ]

        for col_no in range(len(certificate_items_record)):
            self.ui.tableWidget_certificate_items.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(certificate_items_record[col_no])
            )
            if col_no in range(3, 10):
                self.ui.tableWidget_certificate_items.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _calculate_items_total(self):
        row_count = self.ui.tableWidget_certificate_items.rowCount()

        regist_fee = 0
        diag_share_fee = 0
        drug_share_fee = 0
        cash_fee = 0
        ins_apply_fee = 0
        total_fee = 0
        cash_total = 0
        for row_no in range(row_count):
            regist_fee += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 3).text())
            diag_share_fee += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 4).text())
            drug_share_fee += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 5).text())
            cash_fee += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 6).text())
            ins_apply_fee += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 7).text())
            total_fee += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 8).text())
            cash_total += number_utils.get_integer(self.ui.tableWidget_certificate_items.item(row_no, 9).text())

        total_fee_row = [
            None,
            '合計',
            None,
            string_utils.xstr(regist_fee),
            string_utils.xstr(diag_share_fee),
            string_utils.xstr(drug_share_fee),
            string_utils.xstr(cash_fee),
            string_utils.xstr(ins_apply_fee),
            string_utils.xstr(total_fee),
            string_utils.xstr(cash_total),
        ]

        self.ui.tableWidget_certificate_items.setRowCount(row_count + 1)
        for col_no in range(len(total_fee_row)):
            self.ui.tableWidget_certificate_items.setItem(
                row_count, col_no,
                QtWidgets.QTableWidgetItem(total_fee_row[col_no])
            )
            if col_no >= 3:
                self.ui.tableWidget_certificate_items.item(
                    row_count, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )


    # 開立證明
    def _add_certificate(self):
        dialog = dialog_certificate_payment.DialogCertificatePayment(
            self, self.database, self.system_settings
        )

        if dialog.exec_():
            self._read_certificate()
            self._table_item_changed()

        dialog.close_all()
        dialog.deleteLater()

    def _remove_certificate(self):
        msg_box = dialog_utils.get_message_box(
            '刪除醫療費用證明', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定刪除{0}的診斷證明書?</b></font>'.format(
                self.table_widget_certificate_list.field_value(4)),
            '注意！資料刪除後, 將無法回復!'
        )
        remove_record = msg_box.exec_()
        if not remove_record:
            return

        certificate_key = self.table_widget_certificate_list.field_value(0)
        case_key = self.table_widget_certificate_list.field_value(1)

        self.database.exec_sql('DELETE FROM certificate WHERE CertificateKey = {0}'.format(certificate_key))
        self.database.exec_sql('DELETE FROM certificate_items WHERE CertificateKey = {0}'.format(certificate_key))
        self.database.exec_sql('DELETE FROM cases WHERE CaseKey = {0}'.format(case_key))
        self.database.exec_sql('DELETE FROM wait WHERE CaseKey = {0}'.format(case_key))

        current_row = self.ui.tableWidget_certificate_list.currentRow()
        self.ui.tableWidget_certificate_list.removeRow(current_row)

    def _print_certificate(self):
        printer_utils.print_certificate_payment(
            self, self.database, self.system_settings,
            self.table_widget_certificate_list.field_value(0), 'preview',
        )

    def _query_certificate(self):
        dialog = dialog_certificate_query.DialogCertificateQuery(
            self, self.database, self.system_settings,
            '收費證明',
        )

        if dialog.exec_():
            sql = dialog.sql
            self._read_certificate(sql)

        dialog.close_all()
        dialog.deleteLater()

