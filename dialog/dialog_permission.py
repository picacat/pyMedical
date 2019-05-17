#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtGui

from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import personnel_utils


# 權限設定 2019.05.17
class DialogPermission(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogPermission, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.person_key = args[2]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_data()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_PERMISSION, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_permission = table_widget.TableWidget(self.ui.tableWidget_permission, self.database)
        self._set_table_width()
        self.ui.tableWidget_permission.setFocus(True)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.toolButton_select_all.clicked.connect(self._set_selection_tool_button)
        self.ui.toolButton_diselect_all.clicked.connect(self._set_selection_tool_button)

    def accepted_button_clicked(self):
        self._save_permission()

    def _save_permission(self):
        self.database.exec_sql('DELETE FROM permission WHERE PersonKey = {0}'.format(self.person_key))

        for row_no in range(self.ui.tableWidget_permission.rowCount()):
            program_name = self.ui.tableWidget_permission.item(row_no, 0).text()
            permission_item = self.ui.tableWidget_permission.item(row_no, 1).text()
            check_box = self.ui.tableWidget_permission.cellWidget(row_no, 2)
            if check_box.isChecked():
                permission = 'Y'
            else:
                permission = 'N'

            fields = ['PersonKey', 'ProgramName', 'PermissionItem', 'Permission']
            data = [
                self.person_key,
                program_name,
                permission_item,
                permission,
            ]
            self.database.insert_record('permission', fields, data)

    def _set_table_width(self):
        width = [250, 450, 100]
        self.table_widget_permission.set_table_heading_width(width)

    # 讀取資料
    def _read_data(self):
        self.person_row = self._read_person()
        if self.person_row is None:
            return

        self.person_key = self.person_row['PersonKey']
        self.ui.label_user.setText('{user}權限設定表'.format(
            user=string_utils.xstr(self.person_row['Name'])),
        )

        self._set_permission_table()
        self._read_permission_data()

    def _read_person(self):
        sql = '''
            SELECT * FROM person
            WHERE
                PersonKey = {person_key}
        '''.format(
            person_key=self.person_key
        )
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return None

        return rows[0]

    def _set_permission_table(self):
        self.ui.tableWidget_permission.setRowCount(len(personnel_utils.PERMISSION_LIST))

        for row_no, row in zip(range(len(personnel_utils.PERMISSION_LIST)), personnel_utils.PERMISSION_LIST):
            for col_no in range(len(row)):
                self.ui.tableWidget_permission.setItem(
                    row_no, col_no,
                    QtWidgets.QTableWidgetItem(string_utils.xstr(row[col_no]))
                )

            check_box = QtWidgets.QCheckBox(self.ui.tableWidget_permission)
            check_box.setChecked(False)
            check_box.setStyleSheet('margin:auto')
            self.ui.tableWidget_permission.setCellWidget(row_no, 2, check_box)

            if '執行' in self.ui.tableWidget_permission.item(row_no, 1).text():
                self._set_row_font(row_no)

    def _set_row_font(self, row_no):
        font = QtGui.QFont()
        font.setBold(True)

        for col_no in range(self.ui.tableWidget_permission.columnCount()):
            table_widget_item = self.ui.tableWidget_permission.item(row_no, col_no)
            if table_widget_item is not None:
                table_widget_item.setFont(font)

    def _set_selection_tool_button(self):
        sender_name = self.sender().objectName()
        if sender_name == 'toolButton_select_all':
            checked = True
        else:
            checked = False

        for row_no in range(self.ui.tableWidget_permission.rowCount()):
            check_box = self.ui.tableWidget_permission.cellWidget(row_no, 2)
            check_box.setChecked(checked)

    def _read_permission_data(self):
        for row_no in range(self.ui.tableWidget_permission.rowCount()):
            program_name = self.ui.tableWidget_permission.item(row_no, 0).text()
            permission_item = self.ui.tableWidget_permission.item(row_no, 1).text()
            check_box = self.ui.tableWidget_permission.cellWidget(row_no, 2)
            checked = False

            sql = '''
                SELECT * FROM permission
                WHERE
                    PersonKey = {person_key} AND
                    ProgramName = "{program_name}" AND
                    PermissionItem = "{permission_item}"
            '''.format(
                person_key=self.person_key,
                program_name=program_name,
                permission_item=permission_item,
            )

            rows = self.database.select_record(sql)
            if len(rows) <= 0:
                check_box.setChecked(checked)
                continue

            row = rows[0]
            if string_utils.xstr(row['Permission']) == 'Y':
                checked = True

            check_box.setChecked(checked)

