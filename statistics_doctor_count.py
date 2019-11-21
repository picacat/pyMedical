#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils
from libs import export_utils
from libs import system_utils


# 醫師統計 2019.05.02
class StatisticsDoctorCount(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsDoctorCount, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.period = args[4]
        self.ins_type = args[5]
        self.doctor = args[6]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_DOCTOR_COUNT, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_doctor_count = table_widget.TableWidget(self.ui.tableWidget_doctor_count, self.database)
        self._set_table_width()

    def _set_table_width(self):
        width = [
            110,
            85, 85, 85, 85, 85, 85, 85, 85, 85, 85, 85, 85, 85,
            85, 85, 85, 85, 85, 85, 85, 85]
        self.table_widget_doctor_count.set_table_heading_width(width)

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
        self.ui.tableWidget_doctor_count.setRowCount(0)
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
        self.ui.tableWidget_doctor_count.setRowCount(row_count + 1)

        for row_no, case_date in zip(range(row_count), calendar_list):
            self.ui.tableWidget_doctor_count.setItem(
                row_no, 0, QtWidgets.QTableWidgetItem(case_date)
            )

        self.ui.tableWidget_doctor_count.setItem(
            row_count, 0, QtWidgets.QTableWidgetItem('總計')
        )

    def _calculate_data(self):
        self._reset_data()
        rows = self._read_data()
        self._calculate_ins_count(rows)
        self._calculate_period(rows)
        self._calculate_treat_count(rows)
        self._calculate_subtotal()
        self._calculate_total()
        self._plot_chart()

    def _reset_data(self):
        for row_no in range(self.ui.tableWidget_doctor_count.rowCount()):
            for col_no in range(1, self.ui.tableWidget_doctor_count.columnCount()):
                self.ui.tableWidget_doctor_count.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem('0')
                )
                self.ui.tableWidget_doctor_count.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _read_data(self):
        period_condition = ''
        if self.period != '全部':
            period_condition = ' AND Period = "{0}"'.format(self.period)

        ins_type_condition = ''
        if self.ins_type != '全部':
            ins_type_condition = ' AND InsType = "{0}"'.format(self.ins_type)

        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT  
                CaseKey, CaseDate, Period, InsType, TreatType, Continuance
            FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" 
                {period_condition}
                {ins_type_condition}
                {doctor_condition}
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            period_condition=period_condition,
            ins_type_condition=ins_type_condition,
            doctor_condition=doctor_condition,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_row_no(self, case_date):
        for row_no in range(self.ui.tableWidget_doctor_count.rowCount()):
            case_date_filed = self.ui.tableWidget_doctor_count.item(row_no, 0)
            if case_date_filed is None:
                continue

            if case_date == case_date_filed.text():
                return row_no

        return None

    def _calculate_ins_count(self, rows):
        for row in rows:
            case_date = row['CaseDate'].strftime('%Y-%m-%d')
            ins_type = string_utils.xstr(row['InsType'])
            if ins_type == '健保':
                col_no = 1
            else:
                col_no = 2

            row_no = self._get_row_no(case_date)
            ins_count = self.ui.tableWidget_doctor_count.item(row_no, col_no)
            if ins_count is None:
                ins_count = 0
            else:
                ins_count = number_utils.get_integer(ins_count.text())

            self._set_item_data(row_no, col_no, string_utils.xstr(ins_count + 1))

    def _calculate_period(self, rows):
        for row in rows:
            case_date = row['CaseDate'].strftime('%Y-%m-%d')
            period = string_utils.xstr(row['Period'])

            col_no = 3
            if period == '早班':
                col_no = 3
            elif period == '午班':
                col_no = 4
            elif period == '晚班':
                col_no = 5

            row_no = self._get_row_no(case_date)
            period_count = self.ui.tableWidget_doctor_count.item(row_no, col_no)
            if period_count is None:
                period_count = 0
            else:
                period_count = number_utils.get_integer(period_count.text())

            self._set_item_data(row_no, col_no, string_utils.xstr(period_count + 1))

    def _calculate_treat_count(self, rows):
        for row in rows:
            case_date = row['CaseDate'].strftime('%Y-%m-%d')
            treat_type = string_utils.xstr(row['TreatType'])
            course = number_utils.get_integer(row['Continuance'])
            pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])

            row_no = self._get_row_no(case_date)
            col_no = 6  # 內科
            if treat_type == '針灸治療':
                if pres_days <= 0:
                    if course <= 1:
                        col_no = 7
                    else:
                        col_no = 8
                else:
                    col_no = 9
            elif treat_type == '複雜針灸':
                if pres_days <= 0:
                    if course <= 1:
                        col_no = 11
                    else:
                        col_no = 12
                else:
                    col_no = 13
            elif treat_type == '傷科治療':
                if pres_days <= 0:
                    if course <= 1:
                        col_no = 15
                    else:
                        col_no = 16
                else:
                    col_no = 17
            elif treat_type == '複雜傷科':
                if pres_days <= 0:
                    if course <= 1:
                        col_no = 19
                    else:
                        col_no = 20
                else:
                    col_no = 21

            treat_count = self.ui.tableWidget_doctor_count.item(row_no, col_no)
            if treat_count is None:
                treat_count = 0
            else:
                treat_count = number_utils.get_integer(treat_count.text())

            self._set_item_data(row_no, col_no, string_utils.xstr(treat_count + 1))

    def _set_item_data(self, row_no, col_no, data):
        self.ui.tableWidget_doctor_count.setItem(
            row_no, col_no, QtWidgets.QTableWidgetItem(data)
        )
        self.ui.tableWidget_doctor_count.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )

    def _calculate_subtotal(self):
        for row_no in range(self.ui.tableWidget_doctor_count.rowCount()):
            acupuncture1 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 7).text())
            acupuncture2 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 8).text())
            acupuncture3 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 9).text())
            self._set_item_data(row_no, 10, string_utils.xstr(acupuncture1 + acupuncture2 + acupuncture3))

            c_acupuncture1 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 11).text())
            c_acupuncture2 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 12).text())
            c_acupuncture3 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 13).text())
            self._set_item_data(row_no, 14, string_utils.xstr(c_acupuncture1 + c_acupuncture2 + c_acupuncture3))

            massage1 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 15).text())
            massage2 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 16).text())
            massage3 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 17).text())
            self._set_item_data(row_no, 18, string_utils.xstr(massage1 + massage2 + massage3))

            c_massage1 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 19).text())
            c_massage2 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 20).text())
            c_massage3 = number_utils.get_integer(self.ui.tableWidget_doctor_count.item(row_no, 21).text())
            self._set_item_data(row_no, 22, string_utils.xstr(c_massage1 + c_massage2 + c_massage3))

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
            '{0}至{1}{2}醫師門診人次統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_doctor_count, None,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>醫師人次統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _plot_chart(self):
        while self.ui.verticalLayout_chart.count():
            item = self.ui.verticalLayout_chart.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_outpatient_count_chart()

    def _plot_outpatient_count_chart(self):
        treat_type = ['內科', '針灸', '複針', '傷科', '複傷']
        set0 = QtChart.QBarSet(treat_type[0])
        set1 = QtChart.QBarSet(treat_type[1])
        set2 = QtChart.QBarSet(treat_type[2])
        set3 = QtChart.QBarSet(treat_type[3])
        set4 = QtChart.QBarSet(treat_type[4])

        set0 << number_utils.get_integer(
            self.ui.tableWidget_doctor_count.item(self.ui.tableWidget_doctor_count.rowCount()-1, 6).text(),
        )
        set1 << number_utils.get_integer(
            self.ui.tableWidget_doctor_count.item(self.ui.tableWidget_doctor_count.rowCount()-1, 10).text(),
        )
        set2 << number_utils.get_integer(
            self.ui.tableWidget_doctor_count.item(self.ui.tableWidget_doctor_count.rowCount()-1, 14).text(),
        )
        set3 << number_utils.get_integer(
            self.ui.tableWidget_doctor_count.item(self.ui.tableWidget_doctor_count.rowCount()-1, 18).text(),
        )
        set4 << number_utils.get_integer(
            self.ui.tableWidget_doctor_count.item(self.ui.tableWidget_doctor_count.rowCount()-1, 22).text(),
        )

        series = QtChart.QBarSeries()
        series.append(set0)
        series.append(set1)
        series.append(set2)
        series.append(set3)
        series.append(set4)

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('門診人數統計表')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['門診人數']

        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignBottom)

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(400)
        self.ui.verticalLayout_chart.addWidget(self.chartView)
