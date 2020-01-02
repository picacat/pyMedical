#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

from classes import table_widget

from libs import ui_utils
from libs import date_utils
from libs import number_utils
from libs import string_utils
from libs import system_utils
from libs import nhi_utils


# 候診名單 2018.01.31
class CheckCourse(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckCourse, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.ui = None
        self.errors = 0

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_COURSE, self)
        system_utils.set_css(self, self.system_settings)
        self.center()
        self._set_table_widget()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def _set_table_widget(self):
        self.table_widget_errors = table_widget.TableWidget(self.ui.tableWidget_errors, self.database)
        self.table_widget_errors.set_column_hidden([0])
        width = [
            100, 120, 60, 80, 80, 100, 70, 30, 100, 450, 100,
            80, 80, 250,
        ]
        self.table_widget_errors.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_errors.doubleClicked.connect(self.open_medical_record)
        self.ui.toolButton_find_error.clicked.connect(self._find_error)

    def _find_error(self):
        self.table_widget_errors.find_error(13)

    def open_medical_record(self):
        case_key = self.table_widget_errors.field_value(0)
        self.parent.open_medical_record(case_key)

    def read_data(self):
        month = int(self.apply_month)
        if month > 1:
            year = self.apply_year
            month -= 1
        else:
            year = self.apply_year - 1
            month = 12

        start_date = date_utils.get_start_date_by_year_month(
            str(year), str(month))  # 雙月檢查
        end_date = date_utils.get_end_date_by_year_month(
            self.apply_year, self.apply_month)

        apply_type_sql = nhi_utils.get_apply_type_sql(self.apply_type)

        sql = '''
            SELECT 
                *
            FROM cases 
            WHERE
                (CaseDate BETWEEN "{start_date}" AND "{end_date}") AND
                (cases.InsType = "健保") AND
                (Continuance >= 1) AND
                ({apply_type_sql}) 
            ORDER BY PatientKey, CaseDate
        '''.format(
            start_date=start_date,
            end_date=end_date,
            apply_type_sql=apply_type_sql,
        )

        self.rows = self.database.select_record(sql)

    def row_count(self):
        return len(self.rows)

    def start_check(self):
        self.read_data()

        self.ui.tableWidget_errors.setRowCount(0)
        for row in self.rows:
            self._insert_record(row)

        self._remove_useless_record()
        self._set_last_month_color()
        self.ui.tableWidget_errors.setAlternatingRowColors(True)

        self._check_course()
        if self.errors <= 0:
            self.ui.toolButton_find_error.setEnabled(False)
        else:
            self.ui.toolButton_find_error.setEnabled(True)

        self.ui.tableWidget_errors.resizeRowsToContents()

    def _check_course(self):
        row_count = self.ui.tableWidget_errors.rowCount()
        if row_count <= 0:
            return

        progress_dialog = QtWidgets.QProgressDialog(
            '正在執行療程檢查中, 請稍後...', '取消', 0, row_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no in range(row_count):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            if date_utils.str_to_date(case_date).month != self.apply_month:
                continue

            patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
            share_type = self.ui.tableWidget_errors.item(row_no, 5).text()
            card = self.ui.tableWidget_errors.item(row_no, 6).text()
            course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no, 7).text())
            disease_code = self.ui.tableWidget_errors.item(row_no, 8).text()
            treatment = self.ui.tableWidget_errors.item(row_no, 10).text()

            try:
                next_case_date = self.ui.tableWidget_errors.item(row_no+1, 1).text()
                next_patient_key = self.ui.tableWidget_errors.item(row_no+1, 3).text()
                next_share_type = self.ui.tableWidget_errors.item(row_no+1, 5).text()
                next_card = self.ui.tableWidget_errors.item(row_no+1, 6).text()
                next_course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no+1, 7).text())
                next_disease_code = self.ui.tableWidget_errors.item(row_no+1, 8).text()
                next_treatment = self.ui.tableWidget_errors.item(row_no+1, 10).text()
            except AttributeError:
                next_case_date = None
                next_patient_key = 0
                next_share_type = None
                next_card = None
                next_course = 0
                next_disease_code = None
                next_treatment = None

            error_message = []
            next_error_message = []
            if next_patient_key == 0:
                pass
            elif patient_key != next_patient_key:
                # delta = database._get_first_course_delta(
                #     row_no, primary_key, course, case_date,
                # )
                delta = nhi_utils.get_first_course_delta(
                    self.ui.tableWidget_errors, row_no, patient_key, course, case_date,
                )

                if next_course >= 2:
                    next_error_message.append('療程未見首次')

                if course >= 2 and delta is not None and delta.days + 1 > 30:  # 當天也算一天 +1
                    error_message.append('療程已超過30日')
            else:
                if card != next_card:  # 換新療程
                    delta = nhi_utils.get_first_course_delta(  # 檢查當筆
                        self.ui.tableWidget_errors, row_no, patient_key, course, case_date,
                    )
                    next_delta = nhi_utils.get_first_course_delta(  # 以下一筆為檢查資料
                        self.ui.tableWidget_errors, row_no, patient_key, course, next_case_date,
                    )
                    if course >= 2 and delta is None:
                        error_message.append('療程未見首次')
                    elif course >= 2 and delta is not None and delta.days + 1 > 30:  # 當天也算一天 +1
                        error_message.append('療程已超過30日')

                    if course < 6:
                        if next_delta is None:
                            next_error_message.append('療程未滿6次')
                        elif next_delta.days + 1 < 14:  # 當天也算一天 +1
                            next_error_message.append('療程14日未完成另開新療程')
                        elif next_delta.days + 1 < 30:  # 當天也算一天 +1
                            next_error_message.append('療程30日未完成另開新療程')
                    elif course > 6:
                        next_error_message.append('療程超過6次')
                else:   # 同療程
                    delta = nhi_utils.get_first_course_delta(
                        self.ui.tableWidget_errors, row_no, patient_key, course, case_date,
                    )
                    if course >= 2 and delta is not None and delta.days + 1 > 30:  # 當天也算一天 +1
                        error_message.append('療程已超過30日')

                    if next_course == course:
                        if course >= 2:
                            next_error_message.append('療程重複')
                    elif course < 6 and next_course != 1 and next_course - course != 1:
                        next_error_message.append('療程不連續')

                    if case_date >= next_case_date:
                        next_error_message.append('門診日期未照順序')

                    if share_type != next_share_type:
                        next_error_message.append('負擔類別不一致')

                    if disease_code != next_disease_code and next_course >= 2:
                        next_error_message.append('療程診斷碼不一致')

                    if next_treatment == '':
                        next_error_message.append('無處置')
                    elif treatment != next_treatment:
                        next_error_message.append('處置不一致')

            if len(error_message) > 0:
                self.errors += 1
                self._set_row_error_message(row_no, 13, error_message)

            if len(next_error_message) > 0:
                self.errors += 1
                self._set_row_error_message(row_no+1, 13, next_error_message)

            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)

    def _set_row_error_message(self, row_no, col_no, error_message):
        self.ui.tableWidget_errors.setItem(
            row_no, col_no,
            QtWidgets.QTableWidgetItem(
                ', '.join(error_message)
            )
        )
        self._set_row_color(row_no, 'red')

    def _set_row_color(self, row_no, color):
        for column_no in range(self.ui.tableWidget_errors.columnCount()):
            self.ui.tableWidget_errors.item(row_no, column_no).setForeground(QtGui.QColor(color))

    def error_count(self):
        return self.errors

    def _remove_useless_record(self):
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
            card = self.ui.tableWidget_errors.item(row_no, 6).text()
            course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no, 7).text())
            if date_utils.str_to_date(case_date).month != self.apply_month:
                last_case_date = case_date
                for i in range(1, 6):
                    next_case_date = self.ui.tableWidget_errors.item(row_no+i, 1)
                    if next_case_date is None:
                        continue

                    next_case_date = next_case_date.text()
                    next_patient_key = self.ui.tableWidget_errors.item(row_no+i, 3).text()
                    next_card = self.ui.tableWidget_errors.item(row_no+i, 6).text()
                    next_course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no+i, 7).text())
                    if patient_key == next_patient_key and card == next_card and next_course > course:
                        last_case_date = next_case_date

                if date_utils.str_to_date(last_case_date).month != self.apply_month:
                    self._set_row_error_message(row_no, 13, '!')

        for row_no in reversed(range(self.ui.tableWidget_errors.rowCount())):
            remove_flag = self.ui.tableWidget_errors.item(row_no, 13)
            if remove_flag is not None and remove_flag.text() == '!':
                self.ui.tableWidget_errors.removeRow(row_no)

        # for row_no in reversed(range(database.ui.tableWidget_errors.rowCount())):
        #     case_date = database.ui.tableWidget_errors.item(row_no, 1).text()
        #     start_date = date_utils.get_start_date_by_year_month(
        #         database.apply_year, database.apply_month)
        #     if (datetime.datetime.strptime(case_date, '%Y-%m-%d') <
        #             datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')):
        #         database._check_remove_need(row_no)

    def _check_remove_need(self, row_no):
        start_date = date_utils.get_start_date_by_year_month(
            self.apply_year, self.apply_month)
        patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
        card = self.ui.tableWidget_errors.item(row_no, 6).text()
        sql = '''
            SELECT CaseKey FROM cases WHERE
            PatientKey = {0} AND Card = "{1}" AND
            CaseDate >= "{2}"
        '''.format(patient_key, card, start_date)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            self.ui.tableWidget_errors.removeRow(row_no)

    def _set_last_month_color(self):
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            start_date = date_utils.get_start_date_by_year_month(
                self.apply_year, self.apply_month)
            if (datetime.datetime.strptime(case_date, '%Y-%m-%d') <
                    datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')):
                for column in range(0, self.ui.tableWidget_errors.columnCount()):
                    self.ui.tableWidget_errors.item(row_no, column).setForeground(
                        QtGui.QColor('darkGray'))

    def _insert_record(self, row):
        row_no = self.ui.tableWidget_errors.rowCount()
        self.ui.tableWidget_errors.setRowCount(row_no + 1)
        error_record = [
            string_utils.xstr(row['CaseKey']),
            '{0}-{1:0>2}-{2:0>2}'.format(
                row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day
            ),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['DiseaseCode1']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Treatment']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(
                number_utils.get_integer(row['AcupunctureFee']) +
                number_utils.get_integer(row['MassageFee']) +
                number_utils.get_integer(row['DislocateFee'])
            ),
            None,
        ]
        for column_no in range(len(error_record)):
            self.ui.tableWidget_errors.setItem(
                row_no, column_no,
                QtWidgets.QTableWidgetItem(error_record[column_no])
            )
            if column_no in [7]:
                self.ui.tableWidget_errors.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )
            elif column_no in [3, 12]:
                self.ui.tableWidget_errors.item(
                    row_no, column_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

