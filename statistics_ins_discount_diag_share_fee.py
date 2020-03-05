#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import charge_utils
from libs import export_utils
from libs import system_utils
from libs import personnel_utils


# 免收門診負擔統計 2020.02.11
class StatisticsInsDiscountDiagShareFee(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsInsDiscountDiagShareFee, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.doctor = args[4]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_INS_DISCOUNT_DIAG_SHARE_FEE, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self.table_widget_medical_record.set_column_hidden([0])
        self._set_table_width()

    def _set_table_width(self):
        width = [
            100,
            120, 50, 100, 100, 50, 90, 90,
            100, 90, 100, 130, 130, 130, 400,
        ]
        self.table_widget_medical_record.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_medical_record.doubleClicked.connect(self.open_medical_record)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    def open_medical_record(self):
        if (self.parent.user_name != '超級使用者' and
                personnel_utils.get_permission(
                    self.database, self.parent.program_name, '進入病歷', self.user_name) != 'Y'):
            return

        case_key = self.table_widget_medical_record.field_value(0)
        if case_key == '':
            return

        self.parent.parent.open_medical_record(case_key, '病歷查詢')

    def start_calculate(self):
        self._calculate_data()

    def _calculate_data(self):
        self._read_data()

    def _read_data(self):
        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database, '基層醫療', '內科', None,
        )
        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT  
                CaseKey, CaseDate, Period, Share, TreatType, Doctor, Continuance, 
                DiagShareFee, SDiagShareFee,
                patient.*
            FROM cases
                LEFT JOIN patient ON patient.PatientKey = cases.PatientKey
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                cases.InsType = "健保" AND
                SDiagShareFee < {diag_share_fee} 
                {doctor_condition}
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            diag_share_fee=diag_share_fee,
            doctor_condition=doctor_condition,
        )

        self.table_widget_medical_record.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        medical_record = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Continuance']),
            number_utils.get_integer(row['DiagShareFee']),
            number_utils.get_integer(row['SDiagShareFee']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['PatientKey']),
            string_utils.get_mask_name(row['Name']),
            string_utils.get_mask_id(row['ID'], 4),
            string_utils.xstr(row['Telephone']),
            string_utils.xstr(row['Cellphone']),
            string_utils.xstr(row['Address'])
        ]

        for col_no in range(len(medical_record)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, medical_record[col_no])
            self.ui.tableWidget_medical_record.setItem(row_no, col_no, item)

            if col_no in [6, 7, 9]:
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2, 5]:
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def _calculate_total(self):
        total_list = [0 for i in range(self.ui.tableWidget_doctor_count.columnCount())]
        for row_no in range(self.ui.tableWidget_doctor_count.rowCount()):
            for col_no in range(1, self.ui.tableWidget_doctor_count.columnCount()):
                value = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, col_no).text())
                total_list[col_no] += value

        row_no = self.ui.tableWidget_doctor_count.rowCount() - 1
        for col_no in range(1, len(total_list)):
            self._set_item_data(
                row_no, col_no, string_utils.xstr(total_list[col_no])
            )

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '{0}至{1}{2}醫師免收門診負擔統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_medical_record, [0],
            [5, 6, 7, 9],
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>免收門診負擔統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )
