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
class StatisticsInsPerformanceMedicalRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsInsPerformanceMedicalRecord, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_INS_PERFORMANCE_MEDICAL_RECORD, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self._set_table_width()

    def _set_table_width(self):
        width = [
            110,
            85, 85, 85, 85, 85, 85, 85, 85, 85, 85, 85, 85, 85,
            85, 85, 85, 85, 85, 85, 85, 85]
        self.table_widget_medical_record.set_table_heading_width(width)

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
        self.ui.tableWidget_medical_record.setRowCount(0)
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
        self.ui.tableWidget_medical_record.setRowCount(row_count + 1)

        for row_no, case_date in zip(range(row_count), calendar_list):
            self.ui.tableWidget_medical_record.setItem(
                row_no, 0, QtWidgets.QTableWidgetItem(case_date)
            )

        self.ui.tableWidget_medical_record.setItem(
            row_count, 0, QtWidgets.QTableWidgetItem('總計')
        )

    def _calculate_data(self):
        self._reset_data()
        rows = self._read_data()
        self._calculate_ins_performance(rows)
        self._calculate_total()
        self._plot_chart()

    def _reset_data(self):
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            for col_no in range(1, self.ui.tableWidget_medical_record.columnCount()):
                self.ui.tableWidget_medical_record.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem('0')
                )
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def _read_data(self):
        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT  
                *
            FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" 
                {doctor_condition}
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            doctor_condition=doctor_condition,
        )
        rows = self.database.select_record(sql)

        return rows

    def _get_row_no(self, case_date):
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            case_date_field = self.ui.tableWidget_medical_record.item(row_no, 0)
            if case_date_field is None:
                continue

            if case_date == case_date_field.text():
                return row_no

        return None

    @staticmethod
    def _get_item_fee(item):
        if item is None:
            item_fee = 0
        else:
            item_fee = number_utils.get_integer(item.text())

        return item_fee

    def _calculate_ins_performance(self, rows):
        for row in rows:
            case_date = row['CaseDate'].strftime('%Y-%m-%d')
            row_no = self._get_row_no(case_date)
            ins_count = self.ui.tableWidget_medical_record.item(row_no, 1)
            pres_days = self.ui.tableWidget_medical_record.item(row_no, 2)
            diag_fee = self.ui.tableWidget_medical_record.item(row_no, 3)
            drug_fee = self.ui.tableWidget_medical_record.item(row_no, 4)
            pharmacy_fee = self.ui.tableWidget_medical_record.item(row_no, 5)
            acupuncture_fee = self.ui.tableWidget_medical_record.item(row_no, 6)
            massage_fee = self.ui.tableWidget_medical_record.item(row_no, 7)
            dislocate_fee = self.ui.tableWidget_medical_record.item(row_no, 8)
            ins_total_fee = self.ui.tableWidget_medical_record.item(row_no, 9)
            diag_share_fee = self.ui.tableWidget_medical_record.item(row_no, 10)
            drug_share_fee = self.ui.tableWidget_medical_record.item(row_no, 11)
            ins_apply_fee = self.ui.tableWidget_medical_record.item(row_no, 12)

            ins_count = self._get_item_fee(ins_count) + 1
            pres_days = self._get_item_fee(pres_days) + case_utils.get_pres_days(self.database, row['CaseKey'])
            diag_fee = self._get_item_fee(diag_fee) + number_utils.get_integer(row['DiagFee'])
            drug_fee = self._get_item_fee(drug_fee) + number_utils.get_integer(row['InterDrugFee'])
            pharmacy_fee = self._get_item_fee(pharmacy_fee) + number_utils.get_integer(row['PharmacyFee'])
            acupuncture_fee = self._get_item_fee(acupuncture_fee) + number_utils.get_integer(row['AcupunctureFee'])
            massage_fee = self._get_item_fee(massage_fee) + number_utils.get_integer(row['MassageFee'])
            dislocate_fee = self._get_item_fee(dislocate_fee) + number_utils.get_integer(row['DislocateFee'])
            ins_total_fee = self._get_item_fee(ins_total_fee) + number_utils.get_integer(row['InsTotalFee'])
            diag_share_fee = self._get_item_fee(diag_share_fee) + number_utils.get_integer(row['DiagShareFee'])
            drug_share_fee = self._get_item_fee(drug_share_fee) + number_utils.get_integer(row['DrugShareFee'])
            ins_apply_fee = self._get_item_fee(ins_apply_fee) + number_utils.get_integer(row['InsApplyFee'])

            self._set_item_data(row_no, 1, string_utils.xstr(ins_count))
            self._set_item_data(row_no, 2, string_utils.xstr(pres_days))
            self._set_item_data(row_no, 3, string_utils.xstr(diag_fee))
            self._set_item_data(row_no, 4, string_utils.xstr(drug_fee))
            self._set_item_data(row_no, 5, string_utils.xstr(pharmacy_fee))
            self._set_item_data(row_no, 6, string_utils.xstr(acupuncture_fee))
            self._set_item_data(row_no, 7, string_utils.xstr(massage_fee))
            self._set_item_data(row_no, 8, string_utils.xstr(dislocate_fee))
            self._set_item_data(row_no, 9, string_utils.xstr(ins_total_fee))
            self._set_item_data(row_no, 10, string_utils.xstr(diag_share_fee))
            self._set_item_data(row_no, 11, string_utils.xstr(drug_share_fee))
            self._set_item_data(row_no, 12, string_utils.xstr(ins_apply_fee))

    def _set_item_data(self, row_no, col_no, data):
        self.ui.tableWidget_medical_record.setItem(
            row_no, col_no, QtWidgets.QTableWidgetItem(data)
        )
        self.ui.tableWidget_medical_record.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
        )
        if col_no in [10, 11]:
            self.ui.tableWidget_medical_record.item(row_no, col_no).setForeground(
                QtGui.QColor('red')
            )

    def _calculate_total(self):
        total_list = [0 for i in range(self.ui.tableWidget_medical_record.columnCount())]
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            for col_no in range(1, self.ui.tableWidget_medical_record.columnCount()):
                value = number_utils.get_integer(self.ui.tableWidget_medical_record.item(row_no, col_no).text())
                total_list[col_no] += value

        row_no = self.ui.tableWidget_medical_record.rowCount() - 1
        for col_no in range(1, len(total_list)):
            self._set_item_data(
                row_no, col_no, string_utils.xstr(total_list[col_no])
            )

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "醫師健保業績",
            '{0}至{1}{2}醫師病歷健保業績統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_medical_record, None,
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>醫師健保業績統計檔{0}匯出完成.</h3>'.format(excel_file_name),
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
        case_date_list = []
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            case_date_field = self.ui.tableWidget_medical_record.item(row_no, 0)
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
            ins_apply_fee = number_utils.get_integer(
                self.ui.tableWidget_medical_record.item(row_no, 12).text()
            )
            bar_set.append(QtChart.QBarSet(case_date_list[i][8:10]))
            bar_set[i].setColor(QtGui.QColor('green'))
            bar_set[i] << ins_apply_fee
            series.append([bar_set[i]])

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('申報金額統計表')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['申報金額']

        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.setAxisX(axis, series)

        # chart.legend().setVisible(True)
        # chart.legend().setAlignment(QtCore.Qt.AlignBottom)
        chart.legend().hide()

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(500)
        self.ui.verticalLayout_chart.addWidget(self.chartView)
