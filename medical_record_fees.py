#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import charge_utils
from libs import nhi_utils


# 病歷資料 2018.01.31
class MedicalRecordFees(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecordFees, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.call_from = args[3]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_fees()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_MEDICAL_RECORD_FEES, self)
        self.table_widget_ins_fees = table_widget.TableWidget(self.ui.tableWidget_ins_fees, self.database)
        self.table_widget_cash_fees = table_widget.TableWidget(self.ui.tableWidget_cash_fees, self.database)
        self.ui.tableWidget_ins_fees.resizeRowsToContents()
        self.ui.tableWidget_cash_fees.resizeRowsToContents()
        self._set_table_width()
        self.ins_table_headers = [
            '門診診察費', '內服藥費', '藥事服務費', '針灸治療費', '傷科治療費', '脫臼治療費',
            '健保合計', '門診負擔', '藥品負擔', '健保申請', '代辦費',
        ]
        self.ui.tableWidget_ins_fees.setVerticalHeaderLabels(self.ins_table_headers)

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_calculate_fees.clicked.connect(self.calculate_fees)
        self.ui.tableWidget_cash_fees.keyPressEvent = self._table_widget_cash_fees_key_press

    def _table_widget_cash_fees_key_press(self, event):
        key = event.key()
        current_row = self.ui.tableWidget_cash_fees.currentRow()

        if key in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up]:
            self._calculate_own_expense_total()

        if key in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            self.ui.tableWidget_cash_fees.setCurrentCell(current_row+1, 0)

        return QtWidgets.QTableWidget.keyPressEvent(self.ui.tableWidget_cash_fees, event)

    def _set_table_width(self):
        self.table_widget_ins_fees.set_table_heading_width([75])
        self.table_widget_cash_fees.set_table_heading_width([75])

    def _read_fees(self):
        sql = '''
            SELECT * FROM cases WHERE
            CaseKey = {0}
        '''.format(self.case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]

        if row['ChargeDone'] == 'True':  # 批價完成後, 設定批價鎖定
            self.ui.checkBox_disable_calculate.setChecked(True)

        ins_fees = [
            [-1, row['DiagFee']],
            [0, row['InterDrugFee']],
            [1, row['PharmacyFee']],
            [2, row['AcupunctureFee']],
            [3, row['MassageFee']],
            [4, row['DislocateFee']],
            [5, row['InsTotalFee']],
            [6, row['DiagShareFee']],
            [7, row['DrugShareFee']],
            [8, row['InsApplyFee']],
            [9, row['AgentFee']],
        ]

        cash_fees = [
            [-1, row['RegistFee']],
            [0, row['SDiagShareFee']],
            [1, row['SDrugShareFee']],
            [2, row['DepositFee']],
            [3, row['RefundFee']],
            [4, row['SDiagFee']],
            [5, row['SDrugFee']],
            [6, row['SHerbFee']],
            [7, row['SExpensiveFee']],
            [8, row['SAcupunctureFee']],
            [9, row['SMassageFee']],
            [10, row['SMaterialFee']],
            [11, row['SelfTotalFee']],
            [12, row['DiscountFee']],
            [13, row['TotalFee']],
            [14, row['ReceiptFee']],
            [15, row['DebtFee']],
        ]

        for fees in ins_fees:
            if fees[1] is None:
                fees[1] = 0
            self.ui.tableWidget_ins_fees.setItem(
                fees[0], 1,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fees[1])))

        for fees in cash_fees:
            if fees[1] is None:
                fees[1] = 0
            self.ui.tableWidget_cash_fees.setItem(
                fees[0], 1,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fees[1])))

        if string_utils.xstr(row['TreatType']) in nhi_utils.CARE_TREAT:
            self.ins_table_headers[5] = '加強照護費'
            self.ui.tableWidget_ins_fees.setVerticalHeaderLabels(self.ins_table_headers)

        self.ui.tableWidget_ins_fees.setAlternatingRowColors(True)
        self.ui.tableWidget_cash_fees.setAlternatingRowColors(True)

        self._adjust_table_widget_align()

    def _adjust_table_widget_align(self):
        for row_no in range(self.ui.tableWidget_ins_fees.rowCount()):
            self.ui.tableWidget_ins_fees.item(
                row_no, 0).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
            if row_no in [7, 8]:
                self.ui.tableWidget_ins_fees.item(
                    row_no, 0).setForeground(
                    QtGui.QColor('red')
                )
            if row_no in [10]:
                self.ui.tableWidget_ins_fees.item(
                    row_no, 0).setForeground(
                    QtGui.QColor('darkgreen')
                )

        for row_no in range(self.ui.tableWidget_cash_fees.rowCount()):
            self.ui.tableWidget_cash_fees.item(
                row_no, 0).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

            if row_no in [13]:
                self.ui.tableWidget_cash_fees.item(
                    row_no, 0).setForeground(
                    QtGui.QColor('red')
                )

    def calculate_fees(self):
        self.calculate_ins_fees()
        self.calculate_self_fees(self.parent.tab_list, self.ui.checkBox_disable_calculate)

    def calculate_ins_fees(self):
        if self.parent.tab_registration.ui.comboBox_apply_type.currentText() == '補報差額':
            return

        if self.parent.tab_list[0] is None:
            return

        treat_type = string_utils.xstr(self.parent.tab_registration.comboBox_treat_type.currentText())
        share = string_utils.xstr(self.parent.tab_registration.comboBox_share_type.currentText())
        course = number_utils.get_integer(self.parent.tab_registration.comboBox_course.currentText())
        pres_days = number_utils.get_integer(self.parent.tab_list[0].ui.comboBox_pres_days.currentText())
        pharmacy_type = string_utils.xstr(self.parent.tab_registration.comboBox_pharmacy_type.currentText())
        treatment = self.parent.tab_list[0].combo_box_treatment.currentText()

        tab_ins_care = self.parent.tab_list[11]
        if tab_ins_care is not None:
            table_widget_ins_care = tab_ins_care.ui.tableWidget_prescript
        else:
            table_widget_ins_care = None

        ins_fee = charge_utils.get_ins_fee(
            self.database, self.system_settings, self.case_key,
            treat_type, share, course, pres_days, pharmacy_type, treatment,
            table_widget_ins_care,
        )

        ins_fees = [
            [0, ins_fee['diag_fee']],
            [1, ins_fee['drug_fee']],
            [2, ins_fee['pharmacy_fee']],
            [3, ins_fee['acupuncture_fee']],
            [4, ins_fee['massage_fee']],
            [5, ins_fee['dislocate_fee']],
            [6, ins_fee['ins_total_fee']],
            [7, ins_fee['diag_share_fee']],
            [8, ins_fee['drug_share_fee']],
            [9, ins_fee['ins_apply_fee']],
            [10, ins_fee['agent_fee']],
        ]

        for fee in ins_fees:
            self.ui.tableWidget_ins_fees.setItem(
                fee[0], 0,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fee[1]))
            )

        self._adjust_table_widget_align()

    # 自費批價
    def calculate_self_fees(self, tab_list, check_box_disable_calculate):
        if check_box_disable_calculate.isChecked():  #  鎖定批價
            return

        self_fee = charge_utils.get_self_fee(tab_list)

        self_fee['herb_fee'] = round(self_fee['herb_fee'])  # 四捨五入
        self_fee['expensive_fee'] = round(self_fee['expensive_fee'])
        self_fee['acupuncture_fee'] = round(self_fee['acupuncture_fee'])
        self_fee['massage_fee'] = round(self_fee['massage_fee'])
        self_fee['material_fee'] = round(self_fee['material_fee'])
        self_fee['drug_fee'] = round(self_fee['drug_fee'])

        self_fees = [
            [6, self_fee['drug_fee']],
            [7, self_fee['herb_fee']],
            [8, self_fee['expensive_fee']],
            [9, self_fee['acupuncture_fee']],
            [10, self_fee['massage_fee']],
            [11, self_fee['material_fee']],
        ]

        for fee in self_fees:
            self.ui.tableWidget_cash_fees.setItem(
                fee[0], 0,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fee[1]))
            )

        self._calculate_own_expense_total()
        self._adjust_table_widget_align()

    def _calculate_own_expense_total(self):
        current_row = self.ui.tableWidget_cash_fees.currentRow()
        for row_no in range(self.ui.tableWidget_cash_fees.rowCount()):
            self.ui.tableWidget_cash_fees.setCurrentCell(row_no, 0)

        self.ui.tableWidget_cash_fees.setCurrentCell(current_row, 0)

        diag_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 5, 0)
        drug_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 6, 0)
        herb_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 7, 0)
        expensive_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 8, 0)
        acupuncture_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 9, 0)
        massage_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 10, 0)
        material_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 11, 0)
        discount_fee = charge_utils.get_table_widget_item_fee(self.ui.tableWidget_cash_fees, 13, 0)

        self_total_fee = number_utils.get_integer(
                diag_fee + drug_fee + herb_fee + expensive_fee +
                acupuncture_fee + massage_fee +
                material_fee
        )
        total_fee = number_utils.get_integer(self_total_fee - discount_fee)

        self.ui.tableWidget_cash_fees.setItem(
            12, 0,
            QtWidgets.QTableWidgetItem(string_utils.xstr(self_total_fee))
        )
        self.ui.tableWidget_cash_fees.setItem(
            14, 0,
            QtWidgets.QTableWidgetItem(string_utils.xstr(total_fee))
        )

        self._adjust_table_widget_align()

