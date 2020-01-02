#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import massage_utils
from libs import export_utils
from libs import system_utils


# 養生館付款統計 2019.12.06
class StatisticsMassagePayment(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMassagePayment, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.period = args[4]
        self.massager = args[5]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MASSAGE_PAYMENT, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_massage_payment = table_widget.TableWidget(self.ui.tableWidget_massage_payment, self.database)
        self._set_payment_columns()
        self._set_table_width()

    def _set_payment_columns(self):
        header_item = [
            '消費日期', '班別',
        ]
        header_item += massage_utils.PAYMENT_ITEMS
        header_item += ['實收金額']

        self.ui.tableWidget_massage_payment.setColumnCount(len(header_item))
        for col_no in range(len(header_item)):
            self.ui.tableWidget_massage_payment.setHorizontalHeaderItem(
                col_no, QtWidgets.QTableWidgetItem(header_item[col_no])
            )

    def _set_table_width(self):
        width = [110, 50]
        width += [100 for i in range(len(massage_utils.PAYMENT_ITEMS))]
        width += [85]
        self.table_widget_massage_payment.set_table_heading_width(width)

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
        self.ui.tableWidget_massage_payment.setRowCount(0)
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
        self.ui.tableWidget_massage_payment.setRowCount(row_count + 1)

        for row_no, case_date in zip(range(row_count), calendar_list):
            self.ui.tableWidget_massage_payment.setItem(
                row_no, 0, QtWidgets.QTableWidgetItem(case_date)
            )
            self.ui.tableWidget_massage_payment.setItem(
                row_no, 1, QtWidgets.QTableWidgetItem(self.period)
            )

        self.ui.tableWidget_massage_payment.setItem(
            row_count, 0, QtWidgets.QTableWidgetItem('總計')
        )

    def _calculate_data(self):
        self._reset_data()
        rows = self._read_data()
        self._set_data(rows)
        # database._plot_chart()

    def _reset_data(self):
        font = QtGui.QFont()
        font.setBold(True)

        for row_no in range(self.ui.tableWidget_massage_payment.rowCount()):
            for col_no in range(2, self.ui.tableWidget_massage_payment.columnCount()):
                self.ui.tableWidget_massage_payment.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem('0')
                )
                self.ui.tableWidget_massage_payment.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
                if col_no == len(massage_utils.PAYMENT_ITEMS) + 2:
                    self.ui.tableWidget_massage_payment.item(row_no, col_no).setFont(font)

    def _read_data(self):
        period_condition = ''
        if self.period != '全部':
            period_condition = ' AND Period = "{0}"'.format(self.period)

        massager_condition = ''
        if self.massager != '全部':
            massager_condition = ' AND Doctor = "{0}"'.format(self.massager)

        sql = '''
            SELECT
                massage_cases.*, massage_payment.*
            FROM massage_cases
                LEFT JOIN massage_payment
                ON massage_payment.MassageCaseKey = massage_cases.MassageCaseKey
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" 
                {period_condition}
                {massager_condition}
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            period_condition=period_condition,
            massager_condition=massager_condition,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_row_no(self, case_date):
        for row_no in range(self.ui.tableWidget_massage_payment.rowCount()):
            case_date_field = self.ui.tableWidget_massage_payment.item(row_no, 0)
            if case_date_field is None:
                continue

            if case_date == case_date_field.text():
                return row_no

        return None

    def _get_col_no(self, payment_item):
        for col_no in range(self.ui.tableWidget_massage_payment.columnCount()):
            header = self.ui.tableWidget_massage_payment.horizontalHeaderItem(col_no).text()

            if payment_item == header:
                return col_no

        return None

    def _set_data(self, rows):
        total_row_no = self.ui.tableWidget_massage_payment.rowCount() - 1
        subtotal_col_no = len(massage_utils.PAYMENT_ITEMS) + 2

        for row in rows:
            case_date = row['CaseDate'].strftime('%Y-%m-%d')
            payment_item = row['PaymentType']
            if payment_item is None:  # 沒有付款資料
                continue

            row_no = self._get_row_no(case_date)
            col_no = self._get_col_no(payment_item)

            amount = number_utils.get_integer(row['Amount'])
            payment = self._get_cell_fee(row_no, col_no) + amount
            subtotal = number_utils.get_integer(
                self.ui.tableWidget_massage_payment.item(row_no, subtotal_col_no).text()
            ) + amount

            total = number_utils.get_integer(
                self.ui.tableWidget_massage_payment.item(total_row_no, col_no).text()
            ) + amount

            self._set_item_data(row_no, col_no, string_utils.xstr(payment))
            self._set_item_data(row_no, subtotal_col_no, string_utils.xstr(subtotal))
            self._set_item_data(total_row_no, col_no, string_utils.xstr(total))

        total_payment = 0
        for col_no in range(2, subtotal_col_no):
            total_payment += number_utils.get_integer(
                self.ui.tableWidget_massage_payment.item(total_row_no, col_no).text()
            )
        self._set_item_data(total_row_no, subtotal_col_no, string_utils.xstr(total_payment))

    def _get_cell_fee(self, row_no, col_no):
        cell = self.ui.tableWidget_massage_payment.item(row_no, col_no)

        if cell is None:
            cell_fee = 0
        else:
            cell_fee = number_utils.get_integer(cell.text())

        return cell_fee

    def _set_item_data(self, row_no, col_no, data):
        font = QtGui.QFont()
        font.setBold(True)

        self.ui.tableWidget_massage_payment.setItem(
            row_no, col_no, QtWidgets.QTableWidgetItem(data)
        )
        self.ui.tableWidget_massage_payment.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )

        if col_no == len(massage_utils.PAYMENT_ITEMS) + 2:
            self.ui.tableWidget_massage_payment.item(row_no, col_no).setFont(font)

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '{0}至{1}{2}養生館消費人次統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.massager
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options=options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_massage_payment, None,
            [1, 2, 3, 4, 5, 6, 7, 8, 9],
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>養生館消費人次統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _plot_chart(self):
        while self.ui.verticalLayout_chart.count():
            item = self.ui.verticalLayout_chart.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_massage_count_chart()

    def _plot_massage_count_chart(self):
        series = QtChart.QBarSeries()

        massage_type = ['早班服務', '午班服務', '晚班服務', '早班購物', '午班購物', '晚班購物']
        massage_col_no = [1, 2, 3, 5, 6, 7]

        set_list = []
        for i in range(len(massage_type)):
            set_list.append(QtChart.QBarSet(massage_type[i]))
            set_list[i] << number_utils.get_integer(
                self.ui.tableWidget_massage_payment.item(
                    self.ui.tableWidget_massage_payment.rowCount()-1, massage_col_no[i]).text()
            )
            series.append(set_list[i])

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('消費人數統計表')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['養生館消費人數']

        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignBottom)

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(600)
        self.ui.verticalLayout_chart.addWidget(self.chartView)
