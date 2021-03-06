#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import datetime

from classes import table_widget

from libs import system_utils
from libs import ui_utils
from libs import date_utils
from libs import number_utils
from libs import string_utils
from libs import case_utils
from libs import nhi_utils


# 卡序檢查 2019.04.24
class CheckCard(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(CheckCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.apply_year = int(args[2])
        self.apply_month = int(args[3])
        self.apply_type = args[4]
        self.ui = None
        self.errors = 0
        self.rows = None

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CHECK_CARD, self)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
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
            100, 130, 60, 90, 90, 100, 80, 50, 100, 400, 100,
            90, 60, 250,
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

        self._check_data()
        if self.errors <= 0:
            self.ui.toolButton_find_error.setEnabled(False)
        else:
            self.ui.toolButton_find_error.setEnabled(True)

        self.ui.tableWidget_errors.resizeRowsToContents()
        self._calculate_indicator()

    def _check_data(self):
        row_count = self.ui.tableWidget_errors.rowCount()

        if row_count <= 0:
            return

        progress_dialog = QtWidgets.QProgressDialog(
            '正在執行卡序檢查中, 請稍後...', '取消', 0, row_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no in range(row_count):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
            card = self.ui.tableWidget_errors.item(row_no, 6).text()
            course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no, 7).text())
            disease_code = self.ui.tableWidget_errors.item(row_no, 8).text()
            treat_type = self.ui.tableWidget_errors.item(row_no, 10).text()

            try:
                next_case_date = self.ui.tableWidget_errors.item(row_no+1, 1).text()
                next_patient_key = self.ui.tableWidget_errors.item(row_no+1, 3).text()
                next_card = self.ui.tableWidget_errors.item(row_no+1, 6).text()
                next_course = number_utils.get_integer(
                    self.ui.tableWidget_errors.item(row_no+1, 7).text()
                )
                next_disease_code = self.ui.tableWidget_errors.item(row_no+1, 8).text()
                next_treat_type = self.ui.tableWidget_errors.item(row_no+1, 10).text()
            except AttributeError:
                next_case_date = None
                next_patient_key = 0
                next_card = None
                next_course = 0
                next_disease_code = None
                next_treat_type = None

            current_error_message = []
            error_message = []
            if card == '自動取得':
                current_error_message.append('未取得卡序')

            if next_card == '':
                error_message.append('卡序空白')

            if next_patient_key == 0:
                pass
            elif patient_key != next_patient_key:  # 換人
                pass
            else:  # 同一人
                if card == next_card and next_course <= 1:
                    error_message.append('卡序與{0}相同'.format(case_date))
                elif next_course <= 1:  # 2020.01.03 板橋新生堂
                    duplicated_case_date = nhi_utils.get_duplicated_card(
                        self.ui.tableWidget_errors, row_no, patient_key, next_card,
                    )
                    if duplicated_case_date:
                        error_message.append('卡序與{0}相同'.format(duplicated_case_date))

                if card != next_card and 1 <= course <= 5:
                    delta = nhi_utils.get_first_course_delta(
                        self.ui.tableWidget_errors, row_no, patient_key, course, next_case_date,
                    )
                    if delta is None:
                        error_message.append('療程未滿6次')
                    elif delta.days + 1 < 14:  # 當天也算一天 +1
                        error_message.append('療程14日未完成另開新卡')
                    elif delta.days + 1 < 30:  # 當天也算一天 +1
                        error_message.append('療程30日未完成另開新卡')

                if treat_type != next_treat_type and next_course <= 1 and 1 <= course <= 5:
                    is_new_course = False
                    for i in range(row_no, self.ui.tableWidget_errors.rowCount()+1):
                        check_next_patient_key = self.ui.tableWidget_errors.item(i+1, 3)
                        if check_next_patient_key is None:
                            continue

                        if patient_key != check_next_patient_key.text():
                            break

                        check_next_card = self.ui.tableWidget_errors.item(i+1, 6)
                        if check_next_card is None:
                            continue

                        if card != check_next_card.text():
                            continue

                        if (self.ui.tableWidget_errors.item(i+1, 7) is not None and
                                number_utils.get_integer(
                                    self.ui.tableWidget_errors.item(i+1, 7).text()) > course):
                            is_new_course = True
                            break

                    if is_new_course:
                        error_message.append('療程中刷卡')
                elif ((treat_type in nhi_utils.INS_TREAT and next_treat_type == '內科') or
                        (treat_type == '內科' and next_treat_type in nhi_utils.INS_TREAT)):
                    error_message.append('內科與針傷療程交替')
                if (treat_type in nhi_utils.INS_TREAT and next_treat_type == '內科' and
                        disease_code == next_disease_code):
                    error_message.append('內科與針傷療程同診斷碼')
                elif (treat_type == '內科' and next_treat_type in nhi_utils.INS_TREAT and
                        disease_code == next_disease_code):
                    error_message.append('針傷療程與內科同診斷碼')

                if course <= 1 and next_course <= 1:
                    delta = date_utils.str_to_date(next_case_date) - date_utils.str_to_date(case_date)
                    if delta.days == 1:
                        error_message.append('隔日刷卡')

                if card != next_card:  # 換新療程
                    pass
                else:   # 同療程
                    pass

            if len(current_error_message) > 0:
                self._set_error_message(row_no, current_error_message)
            if len(error_message) > 0:
                self._set_error_message(row_no+1, error_message)

            progress_dialog.setValue(row_no)

        progress_dialog.setValue(row_count)

    def _set_error_message(self, row_no, error_message):
        self.errors += 1

        self.ui.tableWidget_errors.setItem(
            row_no, 13, QtWidgets.QTableWidgetItem(', '.join(error_message))
        )
        try:
            self._set_row_color(row_no, 'red')
        except AttributeError:
            pass

    def _set_row_color(self, row_no, color):
        for column_no in range(self.ui.tableWidget_errors.columnCount()):
            self.ui.tableWidget_errors.item(row_no, column_no).setForeground(QtGui.QColor(color))

    def error_count(self):
        return self.errors

    def _set_row_error_message(self, row_no, col_no, error_message):
        self.ui.tableWidget_errors.setItem(
            row_no, col_no,
            QtWidgets.QTableWidgetItem(
                ', '.join(error_message)
            )
        )
        self._set_row_color(row_no, 'red')

    def _remove_useless_record(self):
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            case_date = self.ui.tableWidget_errors.item(row_no, 1).text()
            patient_key = self.ui.tableWidget_errors.item(row_no, 3).text()
            card = self.ui.tableWidget_errors.item(row_no, 6).text()
            course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no, 7).text())
            if date_utils.str_to_date(case_date).month != self.apply_month:
                last_case_date = case_date
                for i in range(1, 6):
                    try:
                        next_case_date = self.ui.tableWidget_errors.item(row_no+i, 1).text()
                        next_patient_key = self.ui.tableWidget_errors.item(row_no+i, 3).text()
                        next_card = self.ui.tableWidget_errors.item(row_no+i, 6).text()
                        next_course = number_utils.get_integer(self.ui.tableWidget_errors.item(row_no+i, 7).text())
                        if patient_key == next_patient_key and card == next_card and next_course > course:
                            last_case_date = next_case_date
                    except:
                        continue

                if date_utils.str_to_date(last_case_date).month != self.apply_month:
                    self._set_row_error_message(row_no, 13, '!')

        for row_no in reversed(range(self.ui.tableWidget_errors.rowCount())):
            remove_flag = self.ui.tableWidget_errors.item(row_no, 13)
            if remove_flag is not None and remove_flag.text() == '!':
                self.ui.tableWidget_errors.removeRow(row_no)

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
        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])

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
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(pres_days),
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

    # 異常指標
    def _calculate_indicator(self):
        self._calculate_indicator1()
        self._calculate_indicator2()
        self._calculate_indicator3()

    # 內傷交替率
    def _calculate_indicator1(self):
        denominator = self.ui.tableWidget_errors.rowCount()

        numerator = 0
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            error_message = self.ui.tableWidget_errors.item(row_no, 13)
            if error_message is None:
                continue

            if '內科與針傷療程交替' in error_message.text():
                numerator += 1

        if denominator == 0:
            result = 0
        else:
            result=numerator/denominator*100

        self.ui.label_indicator1.setText(
            '''內傷交替率 = 同時申報針傷及內科件數 / 當月申報總人數<br> 
                <b>{numerator} / {denominator} = {result:.2f}%</b>'''.format(
                numerator=numerator,
                denominator=denominator,
                result=result,
            )
        )

    # 隔日刷卡率
    def _calculate_indicator2(self):
        denominator = 0
        numerator = 0
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            course = self.ui.tableWidget_errors.item(row_no, 7)
            if course is None or number_utils.get_integer(course.text()) <= 1:
                denominator += 1

            error_message = self.ui.tableWidget_errors.item(row_no, 13)
            if error_message is None:
                continue

            if '隔日刷卡' in error_message.text():
                numerator += 1

        if denominator == 0:
            result = 0
        else:
            result=numerator/denominator*100

        self.ui.label_indicator2.setText(
            '''隔日刷卡率 = 隔日申報診察費件數 / 診察費總件數<br> 
                <b>{numerator} / {denominator} = {result:.2f}%</b>'''.format(
                numerator=numerator,
                denominator=denominator,
                result=result
            )
        )

    # 療程中刷卡率
    def _calculate_indicator3(self):
        denominator = 0
        numerator = 0
        for row_no in range(self.ui.tableWidget_errors.rowCount()):
            course = self.ui.tableWidget_errors.item(row_no, 7)
            if course is None or number_utils.get_integer(course.text()) >= 1:
                denominator += 1

            error_message = self.ui.tableWidget_errors.item(row_no, 13)
            if error_message is None:
                continue

            if '療程中刷卡' in error_message.text():
                numerator += 1

        if denominator == 0:
            result = 0
        else:
            result=numerator/denominator*100

        self.ui.label_indicator3.setText(
            '''療程中刷卡率 = 療程中申報診察費件數 / 療程總件數 <br> 
                <b>{numerator} / {denominator} = {result:.2f}%</b>'''.format(
                numerator=numerator,
                denominator=denominator,
                result=result,
            )
        )
