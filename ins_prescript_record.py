#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
import sys

from PyQt5 import QtGui
from libs import ui_settings
from libs import strings
from classes import table_widget


# 輸入健保處方 2018.04.14
class InsPrescriptRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(InsPrescriptRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_prescript()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_INS_PRESCRIPT_RECORD, self)
        self.table_widget_prescript = table_widget.TableWidget(self.ui.tableWidget_prescript, self.database)
        self.table_widget_prescript.set_column_hidden([0])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_add.clicked.connect(self.add_medicine)
        self.ui.toolButton_delete.clicked.connect(self.delete_medicine)

    def _set_table_width(self):
        width = [70,
                 250, 60, 40, 50]
        self.table_widget_prescript.set_table_heading_width(width)

    def _read_prescript(self):
        sql = ('SELECT * FROM prescript '
               'WHERE '
               'CaseKey = {0} AND '
               'MedicineSet = 1 '
               'ORDER BY PrescriptKey'.format(self.case_key))
        self.table_widget_prescript.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, rec_no, rec):
        prescript_rec = [
            strings.xstr(rec['PrescriptKey']),
            strings.xstr(rec['MedicineName']),
            strings.xstr(rec['Dosage']),
            strings.xstr(rec['Unit']),
            strings.xstr(rec['Instruction']),
        ]

        for column in range(0, self.ui.tableWidget_prescript.columnCount()):
            self.ui.tableWidget_prescript.setItem(rec_no,
                                                  column,
                                                  QtWidgets.QTableWidgetItem(prescript_rec[column]))
            if column in [2]:
                self.ui.tableWidget_prescript.item(rec_no, column)\
                    .setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [3]:
                self.ui.tableWidget_prescript.item(rec_no, column)\
                    .setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            if rec['InsCode'] == '':
                self.ui.tableWidget_prescript.item(rec_no, column).setForeground(QtGui.QColor('blue'))

    # 增加處方資料
    def add_medicine(self):
        row_count = self.table_widget_prescript.row_count()
        print(row_count)
        if row_count <= 0:
            self._insert_row(row_count)
            return

        item = self.ui.tableWidget_prescript.item(row_count-1, 1)

        if item is None or item.text().strip() == '':
            return

        self._insert_row(row_count)

    def _insert_row(self, index):
        self.ui.tableWidget_prescript.setFocus(True)
        self.ui.tableWidget_prescript.insertRow(index)
        self.ui.tableWidget_prescript.setCurrentCell(index, 1)

    # 刪除處方
    def delete_medicine(self):
        index = self.ui.tableWidget_prescript.currentRow()
        self.ui.tableWidget_prescript.removeRow(index)


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = InsPrescriptRecord()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
