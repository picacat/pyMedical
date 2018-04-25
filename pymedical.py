#!/usr/bin/env python3
#coding: utf-8

import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import os

from libs import ui_settings
from libs import modules
from libs import system
from dialog import dialog_system_settings
from classes import system_settings, db


# 主畫面
class PyMedical(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, *args):
        super(PyMedical, self).__init__(*args)
        self.database = db.Database()
        if not self.database.connected():
            sys.exit(0)
            return

        self.system_settings = system_settings.SystemSettings(self.database)
        self.ui = None

        self._check_db()
        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉主程式
    def closeEvent(self, event: QtGui.QCloseEvent):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('關閉醫療系統')
        msg_box.setText("<font size='5' color='red'><b>確定要關閉醫療資訊管理系統?</b></font>")
        msg_box.setInformativeText("<font size='4'>注意！系統結束後, 會自動執行資料備份作業，請稍後...</font>")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)  # 0
        msg_box.addButton(QPushButton("關閉醫療系統"), QMessageBox.AcceptRole)  # 1
        quit_app = msg_box.exec_()

        if quit_app:
            event.accept()
        else:
            event.ignore()

    # 檢查資料庫狀態
    def _check_db(self):
        mysql_path = './mysql'
        mysql_files = [f for f in os.listdir(mysql_path) if os.path.isfile(os.path.join(mysql_path, f))]
        for file in mysql_files:
            table_name = file.split('.sql')[0]
            self.database.check_table_exists(table_name)

    # 關閉
    def close_all(self):
        self.database.close_database()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_PY_MEDICAL, self)
        system.set_css(self)
        system.set_theme(self.ui, self.system_settings)
        self.ui.tabWidget_window.setTabsClosable(True)
        self.showMaximized()

    # 設定信號
    def _set_signal(self):
        self.ui.pushButton_registration.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_return_card.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_checkout.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_waiting_list.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_medical_record_list.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_record_statistics.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_patient_list.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_settings.clicked.connect(self.open_settings)
        self.ui.pushButton_charge.clicked.connect(self.push_button_clicked)

        self.ui.tabWidget_window.tabCloseRequested.connect(self.close_tab)
        self.ui.tabWidget_window.currentChanged.connect(self.tab_changed)

    def tab_changed(self, i):
        tab_name = self.ui.tabWidget_window.tabText(i)
        tab = self.ui.tabWidget_window.currentWidget()
        if tab_name == '門診掛號':
            tab.read_wait()
        elif tab_name == '醫師看診作業':
            tab.read_wait()

    # 按鍵驅動
    def push_button_clicked(self):
        tab_name = self.sender().text()
        self._add_tab(tab_name, self.database, self.system_settings)

    # 新增tab
    def _add_tab(self, tab_name, *args):
        if self._is_tab_exists(tab_name):
            return

        module_name = modules.get_module_name(tab_name)
        new_tab = module_name(self, *args)
        self.ui.tabWidget_window.addTab(new_tab, tab_name)
        self.ui.tabWidget_window.setCurrentWidget(new_tab)
        self._set_focus(tab_name, new_tab)

    @staticmethod
    def _set_focus(widget_name, widget):
        if widget_name == "門診掛號":
            widget.ui.lineEdit_query.setFocus()
        elif widget_name == "醫師看診作業":
            widget.ui.tableWidget_waiting_list.setFocus()
        elif widget_name == "新病患資料":
            widget.ui.lineEdit_name.setFocus()
        elif widget_name == "病歷查詢":
            widget.open_dialog()
        elif widget_name == "病患查詢":
            widget.open_dialog()

    # 關閉 tab
    def close_tab(self, current_index):
        current_tab = self.ui.tabWidget_window.widget(current_index)
        tab_name = self.ui.tabWidget_window.tabText(current_index)
        if tab_name == '首頁':
            return

        if not self._tab_is_closable(tab_name, current_tab):
            return

        current_tab.close_all()
        current_tab.deleteLater()
        self.ui.tabWidget_window.removeTab(current_index)
        if tab_name.find('病歷資料') != -1:
            self._set_tab(current_tab.call_from)
        elif tab_name.find('病患資料') != -1:
            self._set_tab(current_tab.call_from)

    def _tab_is_closable(self, tab_name, current_tab):
        closable = True

        if tab_name.find('病歷資料') == -1:
            return closable

        record_modified = current_tab.record_modified()
        if not record_modified:
            return closable

        if not current_tab.record_saved:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('關閉病歷資料')
            msg_box.setText("<font size='4' color='red'><b>病歷資料已被變更, 確定離開病歷資料而不存檔?</b></font>")
            msg_box.setInformativeText("注意！選擇不存檔而關閉病歷資料後, 之前所輸入的病歷資料將會回復原來狀態.")
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)  # 0
            msg_box.addButton(QPushButton("存檔"), QMessageBox.AcceptRole)  # 1
            msg_box.addButton(QPushButton("不存檔"), QMessageBox.YesRole)  # 2
            quit_medical_record = msg_box.exec_()
            if not quit_medical_record:
                closable = False
            else:
                closable = True

            if quit_medical_record == 1:  # 存檔
                current_tab.save_medical_record()

        return closable

    # 檢查是否開啟tab
    def _is_tab_exists(self, tab_text):
        if self.ui.tabWidget_window.count() <= 0:
            return False

        for i in range(self.ui.tabWidget_window.count()):
            if self.ui.tabWidget_window.tabText(i) == tab_text:
                self.ui.tabWidget_window.setCurrentIndex(i)
                return True

        return False

    # 打開指定的tab
    def _set_tab(self, tab_name):
        if self.ui.tabWidget_window.count() <= 0:
            return False

        for i in range(self.ui.tabWidget_window.count()):
            if self.ui.tabWidget_window.tabText(i) == tab_name:
                current_tab = self.ui.tabWidget_window.widget(i)
                self.ui.tabWidget_window.setCurrentIndex(i)
                if tab_name == '病歷查詢':
                    current_tab.ui.tableWidget_medical_record_list.setFocus(True)
                elif tab_name == '病患查詢':
                    current_tab.ui.tableWidget_patient_list.setFocus(True)

                return

    def open_medical_record(self, case_key, call_from=None):
        script = ('select CaseKey, PatientKey, Name from cases where CaseKey = {0}'.format(case_key))
        try:
            row = self.database.select_record(script)[0]
        except IndexError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('查無病歷資料')
            msg_box.setText("<font size='4' color='red'><b>雖然掛號資料存在, 但是病歷資料因不明原因遺失!</b></font>")
            msg_box.setInformativeText("請至掛號作業刪除此筆掛號資料並重新掛號.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        tab_name = '{0}-{1}-病歷資料'.format(str(row['PatientKey']), str(row['Name']))
        self._add_tab(tab_name, (self.database, self.system_settings, row['CaseKey'], call_from))

    def open_patient_record(self, patient_key, call_from=None):
        if patient_key is None:
            tab_name = '新病患資料'
            self._add_tab(tab_name, (self.database, self.system_settings, patient_key, call_from))
            return

        script = 'SELECT PatientKey, Name FROM patient WHERE PatientKey = {0}'.format(patient_key)
        try:
            row = self.database.select_record(script)[0]
        except IndexError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('查無病患資料')
            msg_box.setText("<font size='4' color='red'><b>雖然掛號資料存在, 但是病歷資料因不明原因遺失!</b></font>")
            msg_box.setInformativeText("請至掛號作業刪除此筆掛號資料並重新掛號.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        tab_name = '{0}-{1}-病患資料'.format(str(row['PatientKey']), str(row['Name']))
        self._add_tab(tab_name, (self.database, self.system_settings, row['PatientKey'], call_from))

    def set_new_patient(self, new_patient_key):
        current_tab = None
        for i in range(self.ui.tabWidget_window.count()):
            if self.ui.tabWidget_window.tabText(i) == '門診掛號':
                current_tab = self.ui.tabWidget_window.widget(i)
                break

        current_tab.ui.lineEdit_query.setText(str(new_patient_key))
        current_tab.query_clicked()

    # 系統設定
    def open_settings(self):
        dialog = dialog_system_settings.DialogSettings(self.ui, self.database, self.system_settings)
        dialog.exec_()
        del dialog


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = PyMedical()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
