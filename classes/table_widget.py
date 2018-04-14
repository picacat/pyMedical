from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from libs import number


# tableWidget 設定 2018.03.29
class TableWidget:
    # 初始化
    def __init__(self, table_widget, database):
        self.table_widget = table_widget
        self.database = database
        self.sql = None
        self.process_data = None
        self.db_row_count = 0
        self.is_set_heading = False

    # 解構
    def __del__(self):
        pass

    # 設定 tableWidget heading width
    def set_table_heading_width(self, width):
        for i in range(0, self.table_widget.columnCount()):
            self.table_widget.setColumnWidth(i, width[i])

        self.is_set_heading = True

    def set_column_hidden(self, hidden_columns=[]):
        for i in hidden_columns:
            self.table_widget.setColumnHidden(i, True)

    # 設定資料庫資料
    def set_db_data(self, sql=None, process_data=None, rows=None):
        self.sql = sql
        self.process_data = process_data

        if rows is None:
            rows = self.database.select_record(self.sql)

        self.db_row_count = len(list(rows))

        self.table_widget.setRowCount(self.db_row_count)
        for i, rec in zip(range(0, self.db_row_count), rows):
            self.process_data(i, rec)

        if not self.is_set_heading:
            self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
            self.table_widget.resizeColumnsToContents()

        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.selectRow(0)
        self.table_widget.setFocus(True)

    def row_count(self):
        return self.table_widget.rowCount()

    # 取得欄位內容 by index no
    def field_value(self, field_index):
        row = self.table_widget.currentRow()
        return self.table_widget.item(row, field_index).text()

    # 重新整理
    def refresh(self):
        if self.sql is None:
            return

        self.set_db_data()
