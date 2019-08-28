#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import export_utils
from libs import system_utils


# 醫師門診收入統計 2019.05.10
class StatisticsDoctorIncome(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsDoctorIncome, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.ins_type = args[4]
        self.doctor = args[5]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_DOCTOR_INCOME, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_doctor_income = table_widget.TableWidget(self.ui.tableWidget_doctor_income, self.database)
        self._set_table_width()

    def _set_table_width(self):
        width = [
            110,
            85, 85, 85, 85, 85, 85, 85, 85, 85,
        ]
        self.table_widget_doctor_income.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    def start_calculate(self):
        self.ui.tableWidget_doctor_income.setRowCount(0)
        self._set_statistics_table_heading()
        self._calculate_data()

    def _set_statistics_table_heading(self):
        start_date = datetime.datetime.strptime(self.start_date, '%Y-%m-%d %H:%M:%S').date()
        end_date = datetime.datetime.strptime(self.end_date, '%Y-%m-%d %H:%M:%S').date()
        day_count = (end_date - start_date).days + 1

        calendar_list = []
        for date in (start_date + datetime.timedelta(n) for n in range(day_count)):
            case_date = date.strftime("%Y-%m-%d")
            if case_date not in calendar_list:
                calendar_list.append(case_date)

        row_count = len(calendar_list)
        self.ui.tableWidget_doctor_income.setRowCount(row_count + 1)

        for row_no, case_date in zip(range(row_count), calendar_list):
            self.ui.tableWidget_doctor_income.setItem(
                row_no, 0, QtWidgets.QTableWidgetItem(case_date)
            )

        self.ui.tableWidget_doctor_income.setItem(
            row_count, 0, QtWidgets.QTableWidgetItem('總計')
        )

    def _calculate_data(self):
        self._reset_data()
        rows = self._read_data()
        self._calculate_income(rows)
        self._calculate_refund()
        self._calculate_debt()
        self._calculate_repayment()
        self._calculate_subtotal()
        self._calculate_total()
        self._plot_chart()

    def _reset_data(self):
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            for col_no in range(1, self.ui.tableWidget_doctor_income.columnCount()):
                self.ui.tableWidget_doctor_income.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem('0')
                )
                self.ui.tableWidget_doctor_income.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _read_data(self):
        ins_type_condition = ''
        if self.ins_type != '全部':
            ins_type_condition = ' AND InsType = "{0}"'.format(self.ins_type)

        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT  
                CaseKey, Name, CaseDate, RegistFee, SDiagShareFee, SDrugShareFee, DepositFee, TotalFee
            FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" 
                {ins_type_condition}
                {doctor_condition}
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            ins_type_condition=ins_type_condition,
            doctor_condition=doctor_condition,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_row_no(self, case_date):
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            case_date_field = self.ui.tableWidget_doctor_income.item(row_no, 0)
            if case_date_field is None:
                continue

            if case_date == case_date_field.text():
                return row_no

        return None

    def _calculate_income(self, rows):
        for row in rows:
            case_date = row['CaseDate'].strftime('%Y-%m-%d')
            row_no = self._get_row_no(case_date)
            regist_fee = self._get_cell_fee(row_no, 1) + number_utils.get_integer(row['RegistFee'])
            diag_share_fee = self._get_cell_fee(row_no, 2) + number_utils.get_integer(row['SDiagShareFee'])
            drug_share_fee = self._get_cell_fee(row_no, 3) + number_utils.get_integer(row['SDrugShareFee'])
            deposit_fee = self._get_cell_fee(row_no, 4) + number_utils.get_integer(row['DepositFee'])
            total_fee = self._get_cell_fee(row_no, 8) + number_utils.get_integer(row['TotalFee'])

            self._set_item_data(row_no, 1, string_utils.xstr(regist_fee))
            self._set_item_data(row_no, 2, string_utils.xstr(diag_share_fee))
            self._set_item_data(row_no, 3, string_utils.xstr(drug_share_fee))
            self._set_item_data(row_no, 4, string_utils.xstr(deposit_fee))
            self._set_item_data(row_no, 8, string_utils.xstr(total_fee))

    def _get_cell_fee(self, row_no, col_no):
        cell = self.ui.tableWidget_doctor_income.item(row_no, col_no)

        if cell is None:
            cell_fee = 0
        else:
            cell_fee = number_utils.get_integer(cell.text())

        return cell_fee

    def _set_item_data(self, row_no, col_no, data):
        self.ui.tableWidget_doctor_income.setItem(
            row_no, col_no, QtWidgets.QTableWidgetItem(data)
        )
        self.ui.tableWidget_doctor_income.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )

        if col_no > 0 and number_utils.get_integer(data) < 0:
            self.ui.tableWidget_doctor_income.item(row_no, col_no).setForeground(
                QtGui.QColor('red')
            )

    def _calculate_refund(self):
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            case_date = self.ui.tableWidget_doctor_income.item(row_no, 0)
            if case_date is  None:
                refund = 0
            else:
                refund = self._get_refund(case_date.text())

            self._set_item_data(row_no, 5, string_utils.xstr(refund))

    def _get_refund(self, return_date):
        start_date = '{0} 00:00:00'.format(return_date)
        end_date = '{0} 23:59:59'.format(return_date)

        if self.doctor != '全部':
            doctor_condition = 'AND cases.Doctor = "{0}"'.format(self.doctor)
        else:
            doctor_condition = ''

        sql = '''
            SELECT Fee FROM deposit
                LEFT JOIN cases ON deposit.CaseKey = cases.CaseKey
            WHERE
                ReturnDate BETWEEN "{start_date}" AND "{end_date}"
                {doctor_condition}
        '''.format(
            start_date=start_date,
            end_date=end_date,
            doctor_condition=doctor_condition,
        )

        rows = self.database.select_record(sql)

        return_fee = 0
        for row in rows:
           return_fee += number_utils.get_integer(row['Fee'])

        return -return_fee

    def _calculate_debt(self):
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            case_date = self.ui.tableWidget_doctor_income.item(row_no, 0)
            if case_date is  None:
                debt = 0
            else:
                debt = self._get_debt(case_date.text())

            self._set_item_data(row_no, 6, string_utils.xstr(debt))

    def _get_debt(self, case_date):
        start_date = '{0} 00:00:00'.format(case_date)
        end_date = '{0} 23:59:59'.format(case_date)

        if self.doctor != '全部':
            doctor_condition = 'AND cases.Doctor = "{0}"'.format(self.doctor)
        else:
            doctor_condition = ''

        sql = '''
            SELECT Fee FROM debt
                LEFT JOIN cases ON debt.CaseKey = cases.CaseKey
            WHERE
                debt.CaseDate BETWEEN "{start_date}" AND "{end_date}"
                {doctor_condition}
        '''.format(
            start_date=start_date,
            end_date=end_date,
            doctor_condition=doctor_condition,
        )

        rows = self.database.select_record(sql)

        debt = 0
        for row in rows:
            debt += number_utils.get_integer(row['Fee'])

        return -debt

    def _calculate_repayment(self):
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            case_date = self.ui.tableWidget_doctor_income.item(row_no, 0)
            if case_date is  None:
                repayment = 0
            else:
                repayment = self._get_repayment(case_date.text())

            self._set_item_data(row_no, 7, string_utils.xstr(repayment))

    def _get_repayment(self, case_date):
        start_date = '{0} 00:00:00'.format(case_date)
        end_date = '{0} 23:59:59'.format(case_date)

        if self.doctor != '全部':
            doctor_condition = 'AND cases.Doctor = "{0}"'.format(self.doctor)
        else:
            doctor_condition = ''

        sql = '''
            SELECT Fee1 FROM debt
                LEFT JOIN cases ON debt.CaseKey = cases.CaseKey
            WHERE
                ReturnDate1 BETWEEN "{start_date}" AND "{end_date}"
        '''.format(
            start_date=start_date,
            end_date=end_date,
            doctor_condition=doctor_condition,
        )

        rows = self.database.select_record(sql)

        repayment = 0
        for row in rows:
            repayment += number_utils.get_integer(row['Fee1'])

        return repayment

    def _calculate_subtotal(self):
        subtotal_field_no = 9

        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            subtotal = 0
            for col_no in range(1, subtotal_field_no):
                subtotal += number_utils.get_integer(
                    self.ui.tableWidget_doctor_income.item(row_no, col_no).text()
                )

            self._set_item_data(row_no, subtotal_field_no, string_utils.xstr(subtotal))

    def _calculate_total(self):
        total_list = [0 for i in range(self.ui.tableWidget_doctor_income.columnCount())]
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            for col_no in range(1, self.ui.tableWidget_doctor_income.columnCount()):
                value = number_utils.get_integer(self.ui.tableWidget_doctor_income.item(row_no, col_no).text())
                total_list[col_no] += value

        row_no = self.ui.tableWidget_doctor_income.rowCount() - 1
        for col_no in range(1, len(total_list)):
            self._set_item_data(
                row_no, col_no, string_utils.xstr(total_list[col_no])
            )

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '{0}至{1}{2}醫師門診收入統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_doctor_income,
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>醫師收入統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _plot_chart(self):
        while self.ui.horizontalLayout_income.count():
            item = self.ui.horizontalLayout_income.takeAt(1)
            if item is None:
                break

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_income_chart()

    def _plot_income_chart(self):
        case_date_list = []
        for row_no in range(self.ui.tableWidget_doctor_income.rowCount()):
            case_date_field = self.ui.tableWidget_doctor_income.item(row_no, 0)
            if case_date_field is None:
                continue

            case_date = case_date_field.text()
            if case_date == '總計':
                continue

            case_date_list.append(case_date)

        series = QtChart.QBarSeries()
        bar_set = []
        for i in range(len(case_date_list)):
            case_date = case_date_list[i]
            row_no = self._get_row_no(case_date)
            subtotal = number_utils.get_integer(
                self.ui.tableWidget_doctor_income.item(row_no, 9).text()
            )
            bar_set.append(QtChart.QBarSet(case_date_list[i][8:10]))
            bar_set[i].setColor(QtGui.QColor('green'))
            bar_set[i] << subtotal
            series.append([bar_set[i]])

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('門診收入統計表')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['門診收入']

        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        # chart.legend().setVisible(True)
        # chart.legend().setAlignment(QtCore.Qt.AlignBottom)
        chart.legend().hide()

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(750)
        self.ui.horizontalLayout_income.addWidget(self.chartView)
