#!/usr/bin/env python3
#coding: utf-8

import sys
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
import os

from classes import system_settings, db
from classes import udp_socket_server
from convert import convert

from libs import ui_utils
from libs import module_utils
from libs import system_utils
from libs import personnel_utils

from dialog import dialog_system_settings
from dialog import dialog_ic_card
from dialog import dialog_export_emr_xml

import check_database
import login
import login_statistics
import backup

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis

# 主畫面
class PyMedical(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(PyMedical, self).__init__(parent)
        self.database = db.Database()
        if not self.database.connected():
            sys.exit(0)

        self.check_system_db()

        self.system_settings = system_settings.SystemSettings(self.database)
        self.ui = None
        self.statistics_dicts = None
        self.socket_server = udp_socket_server.UDPSocketServer()

        self._reset_wait()
        self._set_ui()
        self._set_signal()
        self._start_udp_socket_server()

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
            if self.system_settings.field('使用者') != '超級使用者':
                backup_process = backup.Backup(
                    self, self.database, self.system_settings)
                backup_process.start_backup()

            event.accept()
        else:
            event.ignore()

    def check_system_db(self):
        mysql_path = './mysql'
        mysql_files = [f for f in os.listdir(mysql_path) if os.path.isfile(os.path.join(mysql_path, f))]
        for file in mysql_files:
            table_name = file.split('.sql')[0]
            self.database.check_table_exists(table_name)

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_PY_MEDICAL, self)
        self.ui.tabWidget_window.setTabsClosable(True)

        # self.ui.setWindowFlags(Qt.FramelessWindowHint)  # 無視窗邊框

        self._set_button_enabled()
        self.ui.setWindowTitle('{0} 醫療資訊管理系統'.format(self.system_settings.field('院所名稱')))
        self._set_style()
        self.set_status_bar()

        if self.system_settings.field('顯示側邊欄') == 'Y':
            self.ui.frameSidebar.show()
            self.ui.action_show_side_bar.setChecked(True)
        else:
            self.ui.frameSidebar.hide()
            self.ui.action_show_side_bar.setChecked(False)

    # 設定 status bar
    def set_status_bar(self):
        self.label_station_no = QtWidgets.QLabel()
        self.label_station_no.setFixedWidth(200)
        self.ui.statusbar.addPermanentWidget(self.label_station_no)

        self.label_user_name = QtWidgets.QLabel()
        self.label_user_name.setFixedWidth(200)
        self.ui.statusbar.addPermanentWidget(self.label_user_name)

    # 設定信號
    def _set_signal(self):
        self.socket_server.update_signal.connect(self._refresh_waiting_data)

        self.ui.pushButton_registration.clicked.connect(self._open_subroutine)           # 掛號作業
        self.ui.pushButton_cashier.clicked.connect(self._open_subroutine)                # 批價作業
        self.ui.pushButton_return_card.clicked.connect(self._open_subroutine)            # 健保卡欠還卡
        self.ui.pushButton_debt.clicked.connect(self._open_subroutine)                   # 欠還款作業
        self.ui.pushButton_checkout.clicked.connect(self._open_subroutine)               # 掛號櫃台結帳
        self.ui.pushButton_patient_list.clicked.connect(self._open_subroutine)           # 病患查詢
        self.ui.pushButton_ic_record_upload.clicked.connect(self._open_subroutine)       # 健保IC卡資料上傳

        self.ui.pushButton_waiting_list.clicked.connect(self._open_subroutine)           # 醫師看診作業
        self.ui.pushButton_medical_record_list.clicked.connect(self._open_subroutine)    # 病歷查詢
        self.ui.pushButton_record_statistics.clicked.connect(self._open_subroutine)      # 病歷統計

        self.ui.pushButton_settings.clicked.connect(self.open_settings)                     # 系統設定
        self.ui.pushButton_charge.clicked.connect(self._open_subroutine)                 # 收費設定
        self.ui.pushButton_diagnostic.clicked.connect(self._open_subroutine)             # 診察資料
        self.ui.pushButton_medicine.clicked.connect(self._open_subroutine)               # 處方資料
        self.ui.pushButton_ic_card.clicked.connect(self.open_ic_card)                       # 健保卡讀卡機

        self.ui.pushButton_logout.clicked.connect(self.logout)                              # 登出
        self.ui.pushButton_quit.clicked.connect(self.close)                                 # 離開系統

        self.ui.action_convert.triggered.connect(self.convert)                              # 轉檔作業
        self.ui.action_export_emr_xml.triggered.connect(self.export_emr_xml)                              # 轉檔作業

        self.ui.action_ins_check.triggered.connect(self._open_subroutine)                   # 申報預檢
        self.ui.action_ins_apply.triggered.connect(self._open_subroutine)                   # 申報預檢
        self.ui.action_ins_judge.triggered.connect(self._open_subroutine)                   # 申報預檢

        self.ui.action_registration.triggered.connect(self._open_subroutine)
        self.ui.action_cashier.triggered.connect(self._open_subroutine)
        self.ui.action_return_card.triggered.connect(self._open_subroutine)
        self.ui.action_purchase.triggered.connect(self._open_subroutine)
        self.ui.action_checkout.triggered.connect(self._open_subroutine)
        self.ui.action_patient_list.triggered.connect(self._open_subroutine)
        self.ui.action_ins_record_upload.triggered.connect(self._open_subroutine)

        self.ui.action_waiting_list.triggered.connect(self._open_subroutine)
        self.ui.action_medical_record_list.triggered.connect(self._open_subroutine)
        self.ui.action_medical_record_statistics.triggered.connect(self._open_subroutine)

        self.ui.action_settings.triggered.connect(self.open_settings)
        self.ui.action_charge.triggered.connect(self._open_subroutine)
        self.ui.action_doctor_nurse_table.triggered.connect(self._open_subroutine)
        self.ui.action_users.triggered.connect(self._open_subroutine)
        self.ui.action_diagnostic.triggered.connect(self._open_subroutine)
        self.ui.action_medicine.triggered.connect(self._open_subroutine)
        self.ui.action_ic_card.triggered.connect(self.open_ic_card)
        self.ui.action_show_side_bar.triggered.connect(self.switch_side_bar)

        self.ui.action_certificate_diagnosis.triggered.connect(self._open_subroutine)       # 申請診斷證明書
        self.ui.action_certificate_payment.triggered.connect(self._open_subroutine)         # 申請醫療費用證明書

        self.ui.tabWidget_window.tabCloseRequested.connect(self.close_tab)                  # 關閉分頁
        self.ui.tabWidget_window.currentChanged.connect(self.tab_changed)                   # 切換分頁

    # 設定 css style
    def _set_style(self):
        system_utils.set_css(self, self.system_settings)
        system_utils.set_theme(self.ui, self.system_settings)

    # 候診名單歸零
    def _reset_wait(self):
        today = datetime.datetime.today().strftime('%Y-%m-%d 00:00:00')
        sql = '''
            DELETE FROM wait 
            WHERE
                CaseDate < "{0}"
        '''.format(today)
        self.database.exec_sql(sql)

    # 設定按鈕權限
    def _set_button_enabled(self):
        if self.system_settings.field('使用讀卡機') == 'Y':
            self.ui.pushButton_ic_card.setEnabled(True)
        else:
            self.ui.pushButton_ic_card.setEnabled(False)

    # tab 切換
    def tab_changed(self, i):
        tab_name = self.ui.tabWidget_window.tabText(i)
        tab = self.ui.tabWidget_window.currentWidget()
        if tab_name in ['門診掛號', '醫師看診作業', '批價作業']:
            tab.read_wait()
        elif tab_name == '健保卡欠還卡':
            tab.read_return_card()
        elif tab_name == '欠還款作業':
            tab.read_debt()
        elif tab_name == '預約掛號':
            tab.read_reservation()

    # 按鍵驅動
    def _open_subroutine(self):
        tab_name = self.sender().text()
        if tab_name == '醫師看診作業':
            self._add_tab(tab_name, self.database, self.system_settings, self.statistics_dicts)
        else:
            self._add_tab(tab_name, self.database, self.system_settings)

    # 新增tab
    def _add_tab(self, tab_name, *args):
        if self._tab_exists(tab_name):
            return

        new_tab = module_utils.get_module_name(tab_name)(self, *args)
        self.ui.tabWidget_window.addTab(new_tab, tab_name)
        self.ui.tabWidget_window.setCurrentWidget(new_tab)
        self._set_focus(tab_name, new_tab)

        return new_tab

    # 設定 focus
    @staticmethod
    def _set_focus(widget_name, widget):
        if widget_name == "門診掛號":
            widget.ui.lineEdit_query.setFocus()

        if widget_name in [
            '掛號櫃台結帳',
            '病患查詢',
            '病歷查詢',
            '健保IC卡資料上傳',
            '申報預檢',
            '健保申報',
            '健保抽審',
        ]:
            widget.open_dialog()
        elif widget_name == "醫師看診作業":
            widget.ui.tableWidget_waiting_list.setFocus()
        elif widget_name == "新病患資料":
            widget.ui.lineEdit_name.setFocus()

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
        elif tab_name.find('購買商品') != -1:
            self._set_tab(current_tab.call_from)

    # 關閉分頁
    def _tab_is_closable(self, tab_name, current_tab):
        closable = True

        if tab_name.find('病歷資料') == -1:
            return closable

        if current_tab.call_from == '醫師看診作業' and not current_tab.record_saved:
            current_tab.update_medical_record()

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
                    current_tab.refresh_medical_record()
                elif tab_name == '病患查詢':
                    current_tab.ui.tableWidget_patient_list.setFocus(True)
                    current_tab.refresh_patient_record()
                elif tab_name == '櫃台購藥':
                    current_tab.ui.tableWidget_purchase_list.setFocus(True)
                    # current_tab.read_purchase_today()
                elif tab_name == '門診掛號':
                    current_tab.read_wait()

                return

    # 開啟病歷資料
    def open_medical_record(self, case_key, call_from=None):
        script = '''
            SELECT CaseKey, CaseDate, PatientKey, Name 
            FROM cases 
            WHERE CaseKey = {0}
        '''.format(case_key)

        rows = self.database.select_record(script)
        if len(rows) <= 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無病歷資料',
                '<font color="red"><h3>找不到病歷主鍵{0}的資料, 請重新查詢!</h3></font>'.format(case_key),
                '請至病歷查詢確認此筆資料是否存在.'
            )
            return

        row = rows[0]

        position_list = personnel_utils.get_personnel(self.database, '醫師')
        if (call_from == '醫師看診作業' and
                self.system_settings.field('使用者') not in position_list):
            system_utils.show_message_box(
                QMessageBox.Critical,
                '使用者非醫師',
                '<font color="red"><h3>登入的使用者並非醫師, 無法進行病歷看診作業!</h3></font>',
                '請重新以醫師身份登入系統.'
            )
            return

        tab_name = '{0}-{1}-病歷資料-{2}'.format(
            str(row['PatientKey']),
            str(row['Name']),
            str(row['CaseDate'].date()),
        )
        self._add_tab(tab_name, self.database, self.system_settings, row['CaseKey'], call_from)

    # 開啟病患資料
    def open_patient_record(self, patient_key, call_from=None, ic_card=None):
        if patient_key is None:
            tab_name = '新病患資料'
            self._add_tab(
                tab_name, self.database, self.system_settings, patient_key, call_from, ic_card
            )
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
        self._add_tab(tab_name, self.database, self.system_settings, row['PatientKey'], call_from, None)

    # 預約掛號
    def open_reservation(self, reserve_key):
        tab_name = '預約掛號'
        if self._tab_exists(tab_name):
            current_tab = None
            for i in range(self.ui.tabWidget_window.count()):
                if self.ui.tabWidget_window.tabText(i) == tab_name:
                    current_tab = self.ui.tabWidget_window.widget(i)
                    break

        else:
            current_tab = self._add_tab(tab_name, self.database, self.system_settings, reserve_key)

        if reserve_key is not None:
            current_tab.set_reservation_arrival(reserve_key)

    # 預約掛號
    def open_purchase_tab(self, case_key=None):
        tab_name = '購買商品'
        if self._tab_exists(tab_name):
            current_tab = None
            for i in range(self.ui.tabWidget_window.count()):
                if self.ui.tabWidget_window.tabText(i) == tab_name:
                    current_tab = self.ui.tabWidget_window.widget(i)
                    break
        else:
            self._add_tab(tab_name, self.database, self.system_settings, '櫃台購藥', case_key)

    # 預約掛號
    def registration_arrival(self, reserve_key):
        tab_name = '門診掛號'
        self._add_tab(tab_name, self.database, self.system_settings)

        current_tab = None
        for i in range(self.ui.tabWidget_window.count()):
            if self.ui.tabWidget_window.tabText(i) == tab_name:
                current_tab = self.ui.tabWidget_window.widget(i)
                break

        current_tab.reservation_arrival(reserve_key)

    # 初診掛號
    def set_new_patient(self, new_patient_key):
        current_tab = None
        for i in range(self.ui.tabWidget_window.count()):
            if self.ui.tabWidget_window.tabText(i) == '門診掛號':
                current_tab = self.ui.tabWidget_window.widget(i)
                break

        current_tab.ui.lineEdit_query.setText(str(new_patient_key))
        current_tab.query_patient()

    # 系統設定
    def open_settings(self):
        dialog = dialog_system_settings.DialogSettings(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()
        self.system_settings = system_settings.SystemSettings(self.database)
        self.label_station_no.setText('工作站編號: {0}'.format(self.system_settings.field('工作站編號')))
        self._set_button_enabled()

    # 健保卡讀卡機
    def open_ic_card(self):
        dialog = dialog_ic_card.DialogICCard(self.ui, self.database, self.system_settings)
        if dialog.ic_card is None:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '無法驅動讀卡機',
                '<font size="4" color="red"><b>無法載入健保讀卡機驅動程式, 無法執行健保卡掛號.</b></font>',
                '請確定讀卡機驅動程式是否正確.'
            )
            dialog.deleteLater()
            return

        dialog.exec_()
        dialog.deleteLater()

    # 轉檔
    def convert(self):
        dialog = convert.DialogConvert(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    def export_emr_xml(self):
        dialog = dialog_export_emr_xml.DialogExportEMRXml(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    # 設定權限
    def set_root_permission(self):
        if self.system_settings.field('使用者') != '超級使用者':
            self.action_convert.setEnabled(False)
        else:
            self.action_convert.setEnabled(True)

    # 驅動 udp socket server
    def _start_udp_socket_server(self):
        self.socket_server.start()

    # 重新顯示病歷登錄候診名單
    def _refresh_waiting_data(self, data):
        index = self.ui.tabWidget_window.currentIndex()
        current_tab_text = self.ui.tabWidget_window.tabText(index)
        if current_tab_text in ['醫師看診作業', '批價作業']:
            tab = self.ui.tabWidget_window.currentWidget()
            tab.read_wait()

    # 重新顯示狀態列
    def refresh_status_bar(self):
        self.label_user_name.setText('使用者: {0}'.format(self.system_settings.field('使用者')))
        self.label_station_no.setText('工作站編號: {0}'.format(self.system_settings.field('工作站編號')))

    # 登出
    def logout(self):
        login_dialog = login.Login(self, self.database, self.system_settings)
        login_dialog.exec_()
        if not login_dialog.login_ok:
            return

        user_name = login_dialog.user_name
        self.system_settings.post('使用者', user_name)
        self.refresh_status_bar()
        self.set_root_permission()

        login_dialog.deleteLater()

    def switch_side_bar(self):
        if self.ui.action_show_side_bar.isChecked():
            self.ui.frameSidebar.show()
        else:
            self.ui.frameSidebar.hide()

    def check_ic_card(self):
        if self.system_settings.field('使用讀卡機') == 'N':
            return

        ic_card = cshis.CSHIS(self.database, self.system_settings)
        # ic_card.verify_sam()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    py_medical = PyMedical()
    py_medical.system_settings.post('使用者', None)

    check_db = check_database.CheckDatabase(py_medical, py_medical.database, py_medical.system_settings)
    check_db.check_database()
    del check_db

    login_dialog = login.Login(py_medical, py_medical.database, py_medical.system_settings)
    login_dialog.exec_()
    if not login_dialog.login_ok:
        return

    login_dialog.deleteLater()
    user_name = login_dialog.user_name

    statistics = login_statistics.LoginStatistics(
        py_medical, py_medical.database, py_medical.system_settings)
    statistics.start_statistics()
    py_medical.statistics_dicts = statistics.statistics_dicts
    del statistics

    py_medical.system_settings.post('使用者', user_name)
    py_medical.refresh_status_bar()
    py_medical.set_root_permission()
    py_medical.showMaximized()
    py_medical.check_ic_card()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
