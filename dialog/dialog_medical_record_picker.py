#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtCore, QtGui
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import number_utils
from classes import table_widget


# 門診掛號 2018.01.22
class DialogMedicalRecordPicker(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordPicker, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_date = args[2]
        self.ui = None

        self.case_key = None
        self.patient_key = None

        self._set_ui()
        self._set_signal()
        self._read_medical_records()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICAL_RECORD_PICKER, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.button_accepted)
        self.ui.buttonBox.rejected.connect(self.button_rejected)
        self.ui.tableWidget_medical_record.doubleClicked.connect(self.table_double_clicked)

    def _set_table_width(self):
        # width = [80, 80, 40, 120, 120, 80, 120, 120, 500]
        # self.table_widget_medical_record.set_table_heading_width(width)
        self.table_widget_medical_record.set_column_hidden([0, 1])

    def _read_medical_records(self):
        start_date = '{0} 00:00:00'.format(self.case_date)
        end_date = '{0} 23:59:59'.format(self.case_date)

        sql = '''
            SELECT * FROM cases
            WHERE
                CaseDate BETWEEN "{0}" AND "{1}"
            ORDER BY CaseDate
        '''.format(start_date, end_date)

        self.table_widget_medical_record.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        medical_record = [
            string_utils.xstr(row['CaseKey']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.int_to_str(row['Continuance']).strip('0'),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(row['Doctor']),
        ]
        for column in range(len(medical_record)):
            self.ui.tableWidget_medical_record.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [4]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [3, 6, 9]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if number_utils.get_integer(row['TotalFee']) > 0:
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setForeground(QtGui.QColor('blue')
                                                  )
            if string_utils.xstr(row['InsType']) == '自費':
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )
            if string_utils.xstr(row['TreatType']) == '自購':
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setForeground(
                    QtGui.QColor('darkgreen')
                )

    def button_accepted(self):
        self.case_key = self.table_widget_medical_record.field_value(0)
        self.patient_key = self.table_widget_medical_record.field_value(1)

    def button_rejected(self):
        self.case_key = None
        self.patient_key = None

    def table_double_clicked(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).animateClick()

    def get_case_key(self):
        return self.case_key

    def get_patient_key(self):
        return self.patient_key

