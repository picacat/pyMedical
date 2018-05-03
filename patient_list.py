#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import sys

from libs import ui_settings
from libs import strings
from dialog import dialog_patient_list
from classes import table_widget


# 主視窗
class PatientList(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(PatientList, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_PATIENT_LIST, self)
        self.table_widget_patient_list = table_widget.TableWidget(self.ui.tableWidget_patient_list, self.database)
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_requery.triggered.connect(self.open_dialog)
        self.ui.action_delete_record.triggered.connect(self.delete_patient_record)
        self.ui.action_open_record.triggered.connect(self.open_patient_record)
        self.ui.action_close.triggered.connect(self.close_patient_list)
        self.ui.tableWidget_patient_list.doubleClicked.connect(self.open_patient_record)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 100, 40, 120, 120, 60, 80, 80, 180, 120, 120, 120, 400]
        self.table_widget_patient_list.set_table_heading_width(width)

    # 讀取病歷
    def _get_sql(self):
        dialog = dialog_patient_list.DialogPatientList(self.ui, self.database, self.system_settings)
        result = dialog.exec_()
        sql = dialog.get_sql()
        dialog.close_all()

        if result == 0:
            return None
        else:
            return sql

    def open_dialog(self):
        sql = self._get_sql()
        if sql is None:
            return

        self.table_widget_patient_list.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, rec_no, rec):
        patient_record = [
            str(rec['PatientKey']),
            str(rec['Name']),
            strings.xstr(rec['Gender']),
            strings.xstr(rec['Birthday']),
            strings.xstr(rec['ID']),
            strings.xstr(rec['Nationality']),
            strings.xstr(rec['InsType']),
            strings.xstr(rec['DiscountType']),
            strings.xstr(rec['InitDate']),
            strings.xstr(rec['Telephone']),
            strings.xstr(rec['Cellphone']),
            strings.xstr(rec['Email']),
            strings.xstr(rec['Address']),
        ]

        for column in range(0, self.ui.tableWidget_patient_list.columnCount()):
            self.ui.tableWidget_patient_list.setItem(rec_no, column, QtWidgets.QTableWidgetItem(patient_record[column]))
            if column in [0]:
                self.ui.tableWidget_patient_list.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [2]:
                self.ui.tableWidget_patient_list.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

    def delete_patient_record(self):
        name = self.table_widget_patient_list.field_value(1)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除病患資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除<font color='blue'> {0} </font>的病歷資料?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        patient_key = self.table_widget_patient_list.field_value(0)
        self.database.delete_record('patient', 'PatientKey', patient_key)
        current_row = self.ui.tableWidget_patient_list.currentRow()
        self.ui.tableWidget_patient_list.removeRow(current_row)

    def open_patient_record(self):
        patient_key = self.table_widget_patient_list.field_value(0)
        self.parent.open_patient_record(patient_key, '病患查詢')

    def refresh_patient_record(self):
        patient_key = self.table_widget_patient_list.field_value(0)
        sql = 'SELECT * FROM patient where PatientKey = {0}'.format(patient_key)
        row = self.database.select_record(sql)[0]
        current_row = self.ui.tableWidget_patient_list.currentRow()
        self._set_table_data(current_row, row)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_patient_list(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = PatientList()
    widget.show()

    sys.exit(app.exec_())


# 程式進入點
if __name__ == '__main__':
    main()
