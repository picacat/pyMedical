from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import Qt
from libs import string_utils
from libs import system_utils


# tableWidget 設定 2018.03.29
class TableWidget:
    # 初始化
    def __init__(self, table_widget, database):
        self.table_widget = table_widget
        self.database = database
        self.process_data = None
        self.db_row_count = 0
        self.is_set_heading = False
        self.sort = QtCore.Qt.AscendingOrder
        self._set_signal()

    # 解構
    def __del__(self):
        pass

    def _set_signal(self):
        self.table_widget.horizontalHeader().sectionClicked.connect(
            self._table_widget_header_clicked
        )

    def _table_widget_header_clicked(self, col_no):
        self.table_widget.sortItems(col_no, self.sort)
        if self.sort == QtCore.Qt.AscendingOrder:
            self.sort = QtCore.Qt.DescendingOrder
        else:
            self.sort = QtCore.Qt.AscendingOrder

    # 設定 tableWidget heading width
    def set_table_heading_width(self, width):
        for i in range(0, len(width)):
            if self.table_widget.horizontalHeaderItem(i) is None:
                continue

            self.table_widget.setColumnWidth(i, width[i])
            self.table_widget.horizontalHeaderItem(i).setTextAlignment(Qt.AlignLeft)

        self.is_set_heading = True

    def set_column_hidden(self, hidden_columns=None):
        for i in hidden_columns:
            self.table_widget.setColumnHidden(i, True)

    # 設定資料庫資料
    def set_db_data(self, sql=None, process_data=None, rows=None, start_index=0, set_focus=True):
        self.process_data = process_data

        if rows is None:
            rows = self.database.select_record(sql)

        self.db_row_count = len(list(rows)) + start_index
        self.table_widget.setRowCount(self.db_row_count)
        for i, rec in zip(range(start_index, self.db_row_count), rows):
            self.process_data(i, rec)

        if not self.is_set_heading:
            self.table_widget.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
            self.table_widget.resizeColumnsToContents()

        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.selectRow(0)
        if set_focus:
            self.table_widget.setFocus(True)

        self.table_widget.resizeRowsToContents()

    # 設定資料庫資料
    def set_db_data_without_heading(self, sql, field, align=None):
        rows = self.database.select_record(sql)

        row_count = len(rows)
        self.table_widget.setRowCount(0)

        column_count = self.table_widget.columnCount()
        total_row = int(row_count / column_count)
        if row_count % column_count > 0:
            total_row += 1

        self.table_widget.setRowCount(total_row)
        for row_no in range(total_row):
            for col_no in range(column_count):
                index = (row_no * column_count) + col_no
                if index >= row_count:
                    break

                self.table_widget.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem(rows[index][field])
                )
                if align is not None:
                    self.table_widget.item(
                        row_no, col_no).setTextAlignment(
                        align | QtCore.Qt.AlignVCenter
                    )

        self.table_widget.resizeRowsToContents()
        self.table_widget.setCurrentCell(0, 0)
        # database.table_widget.setFocus(True)

    def row_count(self):
        return self.table_widget.rowCount()

    # 取得欄位內容 by index no
    def field_value(self, field_index):
        row = self.table_widget.currentRow()

        try:
            field_value = self.table_widget.item(row, field_index).text()
        except AttributeError:
            field_value = None

        return field_value

    def cell_widget(self, field_index):
        row = self.table_widget.currentRow()

        try:
            widget = self.table_widget.cellWidget(row, field_index).text()
        except AttributeError:
            widget = None

        return widget

    def set_cell_text_format(self, row_index, column_index, text_format, variable_type=None):
        item = self.table_widget.item(row_index, column_index)
        if item is None:
            return

        self.table_widget.setCurrentCell(row_index, column_index + 1)
        self.table_widget.setCurrentCell(row_index, column_index)

        try:
            if variable_type == 'float':
                field_text = format(float(item.text()), text_format)
            else:
                field_text = format(int(item.text()), text_format)
        except ValueError:
            field_text = item.text()

        self.table_widget.setItem(
            row_index, column_index, QtWidgets.QTableWidgetItem(field_text)
        )
        self.table_widget.item(row_index, column_index).setTextAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_row_color(self, row_index, color):
        for column in range(self.table_widget.columnCount()):
            self.table_widget.item(
                row_index, column).setForeground(color)

    def find_error(self, field_no):
        self.table_widget.setFocus(True)
        for row_no in range(
                self.table_widget.currentRow()+1, self.table_widget.rowCount()):
            self.table_widget.setCurrentCell(row_no, field_no)
            error_message = string_utils.xstr(
                self.table_widget.item(row_no, field_no).text()
            )
            if error_message != '':
                break

        if (self.table_widget.currentRow() ==
                self.table_widget.rowCount() - 1):
            system_utils.show_message_box(
                QMessageBox.Information,
                '尋找錯誤',
                '<font size="4" color="red"><b>所有的錯誤資料均已瀏覽完畢.</b></font>',
                '請按確定鍵繼續.'
            )
            self.table_widget.setCurrentCell(0, field_no)

            # error_message = string_utils.xstr(
            #     database.table_widget_wait.item(0, field_no).text()
            # )
            #
            # if error_message == '':
            #     database.find_error(field_no)

    def set_dict(self, in_dict):
        self.table_widget.setRowCount(len(in_dict))
        self.table_widget.setAlternatingRowColors(True)

        for row_no, field in zip(range(len(in_dict)), in_dict):
            self.table_widget.setItem(
                row_no, 0,
                QtWidgets.QTableWidgetItem(string_utils.xstr(field))
            )
            self.table_widget.setItem(
                row_no, 1,
                QtWidgets.QTableWidgetItem(string_utils.xstr(in_dict[field]))
            )

            self.table_widget.item(
                row_no, 1).setTextAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
