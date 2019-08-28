#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from classes import table_widget
from libs import ui_utils
from libs import case_utils
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
        system_utils.set_css(self, self.system_settings)
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
            110, 70, 85, 250, 50, 50, 50, 60, 85, 70, 70, 85
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
                prescript.MedicineSet >= 2 AND
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
        self._insert_discount()

    def _set_table_data(self, row_no, row):
        case_key = row['CaseKey']
        medicine_key = row['MedicineKey']
        medicine_set = row['MedicineSet']

        pres_days = case_utils.get_pres_days(self.database, case_key, medicine_set)
        if pres_days == 0:
            pres_days = 1

        doctor = string_utils.xstr(row['Doctor'])
        quantity = number_utils.get_float(row['Dosage'])
        price = number_utils.get_float(row['Price'])
        amount = number_utils.get_float(row['Amount']) * pres_days
        commission_rate = charge_utils.get_commission_rate(self.database, medicine_key, doctor)
        commission = charge_utils.calc_commission(quantity, amount, commission_rate)

        if commission_rate != '' and '%' not in commission_rate:
            commission_rate = '${0}'.format(commission_rate)

        sale_row = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['MedicineName']),
            pres_days,
            quantity,
            string_utils.xstr(row['Unit']),
            price,
            amount,
            commission_rate,
            commission,
            doctor,
        ]

        for col_no in range(len(sale_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, sale_row[col_no])
            self.ui.tableWidget_doctor_sale.setItem(row_no, col_no, item)

            if col_no in [2, 5, 6, 8, 9, 10, 11]:
                align = QtCore.Qt.AlignRight
            elif col_no in [7]:
                align = QtCore.Qt.AlignCenter
            else:
                align = QtCore.Qt.AlignLeft

            self.ui.tableWidget_doctor_sale.item(
                row_no, col_no).setTextAlignment(
                align | QtCore.Qt.AlignVCenter
            )
            if price < 0:
                self.ui.tableWidget_doctor_sale.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('red')
                )

    # 計算要插入的折扣rows
    def _get_discount_count(self):
        discount_count = 0
        discount_list = []
        for row_no in range(self.ui.tableWidget_doctor_sale.rowCount()):  # 計算要插入的折扣rows count
            case_key = self.ui.tableWidget_doctor_sale.item(row_no, 0)
            if case_key is None:
                continue

            sql = '''
                SELECT CaseKey, DiscountFee FROM cases
                WHERE
                    CaseKey = {case_key} and
                    DiscountFee > 0
            '''.format(
                case_key=case_key.text(),
            )
            rows = self.database.select_record(sql)
            if len(rows) > 0:
                case_key = rows[0]['CaseKey']
                if case_key not in discount_list:
                    discount_list.append(case_key)
                    discount_count += 1

        return discount_count

    def _insert_discount(self):
        row_count = self.ui.tableWidget_doctor_sale.rowCount() + self._get_discount_count()

        last_patient_key = self.ui.tableWidget_doctor_sale.item(0, 2).text()
        last_case_key = self.ui.tableWidget_doctor_sale.item(0, 0).text()
        for row_no in range(row_count):
            if self.ui.tableWidget_doctor_sale.item(row_no, 2) is None:
                patient_key = 0
            else:
                patient_key = self.ui.tableWidget_doctor_sale.item(row_no, 2).text()

            if patient_key != last_patient_key:
                self._check_discount_row(row_no, last_case_key)

            last_patient_key = patient_key
            last_case_key = self.ui.tableWidget_doctor_sale.item(row_no, 0).text()

    def _check_discount_row(self, row_no, case_key):
        sql = '''
            SELECT CaseKey, PatientKey, CaseDate, Name, Doctor, DiscountFee FROM cases
            WHERE
                CaseKey = {case_key}
        '''.format(
            case_key=case_key,
        )
        rows = self.database.select_record(sql)
        discount_fee = number_utils.get_integer(rows[0]['DiscountFee'])
        if discount_fee > 0:  # 有折扣
            self._insert_discount_row(row_no, rows[0], discount_fee)

    def _insert_discount_row(self, row_no, row, discount_fee):
        self.ui.tableWidget_doctor_sale.insertRow(row_no)
        discount_row = {}
        discount_row['CaseKey'] = row['CaseKey']
        discount_row['CaseDate'] = row['CaseDate']
        discount_row['PatientKey'] = row['PatientKey']
        discount_row['Name'] = row['Name']
        discount_row['MedicineName'] = '折扣'
        discount_row['MedicineSet'] = 0
        discount_row['PresDays'] = 1
        discount_row['Dosage'] = 1
        discount_row['Unit'] = '次'
        discount_row['Price'] = -discount_fee
        discount_row['Amount'] = -discount_fee
        discount_row['MedicineKey'] = None
        discount_row['Doctor'] = row['Doctor']

        self._set_table_data(row_no, discount_row)

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
            amount = self.ui.tableWidget_doctor_sale.item(row_no, 9)
            if amount is not None:
                total_amount += number_utils.get_float(amount.text())

            commission = self.ui.tableWidget_doctor_sale.item(row_no, 11)
            if commission is not None:
                total_commission += number_utils.get_float(commission.text())

        self.ui.tableWidget_doctor_sale.insertRow(row_count)
        self.ui.tableWidget_doctor_sale.setItem(
            row_count, 4, QtWidgets.QTableWidgetItem('總計')
        )
        total_amount = round(total_amount)
        self.ui.tableWidget_doctor_sale.setItem(
            row_count, 9, QtWidgets.QTableWidgetItem(string_utils.xstr(total_amount))
        )
        self.ui.tableWidget_doctor_sale.item(
            row_count, 9).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        self.ui.tableWidget_doctor_sale.setItem(
            row_count, 11, QtWidgets.QTableWidgetItem(string_utils.xstr(total_commission))
        )
        self.ui.tableWidget_doctor_sale.item(
            row_count, 11).setTextAlignment(
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

            quantity = self.ui.tableWidget_doctor_sale.item(row_no, 6)
            if quantity is None:
                quantity = 0
            else:
                quantity = number_utils.get_float(quantity.text())

            amount = self.ui.tableWidget_doctor_sale.item(row_no, 9)
            if amount is None:
                amount = 0
            else:
                amount = number_utils.get_float(amount.text())

            commission = self.ui.tableWidget_doctor_sale.item(row_no, 11)
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
                if total_amount < 0:
                    self.ui.tableWidget_sale_summary.item(
                        row_no, col_no).setForeground(
                        QtGui.QColor('red')
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
        total_amount = round(total_amount)
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

        series = QtChart.QPieSeries()
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

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('{doctor}醫師自費銷售排行榜Top10'.format(doctor=self.doctor))
        chart.legend().hide()
        chart.setAnimationOptions(QtChart.QChart.AllAnimations)

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedHeight(400)
        self.ui.verticalLayout_chart.addWidget(self.chartView)

    def _open_medical_record(self):
        case_key = self.table_widget_doctor_sale.field_value(0)
        if case_key is None:
            return

        self.parent.parent.open_medical_record(case_key)
