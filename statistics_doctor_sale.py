#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from PyQt5.QtChart import *

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import charge_utils
from libs import export_utils
from libs import system_utils


# 醫師自費銷售統計 2019.05.28
class StatisticsDoctorSale(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsDoctorSale, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_DOCTOR_SALE, self)
        self.table_widget_doctor_sale = table_widget.TableWidget(
            self.ui.tableWidget_doctor_sale, self.database
        )
        self.table_widget_sale_summary = table_widget.TableWidget(
            self.ui.tableWidget_sale_summary, self.database
        )
        self.table_widget_doctor_sale.set_column_hidden([0])
        self._set_table_width()

    def _set_table_width(self):
        width = [
            100,
            120, 70, 90, 250, 50, 50, 70, 90, 70, 80, 90
        ]
        self.table_widget_doctor_sale.set_table_heading_width(width)

        width = [300, 70, 90, 80]
        self.table_widget_sale_summary.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_doctor_sale.doubleClicked.connect(self._open_medical_record)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    def start_calculate(self):
        self.ui.tableWidget_doctor_sale.setRowCount(0)
        self._read_data()
        self._calculate_total()
        self._list_sales_summary()
        self._calculate_summary_total()
        self._plot_chart()

    def _read_data(self):
        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND cases.Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT  
                prescript.*, 
                cases.CaseKey, cases.PatientKey, cases.Name, cases.CaseDate, cases.Doctor
            FROM 
                prescript
            LEFT JOIN cases 
                ON prescript.CaseKey = cases.CaseKey
            WHERE
                prescript.MedicineKey >= 2 AND
                Amount > 0 AND
                cases.CaseDate BETWEEN "{start_date}" AND "{end_date}" 
                {doctor_condition}
            ORDER BY cases.CaseKey, prescript.PrescriptKey
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            doctor_condition=doctor_condition,
        )

        self.table_widget_doctor_sale.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        medicine_key = row['MedicineKey']

        doctor = string_utils.xstr(row['Doctor'])
        quantity = number_utils.get_float(row['Dosage'])
        price = number_utils.get_float(row['Price'])
        amount = number_utils.get_float(row['Amount'])
        commission_rate = charge_utils.get_commission_rate(self.database, medicine_key, doctor)
        commission = charge_utils.calc_commission(quantity, amount, commission_rate)

        if commission_rate != '' and '%' not in commission_rate:
            commission_rate = '${0}'.format(commission_rate)

        sale_row = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['MedicineName']),
            quantity,
            string_utils.xstr(row['Unit']),
            price,
            amount,
            commission_rate,
            commission,
            doctor,
        ]

        for column in range(len(sale_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, sale_row[column])
            self.ui.tableWidget_doctor_sale.setItem(row_no, column, item)

            if column in [2, 5, 7, 8, 9, 10]:
                align = QtCore.Qt.AlignRight
            elif column in [6]:
                align = QtCore.Qt.AlignCenter
            else:
                align = QtCore.Qt.AlignLeft

            self.ui.tableWidget_doctor_sale.item(
                row_no, column).setTextAlignment(
                align | QtCore.Qt.AlignVCenter
            )

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '{0}至{1}{2}醫師自費銷售統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_doctor_sale,
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>醫師自費銷售統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _calculate_total(self):
        total_amount = 0
        total_commission = 0

        row_count = self.ui.tableWidget_doctor_sale.rowCount()
        for row_no in range(row_count):
            amount = self.ui.tableWidget_doctor_sale.item(row_no, 8)
            if amount is not None:
                total_amount += number_utils.get_float(amount.text())

            commission = self.ui.tableWidget_doctor_sale.item(row_no, 10)
            if commission is not None:
                total_commission += number_utils.get_float(commission.text())

        self.ui.tableWidget_doctor_sale.insertRow(row_count)
        self.ui.tableWidget_doctor_sale.setItem(
            row_count, 4, QtWidgets.QTableWidgetItem('總計')
        )
        self.ui.tableWidget_doctor_sale.setItem(
            row_count, 8, QtWidgets.QTableWidgetItem(string_utils.xstr(total_amount))
        )
        self.ui.tableWidget_doctor_sale.item(
            row_count, 8).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.ui.tableWidget_doctor_sale.setItem(
            row_count, 10, QtWidgets.QTableWidgetItem(string_utils.xstr(total_commission))
        )
        self.ui.tableWidget_doctor_sale.item(
            row_count, 10).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )

    def _list_sales_summary(self):
        row_count = self.ui.tableWidget_doctor_sale.rowCount()
        for row_no in range(row_count):
            medicine_name = self.ui.tableWidget_doctor_sale.item(row_no, 4)
            if medicine_name is None:
                continue

            medicine_name = medicine_name.text()
            if medicine_name == '總計':
                continue

            quantity = self.ui.tableWidget_doctor_sale.item(row_no, 5)
            if quantity is None:
                quantity = 0
            else:
                quantity = number_utils.get_float(quantity.text())

            amount = self.ui.tableWidget_doctor_sale.item(row_no, 8)
            if amount is None:
                amount = 0
            else:
                amount = number_utils.get_float(amount.text())

            commission = self.ui.tableWidget_doctor_sale.item(row_no, 10)
            if commission is None:
                commission = 0
            else:
                commission = number_utils.get_float(commission.text())

            self._set_to_sale_summary(medicine_name, quantity, amount, commission)

        self.ui.tableWidget_sale_summary.sortItems(2, QtCore.Qt.DescendingOrder)

    def _set_to_sale_summary(self, medicine_name, quantity, amount, commission):
        row_count = self.ui.tableWidget_sale_summary.rowCount()
        medicine_exists = False
        for row_no in range(row_count):
            if medicine_name != self.ui.tableWidget_sale_summary.item(row_no, 0).text():
                continue

            total_quantity = (
                quantity +
                number_utils.get_float(self.ui.tableWidget_sale_summary.item(row_no, 1).text())
            )
            total_amount = (
                    amount +
                    number_utils.get_float(self.ui.tableWidget_sale_summary.item(row_no, 2).text())
            )
            total_commission = (
                    commission +
                    number_utils.get_float(self.ui.tableWidget_sale_summary.item(row_no, 3).text())
            )

            summary_row = [medicine_name, total_quantity, total_amount, total_commission]
            for col_no in range(len(summary_row)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, summary_row[col_no])
                self.ui.tableWidget_sale_summary.setItem(row_no, col_no, item)
                if col_no in [1, 2, 3]:
                    self.ui.tableWidget_sale_summary.item(
                        row_no, col_no).setTextAlignment(
                        QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                    )

            medicine_exists = True
            break

        if not medicine_exists:
            summary_row = [medicine_name, quantity, amount, commission]
            self.ui.tableWidget_sale_summary.insertRow(row_count)

            for col_no in range(len(summary_row)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, summary_row[col_no])
                self.ui.tableWidget_sale_summary.setItem(row_count, col_no, item)
                if col_no in [1, 2, 3]:
                    self.ui.tableWidget_sale_summary.item(
                        row_count, col_no).setTextAlignment(
                        QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                    )

    def _calculate_summary_total(self):
        total_amount = 0
        total_commission = 0

        row_count = self.ui.tableWidget_sale_summary.rowCount()
        for row_no in range(row_count):
            amount = self.ui.tableWidget_sale_summary.item(row_no, 2)
            if amount is not None:
                total_amount += number_utils.get_float(amount.text())

            commission = self.ui.tableWidget_sale_summary.item(row_no, 3)
            if commission is not None:
                total_commission += number_utils.get_float(commission.text())

        self.ui.tableWidget_sale_summary.insertRow(row_count)
        self.ui.tableWidget_sale_summary.setItem(
            row_count, 0, QtWidgets.QTableWidgetItem('總計')
        )
        self.ui.tableWidget_sale_summary.setItem(
            row_count, 2, QtWidgets.QTableWidgetItem(string_utils.xstr(total_amount))
        )
        self.ui.tableWidget_sale_summary.item(
            row_count, 2).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.ui.tableWidget_sale_summary.setItem(
            row_count, 3, QtWidgets.QTableWidgetItem(string_utils.xstr(total_commission))
        )
        self.ui.tableWidget_sale_summary.item(
            row_count, 3).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )

    def _plot_chart(self):
        total_amount = number_utils.get_float(
            self.ui.tableWidget_sale_summary.item(
                self.ui.tableWidget_sale_summary.rowCount()-1, 2
            ).text()
        )

        series = QPieSeries()
        for row_no in range(self.ui.tableWidget_sale_summary.rowCount()):
            medicine_name = self.ui.tableWidget_sale_summary.item(row_no, 0).text()
            amount = number_utils.get_float(self.ui.tableWidget_sale_summary.item(row_no, 2).text())
            total_amount -= amount

            if row_no >= 10 or medicine_name == '總計':
                break

            series.append(medicine_name, amount)
            slice = series.slices()[row_no]
            slice.setExploded()
            slice.setLabelVisible()

        if self.ui.tableWidget_sale_summary.rowCount() > 10:
            series.append('其他', total_amount)
            slice = series.slices()[10]
            slice.setExploded()
            slice.setLabelVisible()

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle('{doctor}醫師自費銷售排行榜Top10'.format(doctor=self.doctor))
        chart.legend().hide()
        chart.setAnimationOptions(QChart.AllAnimations)

        self.chartView = QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedHeight(400)
        self.ui.verticalLayout_chart.addWidget(self.chartView)

    def _open_medical_record(self):
        case_key = self.table_widget_doctor_sale.field_value(0)
        if case_key is None:
            return

        self.parent.parent.open_medical_record(case_key)
