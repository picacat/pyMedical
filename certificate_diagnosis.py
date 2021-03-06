#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
import datetime

from classes import table_widget
from dialog import dialog_certificate_diagnosis
from dialog import dialog_certificate_query

from libs import ui_utils
from libs import string_utils
from libs import dialog_utils
from libs import printer_utils
from libs import system_utils
from printer import print_receipt


# 診斷證明書 2018.12.24
class CertificateDiagnosis(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CertificateDiagnosis, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CERTIFICATE_DIAGNOSIS, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.table_widget_certificate_list = table_widget.TableWidget(
            self.ui.tableWidget_certificate_list, self.database)
        self.table_widget_certificate_list.set_column_hidden([0, 1])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_certificate_diagnosis)
        self.ui.action_add_certificate.triggered.connect(self._add_certificate)
        self.ui.action_modify_certificate.triggered.connect(self._modify_certificate)
        self.ui.action_remove_certificate.triggered.connect(lambda: self.remove_certificate(show_warning=True))
        self.ui.action_print_certificate.triggered.connect(self._print_certificate)
        self.ui.action_print_receipt.triggered.connect(self._print_receipt)
        self.ui.action_query_certificate.triggered.connect(self._query_certificate)
        self.ui.action_export_certificate_payment.triggered.connect(self._export_certificate_payment)
        self.ui.tableWidget_certificate_list.doubleClicked.connect(self._modify_certificate)
        self.ui.tableWidget_certificate_list.itemSelectionChanged.connect(self._item_changed)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_certificate_diagnosis(self):
        self.close_all()
        self.close_tab()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 100, 120, 80, 100, 80, 100, 120, 120, 100, 300, 350, 100, 70]
        self.table_widget_certificate_list.set_table_heading_width(width)

    def _read_certificate(self, sql=None):
        if sql is None:
            start_date = datetime.datetime.now().strftime("%Y-01-01 00:00:00")

            sql = '''
                SELECT certificate.*, cases.ChargeDone FROM certificate
                    LEFT JOIN cases ON cases.CaseKey = certificate.CaseKey
                WHERE
                    CertificateDate >= "{0}" AND
                    CertificateType = "診斷證明"
                ORDER BY CertificateKey DESC
            '''.format(start_date)

        self.table_widget_certificate_list.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        charge_done = ''
        if string_utils.xstr(row['ChargeDone']) == 'True':
            charge_done = '是'

        treat_type = string_utils.xstr(row['TreatType'])
        if treat_type == '':
            treat_type = '全部'

        certificate_record = [
            string_utils.xstr(row['CertificateKey']),
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CertificateDate']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            treat_type,
            string_utils.xstr(row['StartDate']),
            string_utils.xstr(row['EndDate']),
            string_utils.xstr(row['Doctor']),
            string_utils.get_str(row['Diagnosis'], 'utf8'),
            string_utils.get_str(row['DoctorComment'], 'utf8'),
            string_utils.xstr(row['CertificateFee']),
            charge_done,
        ]

        for column in range(len(certificate_record)):
            self.ui.tableWidget_certificate_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(certificate_record[column])
            )
            if column in [3, 12]:
                self.ui.tableWidget_certificate_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [5, 6, 13]:
                self.ui.tableWidget_certificate_list.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    # 開立證明
    def _add_certificate(self):
        dialog = dialog_certificate_diagnosis.DialogCertificateDiagnosis(
            self, self.database, self.system_settings, None
        )

        if dialog.exec_():
            self._read_certificate()

        dialog.close_all()
        dialog.deleteLater()

    # 修改證明
    def _modify_certificate(self):
        certificate_key = self.table_widget_certificate_list.field_value(0)

        dialog = dialog_certificate_diagnosis.DialogCertificateDiagnosis(
            self, self.database, self.system_settings, certificate_key,
        )

        if dialog.exec_():
            self._read_certificate()

        dialog.close_all()
        dialog.deleteLater()

    def remove_certificate(self, show_warning=True):
        if show_warning:
            msg_box = dialog_utils.get_message_box(
                '刪除診斷證明書', QMessageBox.Warning,
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
        printer_utils.print_certificate_diagnosis(
            self, self.database, self.system_settings,
            self.table_widget_certificate_list.field_value(0), 'preview',
        )

    def _query_certificate(self):
        dialog = dialog_certificate_query.DialogCertificateQuery(
            self, self.database, self.system_settings,
            '診斷證明',
        )

        if dialog.exec_():
            sql = dialog.sql
            self._read_certificate(sql)

        dialog.close_all()
        dialog.deleteLater()

    def _export_certificate_payment(self):
        patient_key = self.table_widget_certificate_list.field_value(3)

        if patient_key is None:
            return

        name = self.table_widget_certificate_list.field_value(4)
        msg_box = dialog_utils.get_message_box(
            '自動產生醫療費用證明書', QMessageBox.Question,
            '<font size="4" color="red"><b>確定自動產生{0}的醫療費用證明書?</b></font>'.format(name),
            '系統將自動產生資料, 請檢視是否正確'
        )
        create_record = msg_box.exec_()
        if not create_record:
            return

        ins_type = self.table_widget_certificate_list.field_value(5)
        treat_type = self.table_widget_certificate_list.field_value(6)
        start_date = self.table_widget_certificate_list.field_value(7)
        end_date = self.table_widget_certificate_list.field_value(8)
        doctor = self.table_widget_certificate_list.field_value(9)

        auto_create_list = [
            patient_key, name, ins_type, treat_type, start_date, end_date, doctor,
        ]

        self.parent.create_certificate_payment(auto_create_list)

    # 列印醫療收據
    def _print_receipt(self):
        case_key = self.table_widget_certificate_list.field_value(1)
        if case_key in ['0', '', None]:
            return

        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, '選擇列印')
        print_charge.print()

        del print_charge

    def _item_changed(self):
        self.ui.action_print_receipt.setEnabled(True)

        case_key = self.table_widget_certificate_list.field_value(1)
        if case_key in ['0', '', None]:
            self.ui.action_print_receipt.setEnabled(False)
