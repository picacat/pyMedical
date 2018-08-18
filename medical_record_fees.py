#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import charge_utils


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
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_calculate_fees.clicked.connect(self.calculate_fees)

    def _set_table_width(self):
        self.table_widget_ins_fees.set_table_heading_width([90])
        self.table_widget_cash_fees.set_table_heading_width([90])

    def _read_fees(self):
        sql = '''
            SELECT * FROM cases WHERE
            CaseKey = {0}
        '''.format(self.case_key)
        row = self.database.select_record(sql)[0]
        ins_fees = [
            [-1, row['DiagFee']],
            [0, row['InterDrugFee']],
            [1, row['PharmacyFee']],
            [2, row['AcupunctureFee']],
            [3, row['MassageFee']],
            [4, row['DislocateFee']],
            [5, row['ExamFee']],
            [6, row['InsTotalFee']],
            [7, row['DiagShareFee']],
            [8, row['DrugShareFee']],
            [9, row['InsApplyFee']],
            [10, row['AgentFee']],
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
        ]

        for fees in ins_fees:
            self.ui.tableWidget_ins_fees.setItem(
                fees[0], 1,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fees[1])))

        for fees in cash_fees:
            self.ui.tableWidget_cash_fees.setItem(
                fees[0], 1,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fees[1])))

        self.ui.tableWidget_ins_fees.setAlternatingRowColors(True)
        self.ui.tableWidget_cash_fees.setAlternatingRowColors(True)

    def calculate_fees(self):
        self.calculate_ins_fees()

    def calculate_ins_fees(self):
        for i in range(self.ui.tableWidget_ins_fees.rowCount()):
            self.ui.tableWidget_ins_fees.setItem(
                i, 0, QtWidgets.QTableWidgetItem(''))

        share = string_utils.xstr(self.parent.tab_registration.comboBox_share_type.currentText())
        course = number_utils.get_integer(self.parent.tab_registration.comboBox_course.currentText())
        pres_days = number_utils.get_integer(self.parent.tab_list[0].ui.comboBox_pres_days.currentText())
        pharmacy_type = string_utils.xstr(self.parent.tab_registration.comboBox_pharmacy_type.currentText())
        treatment = self.parent.tab_list[0].combo_box_treatment.currentText()

        ins_fee = charge_utils.get_ins_fee(
            self.database, self.system_settings,
            share, course, pres_days, pharmacy_type, treatment
        )

        ins_fees = [
            [0, ins_fee['diag_fee']],
            [1, ins_fee['drug_fee']],
            [2, ins_fee['pharmacy_fee']],
            [3, ins_fee['acupuncture_fee']],
            [4, ins_fee['massage_fee']],
            [5, ins_fee['dislocate_fee']],
            [6, ins_fee['care_fee']],
            [7, ins_fee['ins_total_fee']],
            [8, ins_fee['diag_share_fee']],
            [9, ins_fee['drug_share_fee']],
            [10, ins_fee['ins_apply_fee']],
            [11, ins_fee['agent_fee']],
        ]

        for fee in ins_fees:
            self.ui.tableWidget_ins_fees.setItem(
                fee[0], 0,
                QtWidgets.QTableWidgetItem(string_utils.xstr(fee[1])))
