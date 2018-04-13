#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
import datetime
from libs import ui_settings
from libs import strings
from classes import table_widget


# 樣板 2018.01.31
class ReturnCard(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ReturnCard, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_return_card()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_RETURN_CARD, self)
        self.table_widget_return_card = table_widget.TableWidget(self.ui.tableWidget_return_card, self.database)
        self.table_widget_return_card.set_column_hidden([0, 1])
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_close.triggered.connect(self.close_return_card)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [80, 80, 80, 80, 120, 130, 150, 180, 180, 60, 80, 40, 80, 80, 80]
        self.table_widget_return_card.set_table_heading_width(width)

    def _read_return_card(self):
        last_date = datetime.date.today().replace(day=1) - datetime.timedelta(days=1)
        last_return_date = last_date.strftime('%Y-%m-01')
        sql = 'SELECT * FROM deposit WHERE DepositDate >= "{0}" ORDER BY DepositDate DESC'.format(last_return_date)
        self.table_widget_return_card.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, rec_no, rec):
        patient_rec = self.database.select_record('SELECT * FROM patient WHERE PatientKey = {0}'.format(rec['PatientKey']))[0]
        try:
            medical_rec = self.database.select_record('SELECT Card, Continuance FROM cases WHERE CaseKey = {0}'.format(rec['CaseKey']))[0]
        except IndexError:
            medical_rec = {'Card': None, 'Continuance': None}

        return_card_rec = [
            str(rec['DepositKey']),
            str(rec['CaseKey']),
            str(rec['PatientKey']),
            str(rec['Name']),
            str(patient_rec['Birthday']),
            str(patient_rec['ID']),
            str(patient_rec['CardNo']),
            strings.xstr(rec['DepositDate']),
            strings.xstr(rec['ReturnDate']),
            strings.xstr(rec['Period']),
            strings.xstr(medical_rec['Card']),
            strings.xstr(medical_rec['Continuance']),
            strings.xstr(rec['Register']),
            strings.xstr(rec['Refunder']),
            strings.xstr(rec['Fee']),
        ]

        for column in range(0, self.ui.tableWidget_return_card.columnCount()):
            self.ui.tableWidget_return_card.setItem(rec_no,
                                                    column,
                                                    QtWidgets.QTableWidgetItem(return_card_rec[column]))
            if column in [2, 14]:
                self.ui.tableWidget_return_card.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [8]:
                self.ui.tableWidget_return_card.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_return_card(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = ReturnCard()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
