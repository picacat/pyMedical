
# 輸入處方 2018.06.15
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QPushButton

import datetime
import os.path
from os import listdir
import ntpath
import shutil
import sys
import datetime

from classes import table_widget
from libs import ui_utils
from libs import system_utils
from libs import string_utils


# 主視窗
class SystemUpdate(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(SystemUpdate, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉G
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_SYSTEM_UPDATE, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('開始更新')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.toolButton_open_file.clicked.connect(self._open_file)
        self.ui.lineEdit_file_name.textChanged.connect(self._file_name_changed)

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.table_widget_file_list = table_widget.TableWidget(self.ui.tableWidget_file_list, self.database)
        self._set_table_width()

        self.ui.lineEdit_file_name.setFocus()

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)

    def _set_table_width(self):
        width = [200, 220, 350, 200]
        self.table_widget_file_list.set_table_heading_width(width)

    def _open_file(self):
        options = QFileDialog.Options()

        fileName, _ = QFileDialog.getOpenFileName(self,
            "開啟更新檔", '*.zip',
            "zip 壓縮檔 (*.zip);;Text Files (*.txt)", options = options)
        if fileName:
            self.ui.lineEdit_file_name.setText(fileName)

    def _file_name_changed(self):
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        file_name = self.ui.lineEdit_file_name.text()
        if file_name == '':
            return

        if not os.path.isfile(file_name):
            return

        self._check_files()
        if self.ui.tableWidget_file_list.rowCount() <= 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('系統更新完成')
            msg_box.setText("<font size='4'><b>系統已經是最新檔, 不需更新.</b></font>")
            msg_box.setInformativeText("請按取消鍵結束系統更新.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

    def accepted_button_clicked(self):
        self._update_files()

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('系統更新完成')
        msg_box.setText("<font size='4'><b>恭喜您! 系統已更新至最新檔, 系統檔案全部更新成功.</b></font>")
        msg_box.setInformativeText("為了讓更新檔生效, 請退出系統重新執行.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()


    def _check_files(self):
        dest_root = os.path.dirname(os.path.abspath(__file__))

        zip_file_name = self.ui.lineEdit_file_name.text()
        temp_dir = os.path.join(dest_root, '_temp')
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

        os.mkdir(temp_dir)
        system_utils.unzip_file(zip_file_name, temp_dir)

        zip_dir = ntpath.basename(zip_file_name).split('.')[0]

        zip_source_root = os.path.join(temp_dir, zip_dir)

        self.ui.tableWidget_file_list.setRowCount(0)

        self._list_files(zip_source_root, dest_root, '')
        self._list_files(zip_source_root, dest_root, 'classes')
        self._list_files(zip_source_root, dest_root, 'convert')
        self._list_files(zip_source_root, dest_root, 'css')
        self._list_files(zip_source_root, dest_root, 'dialog')
        self._list_files(zip_source_root, dest_root, 'libs')
        self._list_files(zip_source_root, dest_root, 'mysql')
        self._list_files(zip_source_root, dest_root, 'printer')
        self._list_files(zip_source_root, dest_root, 'ui')

        self.ui.tableWidget_file_list.resizeRowsToContents()

    def _list_files(self, zip_source_root, dest_root, dir_name):
        source_dir = os.path.join(zip_source_root, dir_name)
        dest_dir = os.path.join(dest_root, dir_name)

        source_files = [f for f in listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]

        for file in source_files:
            source_file_name = file
            source_file_date = datetime.datetime.fromtimestamp(
                self.creation_date(os.path.join(source_dir, source_file_name))
            )
            row = [source_file_name, source_dir, dest_dir, source_file_date]

            dest_file_name = os.path.join(dest_dir, source_file_name)
            if not os.path.isfile(dest_file_name):
                self._add_list(row)
                continue

            dest_file_date = datetime.datetime.fromtimestamp(
                self.creation_date(os.path.join(dest_dir, dest_file_name))
            )
            if source_file_date > dest_file_date:
                self._add_list(row)

    def _add_list(self, row):
        row_no = self.ui.tableWidget_file_list.rowCount()
        self.ui.tableWidget_file_list.setRowCount(row_no + 1)

        for column in range(len(row)):
            self.ui.tableWidget_file_list.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(string_utils.xstr(row[column]))
            )

    def creation_date(self, file_name):
        # if sys.platform == 'win32':
        #     return os.path.getctime(file_name)
        # else:
        #     return os.stat(file_name).st_mtime

        return os.stat(file_name).st_mtime

    def _update_files(self):
        row_count = self.ui.tableWidget_file_list.rowCount()
        self.ui.progressBar.setMaximum(row_count)

        for row_no in range(row_count):
            self.ui.progressBar.setValue(row_no)
            source_dir = self.ui.tableWidget_file_list.item(row_no, 1).text()
            dest_dir = self.ui.tableWidget_file_list.item(row_no, 2).text()

            source_file_name = os.path.join(source_dir, self.ui.tableWidget_file_list.item(row_no, 0).text())
            dest_file_name = os.path.join(dest_dir, self.ui.tableWidget_file_list.item(row_no, 0).text())

            shutil.copy2(source_file_name, dest_file_name)

