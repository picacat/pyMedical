#!/usr/bin/env python3
# 資料轉檔 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_utils
from libs import system_utils
from libs import string_utils
from classes import db
from convert import cvt_utec


# 主視窗
class DialogConvert(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogConvert, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.source_db = None

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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_CONVERT, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Yes).setText('開始轉檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.No).setText('關閉')
        self._set_combo_box()

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_utec_product, ['Medical', 'Med2000'])

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.buttonBox.rejected.connect(self.rejected_button_clicked)
        self.ui.pushButton_test_connection.clicked.connect(self.test_connection)
        self.ui.pushButton_change_encoding.clicked.connect(self.change_encoding)

    # 開始轉檔
    def accepted_button_clicked(self):
        if self.ui.tabWidget_convert.tabText(self.ui.tabWidget_convert.currentIndex()) == '友杏轉檔':
            cvt = cvt_utec.CvtUtec(self)
            cvt.convert()

    # 關閉
    def rejected_button_clicked(self):
        self.close()

    def test_connection(self):
        if string_utils.xstr(self.ui.lineEdit_database.text()) == '':
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('連線失敗')
            msg_box.setText("<font size='4' color='Red'><b>連線至資料庫主機失敗! 資料庫名稱空白.</b></font>")
            msg_box.setInformativeText("請輸入資料庫名稱.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        self.source_db = db.Database(
            host=self.ui.lineEdit_host.text(),
            user=self.ui.lineEdit_user.text(),
            password=self.ui.lineEdit_password.text(),
            charset=self.ui.lineEdit_charset.text(),
            database=self.ui.lineEdit_database.text()
        )
        if not self.source_db.connected():
            return

        self.ui.label_connection_status.setText('已連線')
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('連線成功')
        msg_box.setText("<font size='4' color='Blue'><b>恭喜您! 連線至資料庫主機成功.</b></font>")
        msg_box.setInformativeText("連線成功, 可以執行轉檔作業.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()

    def change_encoding(self):
        sql = '''
            SELECT 
                CONCAT('ALTER TABLE ', tbl.TABLE_NAME, ' CONVERT TO CHARACTER SET {charset};') AS exec_script 
            FROM 
                information_schema.TABLES tbl 
            WHERE 
                tbl.TABLE_SCHEMA = '{database_name}';
        '''.format(
            charset=self.ui.lineEdit_charset.text(),
            database_name=self.ui.lineEdit_database.text(),
        )

        rows = self.database.select_record(sql)
        row_count = len(rows)

        self.progressBar.setMaximum(row_count)
        self.progressBar.setValue(0)
        for row_no, row in zip(range(row_count), rows):
            self.progressBar.setValue(row_no)

            exec_script = row['exec_script']
            try:
                self.database.exec_sql(exec_script)
            except:
                print(exec_script)

        self.progressBar.setValue(row_count)

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('更改成功')
        msg_box.setText("<font size='4' color='Blue'><b>恭喜您! 資料庫編碼更改成功.</b></font>")
        msg_box.setInformativeText("編碼更改成功, 可以儲存更新後的編碼.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
