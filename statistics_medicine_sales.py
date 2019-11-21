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
from libs import case_utils


# 用藥統計內容 2019.08.02
class StatisticsMedicineSales(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMedicineSales, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.start_date = args[2]
        self.end_date = args[3]
        self.ins_type = args[4]
        self.doctor = args[5]
        self.medicine_type = args[6]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MEDICINE_SALES, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_medicine_sales = table_widget.TableWidget(
            self.ui.tableWidget_medicine_sales, self.database
        )
        self._set_table_width()

    def _set_table_width(self):
        width = [
            250,
            80, 50, 90, 90,
        ]
        self.table_widget_medicine_sales.set_table_heading_width(width)

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
        self.ui.tableWidget_medicine_sales.setRowCount(0)
        ins_type_condition = ''
        if self.ins_type != '全部':
            ins_type_condition = 'cases.InsType = "{0}" AND'.format(self.ins_type)

        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = 'cases.Doctor = "{0}" AND'.format(self.doctor)

        sql = '''
            SELECT 
                prescript.MedicineName, prescript.Unit, 
                IFNULL(SUM(prescript.Dosage * IF(dosage.Days, dosage.Days, 1)), 0) AS TotalDosage, 
                medicine.InPrice, medicine.SalePrice
            FROM prescript
                LEFT JOIN cases ON prescript.CaseKey = cases.CaseKey
                LEFT JOIN medicine ON prescript.MedicineKey = medicine.MedicineKey
                LEFT JOIN dosage ON prescript.CaseKey = dosage.CaseKey
            WHERE
                cases.CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                {ins_type_condition}
                {doctor_condition}
                (prescript.MedicineSet = dosage.MedicineSet OR dosage.MedicineSet IS NULL) AND
                prescript.MedicineType = "{medicine_type}" AND
                prescript.Dosage > 0
            GROUP BY prescript.MedicineName
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            ins_type_condition=ins_type_condition,
            doctor_condition=doctor_condition,
            medicine_type=self.medicine_type,
        )
        self.table_widget_medicine_sales.set_db_data(sql, self._set_table_data)
        self.ui.tableWidget_medicine_sales.sortItems(1, QtCore.Qt.DescendingOrder)
        self.ui.tableWidget_medicine_sales.setCurrentCell(0, 0)

        self._plot_chart()

    def _set_table_data(self, row_no, row):
        total_dosage = number_utils.get_float(row['TotalDosage'])
        medicine_record = [
            string_utils.xstr(row['MedicineName']),
            total_dosage,
            string_utils.xstr(row['Unit']),
            number_utils.get_float(row['InPrice']),
            number_utils.get_float(row['SalePrice']),
        ]

        for col_no in range(len(medicine_record)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, medicine_record[col_no])
            self.ui.tableWidget_medicine_sales.setItem(
                row_no, col_no, item,
            )

            if col_no in [1, 3, 4]:
                self.ui.tableWidget_medicine_sales.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2]:
                self.ui.tableWidget_medicine_sales.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出用藥統計",
            '{0}至{1}{2}用藥統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.medicine_type
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_medicine_sales, None, [1, 3, 4, 5]
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>用藥統計統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _plot_chart(self):
        while self.ui.verticalLayout_chart.count():
            item = self.ui.verticalLayout_chart.takeAt(1)
            if item is None:
                break

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_medicine_chart()

    def _plot_medicine_chart(self):
        medicine_list = []
        for row_no in range(10):
            medicine = [
                self.ui.tableWidget_medicine_sales.item(row_no, 0),
                self.ui.tableWidget_medicine_sales.item(row_no, 1),
            ]
            if medicine[0] is None:
                continue

            medicine_list.append(medicine)

        series = QtChart.QBarSeries()
        bar_set = []
        for i in range(len(medicine_list)):
            bar_set.append(QtChart.QBarSet(medicine_list[i][0].text()))
            bar_set[i] << number_utils.get_float(medicine_list[i][1].text())
            series.append([bar_set[i]])

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('用藥統計表')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['用藥統計']
        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.addAxis(axis, QtCore.Qt.AlignBottom)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignRight)
        # chart.legend().hide()

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(950)
        self.ui.horizontalLayout_income.addWidget(self.chartView)
