#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from classes import table_widget


# 地址詞庫 2019.03.08
class DialogAddress(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogAddress, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.lineEdit_address = args[2]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_city()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_ADDRESS, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('匯入')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Close).setText('關閉')

        self.table_widget_district = table_widget.TableWidget(self.ui.tableWidget_district, self.database)
        self.table_widget_street = table_widget.TableWidget(self.ui.tableWidget_street, self.database)
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.tableWidget_city.itemSelectionChanged.connect(self._city_changed)
        self.ui.tableWidget_district.itemSelectionChanged.connect(self._district_changed)
        self.ui.tableWidget_street_index.itemSelectionChanged.connect(self._street_index_changed)
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.buttonBox.rejected.connect(self.rejected_button_clicked)

    def accepted_button_clicked(self):
        self._set_address()
        self.close()

    def rejected_button_clicked(self):
        self.close()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [180]
        self.table_widget_district.set_table_heading_width(width)

        width = [260]
        self.table_widget_street.set_table_heading_width(width)

    def _read_city(self):
        sql = '''
            SELECT City FROM address_list
            GROUP BY City
            ORDER BY ZipCode
        '''
        rows = self.database.select_record(sql)

        row_count = len(rows)
        self.ui.tableWidget_city.setRowCount(0)

        column_count = self.ui.tableWidget_city.columnCount()
        total_row = int(row_count / column_count)
        if row_count % column_count > 0:
            total_row += 1

        for row_no in range(0, total_row):
            self.ui.tableWidget_city.setRowCount(
                self.ui.tableWidget_city.rowCount() + 1
            )
            for col_no in range(0, column_count):
                index = (row_no * column_count) + col_no
                if index >= row_count:
                    break

                self.ui.tableWidget_city.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem(rows[index]['City'])
                )

        self.ui.tableWidget_city.resizeRowsToContents()
        self.ui.tableWidget_city.setCurrentCell(0, 0)

    def _city_changed(self):
        if not self.ui.tableWidget_city.selectedItems():
            return

        city = self.ui.tableWidget_city.selectedItems()[0].text()
        self._read_district(city)

    def _read_district(self, city):
        sql = '''
            SELECT District FROM address_list
            WHERE
                City = "{city}"
            GROUP BY District
            ORDER BY ZipCode
        '''.format(city=city)
        self.table_widget_district.set_db_data(sql, self._set_district_data)
        self._read_street_index()

    def _set_district_data(self, row_no, row):
        district_row = [
            string_utils.xstr(row['District']),
        ]

        for column in range(len(district_row)):
            self.ui.tableWidget_district.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(district_row[column])
            )

    def _district_changed(self):
        self._read_street_index()

    def _read_street_index(self):
        if not self.ui.tableWidget_city.selectedItems():
            return

        city = self.ui.tableWidget_city.selectedItems()[0].text()
        district = self.table_widget_district.field_value(0)

        sql = '''
            SELECT SUBSTRING(Street, 1, 1) AS Street FROM address_list
            WHERE
                City = "{city}" AND
                District = "{district}"
            GROUP BY SUBSTRING(Street, 1, 1)
            ORDER BY CAST(CONVERT(`Street` using big5) AS BINARY)
        '''.format(
            city=city,
            district=district,
        )

        rows = self.database.select_record(sql)

        row_count = len(rows)
        self.ui.tableWidget_street_index.setRowCount(0)

        column_count = self.ui.tableWidget_street_index.columnCount()
        total_row = int(row_count / column_count)
        if row_count % column_count > 0:
            total_row += 1

        for row_no in range(0, total_row):
            self.ui.tableWidget_street_index.setRowCount(
                self.ui.tableWidget_street_index.rowCount() + 1
            )
            for col_no in range(0, column_count):
                index = (row_no * column_count) + col_no
                if index >= row_count:
                    break

                self.ui.tableWidget_street_index.setItem(
                    row_no, col_no, QtWidgets.QTableWidgetItem(rows[index]['Street'])
                )
                self.ui.tableWidget_street_index.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        self.ui.tableWidget_street_index.resizeRowsToContents()
        self.ui.tableWidget_street_index.setCurrentCell(0, 0)

    def _street_index_changed(self):
        if not self.ui.tableWidget_street_index.selectedItems():
            return

        self._read_street()

    def _read_street(self):
        if not self.ui.tableWidget_city.selectedItems():
            return

        if not self.ui.tableWidget_street_index.selectedItems():
            return

        city = self.ui.tableWidget_city.selectedItems()[0].text()
        district = self.table_widget_district.field_value(0)
        street_index = self.ui.tableWidget_street_index.selectedItems()[0].text()

        sql = '''
            SELECT Street FROM address_list
            WHERE
                City = "{city}" AND
                District = "{district}" AND
                Street LIKE "{street_index}%"
            GROUP BY Street 
            ORDER BY CAST(CONVERT(`Street` using big5) AS BINARY)
        '''.format(
            city=city,
            district=district,
            street_index=street_index,
        )

        self.table_widget_street.set_db_data(sql, self._set_street_data)

    def _set_street_data(self, row_no, row):
        street_row = [
            string_utils.xstr(row['Street']),
        ]

        for column in range(len(street_row)):
            self.ui.tableWidget_street.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(street_row[column])
            )

    def _set_address(self):
        city = self.ui.tableWidget_city.selectedItems()[0].text()
        district = self.table_widget_district.field_value(0)
        street = self.table_widget_street.field_value(0)

        address = city + district + street

        if self.ui.lineEdit_aly.text().strip() != '':
            address += self.ui.lineEdit_aly.text().strip() + '巷'
        if self.ui.lineEdit_lane.text().strip() != '':
            address += self.ui.lineEdit_lane.text().strip() + '弄'

        if self.ui.lineEdit_sub_number.text().strip() != '':
            address += '{0}-{1}號'.format(
                self.ui.lineEdit_number.text().strip(),
                self.ui.lineEdit_sub_number.text().strip()
            )
        else:
            if self.ui.lineEdit_number.text().strip() != '':
                address += self.ui.lineEdit_number.text().strip() + '號'

        if self.ui.lineEdit_floor.text().strip() != '':
            address += self.ui.lineEdit_floor.text().strip() + '樓'
        if self.ui.lineEdit_sub_floor.text().strip() != '':
            address += '之' + self.ui.lineEdit_sub_floor.text().strip()
        if self.ui.lineEdit_room.text().strip() != '':
            address += ', ' + self.ui.lineEdit_room.text().strip() + '室'

        self.lineEdit_address.setText(address)
