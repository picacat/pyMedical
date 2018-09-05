#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets
from libs import ui_utils
from libs import system_utils
from classes import table_widget


# 門診掛號 2018.01.22
class DialogPatient(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogPatient, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        row = args[2]

        self.patient_key = None
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._set_data(row)

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_PATIENT, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_patient_list = table_widget.TableWidget(self.ui.tableWidget_patient_list, self.database)
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.button_accepted)
        self.ui.buttonBox.rejected.connect(self.button_rejected)
        self.ui.tableWidget_patient_list.doubleClicked.connect(self.table_double_clicked)

    def _set_table_width(self):
        width = [80, 80, 40, 120, 120, 80, 120, 120, 500]
        self.table_widget_patient_list.set_table_heading_width(width)

    def _set_data(self, row):
        self.table_widget_patient_list.set_db_data(None, self._set_table_data, row)

    def _set_table_data(self, rec_no, rec):
        patient_rec = [str(rec['PatientKey']),
                       str(rec['Name']),
                       str(rec['Gender']),
                       str(rec['Birthday']),
                       str(rec['ID']),
                       str(rec['InsType']),
                       str(rec['Telephone']),
                       str(rec['Cellphone']),
                       str(rec['Address'])]

        for column in range(len(patient_rec)):
            self.ui.tableWidget_patient_list.setItem(
                rec_no, column,
                QtWidgets.QTableWidgetItem(patient_rec[column])
            )

    def button_accepted(self):
        self.patient_key = self.table_widget_patient_list.field_value(0)

    def button_rejected(self):
        self.patient_key = None

    def table_double_clicked(self):
        self.patient_key = self.table_widget_patient_list.field_value(0)
        self.close()

    def get_patient_key(self):
        return self.patient_key

