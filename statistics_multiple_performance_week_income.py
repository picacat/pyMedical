#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtChart
from PyQt5.QtWidgets import QMessageBox, QFileDialog

import datetime

from classes import table_widget
from libs import ui_utils
from libs import string_utils
from libs import date_utils
from libs import number_utils
from libs import export_utils
from libs import system_utils
from libs import personnel_utils
from libs import chart_utils
from libs import case_utils


# 綜合業績報表-週統計表 2020.02.15
class StatisticsMultiplePerformanceWeekIncome(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(StatisticsMultiplePerformanceWeekIncome, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.year = args[2]
        self.month = args[3]
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_STATISTICS_MULTIPLE_PERFORMANCE_WEEK_INCOME, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self.table_widget_week = table_widget.TableWidget(
            self.ui.tableWidget_week, self.database
        )
        self._set_table_width()

    def _set_table_width(self):
        width = [
            180, 140, 140, 140, 140, 140, 120, 120,
        ]
        self.table_widget_medical_record.set_table_heading_width(width)

        width = [
            60,
            65, 65, 65,
            65, 65, 65,
            65, 65, 65,
            65, 65, 65,
            65, 65, 65,
            65, 65, 65,
            80,
        ]
        self.table_widget_week.set_table_heading_width(width)

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
        self._calculate_fee()
        self._calculate_week_fee()
        self._plot_chart()

    def _set_fee_data_row_header(self):
        row_header = [
            '日期', '本週總自費', '本週總日數', '平均自費/日', '醫師', '自購', '專案',
        ]
        for row_no in range(len(row_header)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, row_header[row_no])
            self.ui.tableWidget_medical_record.setItem(
                row_no, 0, item
            )
            self.ui.tableWidget_medical_record.item(
                row_no, 0).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )

    def _calculate_fee(self):
        self.ui.tableWidget_medical_record.setRowCount(13)
        self._set_fee_data_row_header()

        week_no = datetime.date(
            number_utils.get_integer(self.year),
            number_utils.get_integer(self.month),
            1
        ).isocalendar()[1]

        header = ['項目', '', '', '', '', '', '總和', '平均']
        self.week_list = []
        for i in range(1, 6):
            week_date = '{year}-W{week_no}'.format(
                year=self.year,
                week_no=week_no,
            )
            first_day = datetime.datetime.strptime(week_date + '-1', '%Y-W%W-%w')
            if first_day.month != number_utils.get_integer(self.month):
                break

            first_date = datetime.date(first_day.year, first_day.month, first_day.day)

            last_day = first_day + datetime.timedelta(days=5)
            last_date = datetime.date(last_day.year, last_day.month, last_day.day)

            self.week_list.append([first_date, last_date])
            week_no += 1
            header[i] = '第{week_no}週'.format(week_no=week_no-1)

        self.ui.tableWidget_medical_record.setHorizontalHeaderLabels(header)
        self._calculate_week(self.week_list)

    def _calculate_week(self, week_list):
        for week, col_no in zip(week_list, range(1, len(week_list)+1)):
            start_date = week[0]
            end_date = week[1]
            date_period = '{start_month}/{start_day}~{end_month}/{end_day}'.format(
                start_month=start_date.month,
                start_day=start_date.day,
                end_month=end_date.month,
                end_day=end_date.day,
            )
            self._set_table_item(self.ui.tableWidget_medical_record, 0, col_no, date_period)

            self._calculate_total_income(1, col_no, start_date, end_date)
            self._calculate_self_days(2, col_no, start_date, end_date)
            self._calculate_avg_days(3, col_no)

            self._calculate_doctor_income(4, col_no, start_date, end_date)
            self._calculate_purchase_income(5, col_no, start_date, end_date)
            self._calculate_project_income(6, col_no, start_date, end_date)

        self._calculate_total()

    @staticmethod
    def _get_datetime_period(start_date, end_date):
        start_date = '{year}-{month}-{day} 00:00:00'.format(
            year=start_date.year,
            month=start_date.month,
            day=start_date.day,
        )

        end_date = '{year}-{month}-{day} 23:59:59'.format(
            year=end_date.year,
            month=end_date.month,
            day=end_date.day,
        )

        return start_date, end_date

    def _calculate_total_income(self, row_no, col_no, start_date, end_date):
        start_date, end_date = self._get_datetime_period(start_date, end_date)
        sql = '''
            SELECT SUM(TotalFee) AS TotalAmount FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}"
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)
        total_amount = number_utils.get_integer(rows[0]['TotalAmount'])

        self._set_table_item(self.ui.tableWidget_medical_record, row_no, col_no, total_amount)

    def _calculate_self_days(self, row_no, col_no, start_date, end_date):
        start_date, end_date = self._get_datetime_period(start_date, end_date)
        sql = '''
            SELECT CaseDate FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                TotalFee > 0
            GROUP BY Date(CaseDate)
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)
        row_count = len(rows)

        self._set_table_item(self.ui.tableWidget_medical_record, row_no, col_no, row_count)

    def _calculate_avg_days(self, row_no, col_no):
        total_amount = number_utils.get_integer(self.ui.tableWidget_medical_record.item(1, col_no).text())
        total_days = number_utils.get_integer(self.ui.tableWidget_medical_record.item(2, col_no).text())
        if total_amount == 0 or total_days == 0:
            avg_days = 0
        else:
            avg_days = number_utils.round_up(total_amount / total_days)

        self._set_table_item(self.ui.tableWidget_medical_record, row_no, col_no, avg_days)

    def _calculate_doctor_income(self, row_no, col_no, start_date, end_date):
        start_date, end_date = self._get_datetime_period(start_date, end_date)
        sql = '''
            SELECT CaseKey, TotalFee FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                TotalFee > 0 AND
                TreatType != "自購"
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)

        total_fee = 0
        for row in rows:
            total_fee += number_utils.get_integer(row['TotalFee'])
            project_income = self._get_project_income(row['CaseKey'])
            total_fee -= project_income

        self._set_table_item(self.ui.tableWidget_medical_record, row_no, col_no, total_fee)

    def _calculate_purchase_income(self, row_no, col_no, start_date, end_date):
        start_date, end_date = self._get_datetime_period(start_date, end_date)
        sql = '''
            SELECT CaseKey, TotalFee FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                TotalFee > 0 AND
                TreatType = "自購"
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)

        total_fee = 0
        for row in rows:
            total_fee += number_utils.get_integer(row['TotalFee'])
            project_income = self._get_project_income(row['CaseKey'])
            total_fee -= project_income

        self._set_table_item(self.ui.tableWidget_medical_record, row_no, col_no, total_fee)

    def _calculate_project_income(self, row_no, col_no, start_date, end_date):
        start_date, end_date = self._get_datetime_period(start_date, end_date)
        sql = '''
            SELECT CaseKey, TotalFee FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                TotalFee > 0
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)

        project_income = 0
        for row in rows:
            project_income += self._get_project_income(row['CaseKey'])

        self._set_table_item(self.ui.tableWidget_medical_record, row_no, col_no, project_income)

    def _get_project_income(self, case_key):
        sql = '''
            SELECT MedicineSet, Amount FROM prescript
                LEFT JOIN medicine ON medicine.MedicineKey = prescript.MedicineKey
            WHERE
                CaseKey = {case_key} AND
                medicine.Project IS NOT NULL AND LENGTH(medicine.Project) > 0
        '''.format(
            case_key=case_key,
        )

        project_income = 0
        rows = self.database.select_record(sql)
        for row in rows:
            pres_days = case_utils.get_pres_days(self.database, case_key, row['MedicineSet'])
            if pres_days <= 0:
                pres_days = 1

            project_income += number_utils.get_integer(row['Amount']) * pres_days

        return project_income

    @staticmethod
    def _set_table_item(tableWidget, row_no, col_no, data):
        item = QtWidgets.QTableWidgetItem()

        item.setData(QtCore.Qt.EditRole, data)
        tableWidget.setItem(
            row_no, col_no, item
        )
        tableWidget.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        )

    def _calculate_total(self):
        for row_no in range(1, self.ui.tableWidget_medical_record.rowCount() + 1):
            total = 0
            col_count = 0
            for col_no in range(1, 6):
                item = self.ui.tableWidget_medical_record.item(row_no, col_no)
                if item is None:
                    continue

                value = number_utils.get_integer(item.text())
                total += value
                col_count += 1

            if total > 0 and col_count > 0:
                self._set_table_item(self.ui.tableWidget_medical_record, row_no, 6, total)
                self._set_table_item(
                    self.ui.tableWidget_medical_record, row_no, 7, number_utils.round_up(total/col_count)
                )

    def _plot_chart(self):
        while self.ui.verticalLayout_chart.count():
            item = self.ui.verticalLayout_chart.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self._plot_income_chart()
        self._plot_week_chart()

    def _calculate_week_fee(self):
        self.ui.tableWidget_week.setRowCount(8)
        self._set_week_header()
        self._calculate_week_data()
        self._calculate_week_total()

    def _set_week_header(self):
        start_date = '{year}-{month}-{day}'.format(
            year=self.week_list[0][0].year,
            month=self.week_list[0][0].month,
            day=self.week_list[0][0].day,
        )
        end_date = '{year}-{month}-{day}'.format(
            year=self.week_list[-1][1].year,
            month=self.week_list[-1][1].month,
            day=self.week_list[-1][1].day,
        )

        sql = '''
            SELECT CaseDate FROM cases
            WHERE
                DATE(CaseDate) BETWEEN "{start_date}" AND "{end_date}"
            GROUP BY Date(CaseDate)
            ORDER BY CaseDate
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )
        rows = self.database.select_record(sql)

        week_list = [[], [], [], [], [], [], []]
        for row in rows:
            week_day = row['CaseDate'].weekday()
            week_list[week_day].append(string_utils.xstr(row['CaseDate'].day))

        col_list = [1, 4, 7, 10, 13, 16]
        for col_no in col_list:
            self.ui.tableWidget_week.setSpan(0, col_no, 1, 3)

        self._set_table_item(self.ui.tableWidget_week, 0, 0, '日期')
        for col_no, i in zip(col_list, range(len(col_list))):
            self._set_table_item(
                self.ui.tableWidget_week, 0, col_no, ', '.join(week_list[i])
            )

        header = [
            '週別',
            '早', '午', '晚',
            '早', '午', '晚',
            '早', '午', '晚',
            '早', '午', '晚',
            '早', '午', '晚',
            '早', '午', '晚',
        ]
        row_no = 1
        for col_no in range(len(header)):
            self.ui.tableWidget_week.setItem(
                row_no, col_no, QtWidgets.QTableWidgetItem(header[col_no])
            )
            self.ui.tableWidget_week.item(
                row_no, col_no).setTextAlignment(
                QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
            )

    def _calculate_week_data(self):
        week_list_count = len(self.week_list)

        progress_dialog = QtWidgets.QProgressDialog(
            '正在統計收入資料中, 請稍後...', '取消', 0, week_list_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for i, week_row in zip(range(week_list_count), self.week_list):
            progress_dialog.setValue(i)
            if progress_dialog.wasCanceled():
                break

            row_no = i + 2
            self._set_table_item(self.ui.tableWidget_week, row_no, 0, i+1)
            start_date, end_date = self._get_datetime_period(
                week_row[0], week_row[1],
            )
            sql = '''
                SELECT CaseDate FROM cases
                WHERE
                    CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                    TotalFee > 0
                GROUP BY Date(CaseDate)
                ORDER BY CaseDate
            '''.format(
                start_date=start_date,
                end_date=end_date,
            )
            rows = self.database.select_record(sql)
            self._calculate_week_period_fee(row_no, rows)

        progress_dialog.setValue(week_list_count)

    def _calculate_week_period_fee(self, row_no, rows):
        col_no_list = [1, 4, 7, 10, 13, 16]
        for row in rows:
            week_no = row['CaseDate'].weekday()
            col_no = col_no_list[week_no]
            total_amount = self._get_period_fee(row['CaseDate'], '早班')
            self._set_table_item(self.ui.tableWidget_week, row_no, col_no, total_amount)
            total_amount = self._get_period_fee(row['CaseDate'], '午班')
            self._set_table_item(self.ui.tableWidget_week, row_no, col_no+1, total_amount)
            total_amount = self._get_period_fee(row['CaseDate'], '晚班')
            self._set_table_item(self.ui.tableWidget_week, row_no, col_no+2, total_amount)

    def _get_period_fee(self, case_date, period):
        start_date = '{year}-{month}-{day} 00:00:00'.format(
            year=case_date.year,
            month=case_date.month,
            day=case_date.day,
        )

        end_date = '{year}-{month}-{day} 23:59:59'.format(
            year=case_date.year,
            month=case_date.month,
            day=case_date.day,
        )
        sql = '''
            SELECT SUM(TotalFee) AS TotalAmount FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" and "{end_date}" AND
                Period = "{period}" AND
                TotalFee > 0
        '''.format(
            start_date=start_date,
            end_date=end_date,
            period=period,
        )
        rows = self.database.select_record(sql)

        return number_utils.get_integer(rows[0]['TotalAmount'])

    def _calculate_week_total(self):
        for row_no in range(2, self.ui.tableWidget_week.rowCount() + 1):
            total = 0
            col_count = 0
            for col_no in range(1, 19):
                item = self.ui.tableWidget_week.item(row_no, col_no)
                if item is None:
                    continue

                value = number_utils.get_integer(item.text())
                total += value
                col_count += 1

            if total > 0 and col_count > 0:
                self._set_table_item(self.ui.tableWidget_week, row_no, 19, total)

        self._set_table_item(self.ui.tableWidget_week, 7, 0, '總計')
        for col_no in range(1, self.ui.tableWidget_week.columnCount()):
            total = 0
            for row_no in range(2, 7):
                item = self.ui.tableWidget_week.item(row_no, col_no)
                if item is not None:
                    total += number_utils.get_integer(item.text())

                self._set_table_item(self.ui.tableWidget_week, 7, col_no, total)

    def _plot_income_chart(self):
        set_list = list()
        set_list.append(QtChart.QBarSet('醫師'))
        set_list.append(QtChart.QBarSet('自購'))
        set_list.append(QtChart.QBarSet('專案'))

        income_list = []
        for i in range(len(set_list)):
            income_list.append([])

        categories = []

        weeks = 5
        for col_no in range(1, weeks+1):
            item = self.ui.tableWidget_medical_record.item(0, col_no)
            if item is None:
                break

            categories.append('{0}週'.format(col_no))
            for j in range(len(set_list)):
                value = number_utils.get_integer(self.ui.tableWidget_medical_record.item(j+4, col_no).text())
                income_list[j].append(value)

        series = QtChart.QStackedBarSeries()
        for i in range(len(set_list)):
            for value in income_list[i]:
                set_list[i] << value

            series.append(set_list[i])

        chart_utils.plot_chart('自費收入統計表', series, categories, self.ui.verticalLayout_chart, 350)

    def _plot_week_chart(self):
        set_list = list()
        set_list.append(QtChart.QBarSet('早班'))
        set_list.append(QtChart.QBarSet('午班'))
        set_list.append(QtChart.QBarSet('晚班'))

        period_list = []
        for i in range(len(set_list)):
            period_list.append([])

        categories = []

        col_no_list = [1, 4, 7, 10, 13, 16]
        for i, col_no in zip(range(len(col_no_list)), col_no_list):
            week_name = date_utils.get_weekday_name(i)
            categories.append(week_name[2])
            for j in range(len(set_list)):
                value = number_utils.get_integer(self.ui.tableWidget_week.item(7, col_no+j).text())
                period_list[j].append(value)

        series = QtChart.QStackedBarSeries()
        for i in range(len(set_list)):
            for value in period_list[i]:
                set_list[i] << value

            series.append(set_list[i])

        chart_utils.plot_chart('週自費統計表', series, categories, self.ui.verticalLayout_chart, 350)

    def export_to_excel(self):
        options = QFileDialog.Options()
        excel_file_name, _ = QFileDialog.getSaveFileName(
            self.parent,
            "QFileDialog.getSaveFileName()",
            '{0}至{1}{2}醫師掛號費優待統計表.xlsx'.format(
                self.start_date[:10], self.end_date[:10], self.doctor
            ),
            "excel檔案 (*.xlsx);;Text Files (*.txt)", options = options
        )
        if not excel_file_name:
            return

        export_utils.export_table_widget_to_excel(
            excel_file_name, self.ui.tableWidget_medical_record, [0],
            [4, 5, 6, 8],
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '資料匯出完成',
            '<h3>掛號費優待統計檔{0}匯出完成.</h3>'.format(excel_file_name),
            'Microsoft Excel 格式.'
        )

