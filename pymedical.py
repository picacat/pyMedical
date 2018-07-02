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
from dialog import dialog_ic_card
from classes import system_settings, db
from convert import convert
import login


# 主畫面
class PyMedical(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(PyMedical, self).__init__(parent)
        self.database = db.Database()
        if not self.database.connected():
            sys.exit(0)

        self.system_settings = system_settings.SystemSettings(self.database)
        self.ui = None

        self._check_db()
        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.database.close_database()

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

        self.database.check_field_exists('icd10', 'Groups', 'VARCHAR (100) AFTER SpecialCode')

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_PY_MEDICAL, self)
        system.set_css(self)
        system.set_theme(self.ui, self.system_settings)
        self.ui.tabWidget_window.setTabsClosable(True)
        self._set_button_enabled()
        self.ui.setWindowTitle('{0} 醫療資訊管理系統'.format(self.system_settings.field('院所名稱')))

    # 設定按鈕權限
    def _set_button_enabled(self):
        if self.system_settings.field('使用讀卡機') == 'Y':
            self.ui.pushButton_ic_card.setEnabled(True)
        else:
            self.ui.pushButton_ic_card.setEnabled(False)

    # 設定信號
    def _set_signal(self):
        self.ui.action_convert.triggered.connect(self.convert)
        self.ui.pushButton_registration.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_return_card.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_checkout.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_waiting_list.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_medical_record_list.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_record_statistics.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_patient_list.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_settings.clicked.connect(self.open_settings)
        self.ui.pushButton_charge.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_users.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_diagnostic.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_medicine.clicked.connect(self.push_button_clicked)
        self.ui.pushButton_ic_card.clicked.connect(self.open_ic_card)

        self.ui.tabWidget_window.tabCloseRequested.connect(self.close_tab)
        self.ui.tabWidget_window.currentChanged.connect(self.tab_changed)

    def tab_changed(self, i):
        tab_name = self.ui.tabWidget_window.tabText(i)
        tab = self.ui.tabWidget_window.currentWidget()
        if tab_name == '門診掛號':
            tab.read_wait()
        elif tab_name == '醫師看診作業':
            tab.read_wait()
        elif tab_name == '健保卡欠還卡':
            tab.read_return_card()

    # 按鍵驅動
    def push_button_clicked(self):
        tab_name = self.sender().text()
        self._add_tab(tab_name, self.database, self.system_settings)

    # 新增tab
    def _add_tab(self, tab_name, *args):
        if self._tab_exists(tab_name):
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

        if current_tab.call_from == '醫師看診作業' and not current_tab.record_saved:
            current_tab.update_medical_record()
            current_tab.save_prescript()

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
    def _tab_exists(self, tab_text):
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
                    current_tab.refresh_patient_record()
                elif tab_name == '門診掛號':
                    current_tab.read_wait()

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

    def open_patient_record(self, patient_key, call_from=None, ic_card=None):
        if patient_key is None:
            tab_name = '新病患資料'
            self._add_tab(tab_name, (self.database, self.system_settings, patient_key, call_from, ic_card))
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
        self._add_tab(tab_name, (self.database, self.system_settings, row['PatientKey'], call_from, None))

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
        dialog.deleteLater()
        self._set_button_enabled()

    # 系統設定
    def open_ic_card(self):
        dialog = dialog_ic_card.DialogICCard(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    # 轉檔
    def convert(self):
        dialog = convert.DialogConvert(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    def set_status_bar(self):
        label_station_no = QtWidgets.QLabel()
        label_station_no.setText('工作站編號: {0}'.format(self.system_settings.field('工作站編號')))
        label_station_no.setFixedWidth(200)
        self.ui.statusbar.addPermanentWidget(label_station_no)

        label_user_name = QtWidgets.QLabel()
        label_user_name.setText('使用者: {0}'.format(self.system_settings.field('使用者')))
        label_user_name.setFixedWidth(200)
        self.ui.statusbar.addPermanentWidget(label_user_name)

    def set_root_permission(self):
        if self.system_settings.field('使用者') != '超級使用者':
            self.action_convert.setEnabled(False)
        else:
            self.action_convert.setEnabled(True)


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    py_medical = PyMedical()

    py_medical.system_settings.post('使用者', None)
    login_dialog = login.Login(py_medical, py_medical.database, py_medical.system_settings)
    login_dialog.exec_()
    if not login_dialog.login_ok:
        return

    login_dialog.deleteLater()
    user_name = login_dialog.user_name
    py_medical.system_settings.post('使用者', user_name)
    py_medical.set_status_bar()
    py_medical.set_root_permission()
    py_medical.showMaximized()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
