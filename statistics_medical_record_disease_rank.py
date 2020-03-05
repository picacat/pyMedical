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


# 醫師統計 2019.05.02
class StatisticsMedicalRecordDiseaseRank(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMedicalRecordDiseaseRank, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MEDICAL_RECORD_DISEASE_RANK, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.table_widget_disease_rank = table_widget.TableWidget(
            self.ui.tableWidget_disease_rank, self.database
        )
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self.table_widget_medical_record.set_column_hidden([0])
        self._set_table_width()

    def _set_table_width(self):
        self.table_widget_disease_rank.set_table_heading_width([100, 350, 70])
        self.table_widget_medical_record.set_table_heading_width(
            [100, 130, 50, 80, 90, 90, 90]
        )

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_disease_rank.itemSelectionChanged.connect(self._disease_changed)
        self.ui.tableWidget_medical_record.doubleClicked.connect(self._open_medical_record)

    def _open_medical_record(self):
        case_key = self.table_widget_medical_record.field_value(0)
        if case_key is None:
            return

        self.parent.parent.open_medical_record(case_key)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_form(self):
        self.close_all()
        self.close_tab()

    def start_calculate(self):
        self._calculate_data()

    def _calculate_data(self):
        self._read_data()
        self._plot_chart()

    def _read_data(self):
        ins_type_condition = ''
        if self.ins_type != '全部':
            ins_type_condition = ' AND InsType = "{0}"'.format(self.ins_type)

        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT  
                DiseaseCode1, DiseaseName1
            FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" 
                {ins_type_condition}
                {doctor_condition}
            ORDER BY DiseaseCode1
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            ins_type_condition=ins_type_condition,
            doctor_condition=doctor_condition,
        )
        rows = self.database.select_record(sql)
        self._set_table_data(rows)

    def _set_table_data(self, rows):
        disease_dict = {}

        for row in rows:
            disease_code = string_utils.xstr(row['DiseaseCode1'])
            if disease_code == '':
                continue

            if disease_code not in disease_dict:
                disease_dict[disease_code] = [string_utils.xstr(row['DiseaseName1']), 1]
            else:
                disease_dict[disease_code][1] += 1

        self.ui.tableWidget_disease_rank.setRowCount(0)
        for row_no, row in zip(range(len(disease_dict)), disease_dict.items()):
            self.ui.tableWidget_disease_rank.insertRow(row_no)
            disease_row = [row[0], row[1][0], row[1][1]]
            for col_no in range(len(disease_row)):
                item = QtWidgets.QTableWidgetItem()
                item.setData(QtCore.Qt.EditRole, disease_row[col_no])
                self.ui.tableWidget_disease_rank.setItem(
                    row_no, col_no, item,
                )
            self.ui.tableWidget_disease_rank.item(
                row_no, 2).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )

        self.ui.tableWidget_disease_rank.resizeRowsToContents()
        self.ui.tableWidget_disease_rank.sortItems(2, QtCore.Qt.DescendingOrder)

    def _get_row_no(self, disease_code):
        for row_no in range(self.ui.tableWidget_disease_rank.rowCount()):
            item = self.ui.tableWidget_disease_rank.item(row_no, 0)
            if item is None:
                continue

            if disease_code == item.text():
                return row_no

        self.ui.tableWidget_disease_rank.setRowCount(
            self.ui.tableWidget_disease_rank.rowCount() + 1
        )

        return self.ui.tableWidget_disease_rank.rowCount()

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "匯出疾病排行",
            '{0}至{1}{2}醫師門診門診疾病排行.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_disease_rank, None, [2],
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>疾病排行檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

    def _plot_chart(self):
        while self.ui.verticalLayout_chart.count():
            item = self.ui.verticalLayout_chart.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_diseaes_rank_chart()

    def _plot_diseaes_rank_chart(self):
        disease_list = []

        for row_no in range(10):
            disease = [
                self.ui.tableWidget_disease_rank.item(row_no, 1),
                self.ui.tableWidget_disease_rank.item(row_no, 2),
            ]
            if disease[0] is None:
                continue

            disease_list.append(disease)

        series = QtChart.QBarSeries()
        bar_set = []
        for i in range(len(disease_list)):
            bar_set.append(QtChart.QBarSet(disease_list[i][0].text()))
            bar_set[i] << number_utils.get_float(disease_list[i][1].text())
            series.append([bar_set[i]])

        chart = QtChart.QChart()
        chart.addSeries(series)
        chart.setTitle('就醫疾病排行Top10')
        chart.setAnimationOptions(QtChart.QChart.SeriesAnimations)

        categories = ['疾病排行']
        axis = QtChart.QBarCategoryAxis()
        axis.append(categories)
        chart.createDefaultAxes()
        chart.addAxis(axis, QtCore.Qt.AlignBottom)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(QtCore.Qt.AlignRight)
        # chart.legend().hide()

        self.chartView = QtChart.QChartView(chart)
        self.chartView.setRenderHint(QtGui.QPainter.Antialiasing)

        self.chartView.setFixedWidth(500)
        self.ui.verticalLayout_chart.addWidget(self.chartView)

    def _disease_changed(self):
        disease_code = self.ui.tableWidget_disease_rank.item(
            self.ui.tableWidget_disease_rank.currentRow(), 0
        )

        if disease_code is None:
            return

        disease_code = disease_code.text()
        self._read_medical_record(disease_code)

    def _read_medical_record(self, disease_code):
        ins_type_condition = ''
        if self.ins_type != '全部':
            ins_type_condition = ' AND InsType = "{0}"'.format(self.ins_type)

        doctor_condition = ''
        if self.doctor != '全部':
            doctor_condition = ' AND Doctor = "{0}"'.format(self.doctor)

        sql = '''
            SELECT * 
            FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                DiseaseCode1 = "{disease_code}"
                {ins_type_condition}
                {doctor_condition}
            ORDER BY CaseDate
        '''.format(
            start_date=self.start_date,
            end_date=self.end_date,
            disease_code=disease_code,
            ins_type_condition=ins_type_condition,
            doctor_condition=doctor_condition,
        )

        self.table_widget_medical_record.set_db_data(sql, self._set_medical_record)

    def _set_medical_record(self, row_no, row):
        medical_record = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Doctor']),
        ]

        for col_no in range(len(medical_record)):
            self.ui.tableWidget_medical_record.setItem(
                row_no, col_no,
                QtWidgets.QTableWidgetItem(medical_record[col_no])
            )

            if col_no in [2]:
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif col_no in [3]:
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )


