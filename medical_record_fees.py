#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from classes import table_widget
from libs import ui_settings
from libs import strings
from libs import number
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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_MEDICAL_RECORD_FEES, self)
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
                QtWidgets.QTableWidgetItem(strings.xstr(fees[1])))

        for fees in cash_fees:
            self.ui.tableWidget_cash_fees.setItem(
                fees[0], 1,
                QtWidgets.QTableWidgetItem(strings.xstr(fees[1])))

        self.ui.tableWidget_ins_fees.setAlternatingRowColors(True)
        self.ui.tableWidget_cash_fees.setAlternatingRowColors(True)

    def calculate_fees(self):
        self.calculate_ins_fees()

    def calculate_ins_fees(self):
        for i in range(self.ui.tableWidget_ins_fees.rowCount()):
            self.ui.tableWidget_ins_fees.setItem(
                i, 0, QtWidgets.QTableWidgetItem(''))

        treatment = self.parent.tab_ins_prescript.combo_box_treatment.currentText()

        ins_diag_fee = charge_utils.get_ins_diag_fee(self.database, self.system_settings)
        pres_days = number.get_integer(self.parent.tab_ins_prescript.ui.comboBox_pres_days.currentText())
        ins_drug_fee = charge_utils.get_ins_drug_fee(self.database, pres_days)
        ins_pharmacy_fee = charge_utils.get_ins_pharmacy_fee(self.database, self.system_settings, ins_drug_fee)
        ins_acupuncture_fee = charge_utils.get_ins_acupuncture_fee(self.database, treatment, ins_drug_fee)
        ins_massage_fee = charge_utils.get_ins_massage_fee(self.database, treatment, ins_drug_fee)
        ins_dislocate_fee = charge_utils.get_ins_dislocate_fee(self.database, treatment, ins_drug_fee)
        ins_care_fee = charge_utils.get_ins_care_fee(self.database, treatment)
        ins_total_fee = \
            ins_diag_fee + ins_drug_fee + ins_pharmacy_fee + \
            ins_acupuncture_fee + ins_massage_fee + ins_dislocate_fee + ins_care_fee

        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
        rows = self.database.select_record(sql)
        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database,
            rows[0]['Share'],
            rows[0]['TreatType'],
            rows[0]['Continuance']
        )
        drug_share_fee = charge_utils.get_drug_share_fee(
            self.database,
            rows[0]['Share'],
            ins_drug_fee,
        )
        ins_apply_fee = ins_total_fee - diag_share_fee - drug_share_fee
        ins_agent_fee = charge_utils.get_ins_agent_fee(
            self.database,
            rows[0]['Share'],
            treatment,
            rows[0]['Continuance'],
            ins_drug_fee,
        )

        ins_fees = [
            [0, ins_diag_fee],
            [1, ins_drug_fee],
            [2, ins_pharmacy_fee],
            [3, ins_acupuncture_fee],
            [4, ins_massage_fee],
            [5, ins_dislocate_fee],
            [6, ins_care_fee],
            [7, ins_total_fee],
            [8, diag_share_fee],
            [9, drug_share_fee],
            [10, ins_apply_fee],
            [11, ins_agent_fee],
        ]

        for fee in ins_fees:
            self.ui.tableWidget_ins_fees.setItem(
                fee[0], 0,
                QtWidgets.QTableWidgetItem(strings.xstr(fee[1])))
