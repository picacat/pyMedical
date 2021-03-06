#!/usr/bin/env python3
#coding: utf-8

import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

import configparser
import datetime
import os
import urllib

from classes import db
from classes import system_settings
from classes import udp_socket_server
from convert import convert

from libs import ui_utils
from libs import module_utils
from libs import system_utils
from libs import string_utils
from libs import personnel_utils

from dialog import dialog_system_settings
from dialog import dialog_hosts
from dialog import dialog_import_medical_record
from dialog import dialog_ic_card
from dialog import dialog_export_emr_xml
from dialog import dialog_database_repair

import system_update

import check_database
import login
import login_statistics
import backup

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 主程式
class PyMedical(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(PyMedical, self).__init__(parent)
        # QtWidgets.QMainWindow.__init__(database)
        self.args = args
        try:
            config_file = args[0][1]
        except IndexError:
            config_file = None

        if config_file is not None:
            self.config_file = config_file
            config_dict = self._parse_config_file(config_file)
            self.database = db.Database(
                host=config_dict['host'],
                user=config_dict['user'],
                database=config_dict['database'],
                password=config_dict['password'],
                charset=config_dict['charset'],
                buffered=config_dict['buffered'],
            )
        else:
            self.config_file = ui_utils.CONFIG_FILE
            self.database = db.Database()

        if not self.database.connected():
            sys.exit(0)

        self.check_system_db()

        self.system_settings = system_settings.SystemSettings(self.database, self.config_file)
        self.ui = None
        self.statistics_dicts = None

        self._set_ui()
        self._set_socket_server()
        self._set_signal()
        self._start_udp_socket_server()
        self._set_user_name()

        self.reset_wait()

    @staticmethod
    def _parse_config_file(config_file):
        config = configparser.ConfigParser()
        config.read(config_file)

        config_dict = {
            'host': config['db']['host'],
            'user': config['db']['user'],
            'database': config['db']['database'],
            'password': config['db']['password'],
            'charset': config['db']['charset'],
            'buffered': True
        }

        return config_dict

    def _set_user_name(self):
        self.user_name = self.system_settings.field('使用者')

    # 解構
    def __del__(self):
        try:
            self.system_settings.post('使用者', None)
            self.system_settings.post('使用者ip', None)
            self.system_settings.post('登入日期', None)
        finally:
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
            if self.user_name != '超級使用者':
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
        self.setWindowIcon(QtGui.QIcon('./icons/python.ico'))
        self.ui.tabWidget_window.setTabsClosable(True)

        # database.ui.setWindowFlags(Qt.FramelessWindowHint)  # 無視窗邊框

        self._set_images()
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

        self._display_bulletin()
        self._set_plugin()

    def _set_images(self):
        icon_size = 128

        self.ui.label_line_qrcode.setPixmap(QtGui.QPixmap('./images/line_qrcode.jpg'))
        self.ui.label_line_qrcode.setMaximumWidth(icon_size)
        self.ui.label_line_qrcode.setMaximumHeight(icon_size)
        self.ui.label_line_qrcode.setScaledContents(True)

    def _display_bulletin(self):
        self.ui.textBrowser.setStyleSheet('background: transparent;')
        self.ui.textBrowser.setFrameStyle(QtWidgets.QFrame.NoFrame)

        url = 'https://www.dropbox.com/s/w8jwe9b0gffhgt9/bulletin.html?dl=1'
        try:
            u = urllib.request.urlopen(url)
            data = u.read()
            u.close()
        except urllib.error.URLError:
            return

        html_file = 'bulletin.html'
        with open(html_file, "wb") as f:
            f.write(data)

        with open(html_file, 'rt', encoding='utf8') as bulletin_file:
            html_text = bulletin_file.read()

        self.ui.textBrowser.setHtml(html_text)

    def _set_plugin(self):
        visible = False

        if self.system_settings.field('院所名稱') in [
            '黃秀凌中醫診所',
            '明醫中醫診所',
            '林錡宏中醫診所',

        ]:
            visible = True

        self.ui.menu_massage.menuAction().setVisible(visible)

    def _set_socket_server(self):
        self.socket_server = udp_socket_server.UDPSocketServer()
        if not self.socket_server.connected():
            if self.system_settings.field('醫療系統執行個體') == '獨立執行':
                sys.exit(0)
            else:
                self.ui.setWindowTitle('{0} 醫療資訊管理系統  (廣播網路已停用)'.format(
                    self.system_settings.field('院所名稱'))
                )

    # 設定 status bar
    def set_status_bar(self):
        self.label_config_file = QtWidgets.QLabel()
        self.label_config_file.setFixedWidth(250)
        self.ui.statusbar.addPermanentWidget(self.label_config_file)

        self.label_station_no = QtWidgets.QLabel()
        self.label_station_no.setFixedWidth(180)
        self.ui.statusbar.addPermanentWidget(self.label_station_no)

        self.label_ip = QtWidgets.QLabel()
        self.label_ip.setFixedWidth(200)
        self.ui.statusbar.addPermanentWidget(self.label_ip)

        self.label_user_name = QtWidgets.QLabel()
        self.label_user_name.setFixedWidth(200)
        self.ui.statusbar.addPermanentWidget(self.label_user_name)

    # 設定信號
    def _set_signal(self):
        self.socket_server.update_signal.connect(self._refresh_waiting_data)

        self.ui.pushButton_registration.clicked.connect(self._open_subroutine)           # 掛號作業
        self.ui.pushButton_reservation.clicked.connect(lambda: self.open_reservation(None, None, None))  # 預約掛號
        self.ui.pushButton_cashier.clicked.connect(self._open_subroutine)                # 批價作業
        self.ui.pushButton_return_card.clicked.connect(self._open_subroutine)            # 健保卡欠還卡
        self.ui.pushButton_debt.clicked.connect(self._open_subroutine)                   # 欠還款作業
        self.ui.pushButton_checkout.clicked.connect(self._open_subroutine)               # 掛號櫃台結帳
        self.ui.pushButton_patient_list.clicked.connect(self._open_subroutine)           # 病患查詢
        self.ui.pushButton_ic_record_upload.clicked.connect(self._open_subroutine)       # 健保IC卡資料上傳

        self.ui.pushButton_waiting_list.clicked.connect(self._open_subroutine)           # 醫師看診作業
        self.ui.pushButton_medical_record_list.clicked.connect(self._open_subroutine)    # 病歷查詢
        self.ui.pushButton_medical_record_statistics.clicked.connect(self._open_subroutine)      # 病歷統計

        self.ui.pushButton_settings.clicked.connect(self.open_settings)                     # 系統設定
        self.ui.action_hosts.triggered.connect(self.open_hosts_settings)                    # 分院連線設定
        self.ui.action_import_medical_record.triggered.connect(self.open_import_medical_record)  # 分院連線設定
        self.ui.pushButton_charge.clicked.connect(self._open_subroutine)                    # 收費設定
        self.ui.pushButton_diagnostic.clicked.connect(self._open_subroutine)                # 診察資料
        self.ui.pushButton_medicine.clicked.connect(self._open_subroutine)                  # 處方資料
        self.ui.pushButton_ic_card.clicked.connect(self.open_ic_card)                       # 健保卡讀卡機

        self.ui.pushButton_logout.clicked.connect(self.logout)                              # 登出
        self.ui.pushButton_quit.clicked.connect(self.close)                                 # 離開系統

        self.ui.action_convert.triggered.connect(self.convert)                              # 轉檔作業
        self.ui.action_export_emr_xml.triggered.connect(self.export_emr_xml)                              # 轉檔作業

        self.ui.action_ins_check.triggered.connect(self._open_subroutine)                   # 申報檢查
        self.ui.action_ins_apply.triggered.connect(self._open_subroutine)                   # 健保申報
        self.ui.action_ins_judge.triggered.connect(self._open_subroutine)                   # 健保抽審

        self.ui.action_registration.triggered.connect(self._open_subroutine)
        self.ui.action_cashier.triggered.connect(self._open_subroutine)
        self.ui.action_return_card.triggered.connect(self._open_subroutine)
        self.ui.action_purchase.triggered.connect(self._open_subroutine)
        self.ui.action_checkout.triggered.connect(self._open_subroutine)
        self.ui.action_patient_list.triggered.connect(self._open_subroutine)
        self.ui.action_ins_record_upload.triggered.connect(self._open_subroutine)
        self.ui.action_update.triggered.connect(self._update_files)
        self.ui.action_restore_records.triggered.connect(self._open_subroutine)
        self.ui.action_database_repair.triggered.connect(self._database_repair)

        self.ui.action_waiting_list.triggered.connect(self._open_subroutine)
        self.ui.action_medical_record_list.triggered.connect(self._open_subroutine)
        self.ui.action_medical_record_statistics.triggered.connect(self._open_subroutine)
        self.ui.action_examination.triggered.connect(self._open_subroutine)                   # 檢驗報告登錄
        self.ui.action_examination_list.triggered.connect(self._open_subroutine)              # 檢驗報告查詢

        self.ui.action_settings.triggered.connect(self.open_settings)
        self.ui.action_charge.triggered.connect(self._open_subroutine)
        self.ui.action_doctor_schedule.triggered.connect(self._open_subroutine)
        self.ui.action_doctor_nurse_table.triggered.connect(self._open_subroutine)
        self.ui.action_users.triggered.connect(self._open_subroutine)
        self.ui.action_diagnostic.triggered.connect(self._open_subroutine)
        self.ui.action_medicine.triggered.connect(self._open_subroutine)
        self.ui.action_misc.triggered.connect(self._open_subroutine)
        self.ui.action_ins_drug.triggered.connect(self._open_subroutine)

        self.ui.action_statistics_doctor.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_return_rate.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_medicine.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_ins_performance.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_doctor_commission.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_ins_discount.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_multiple_performance.triggered.connect(self._open_subroutine)

        self.ui.action_ic_card.triggered.connect(self.open_ic_card)
        self.ui.action_show_side_bar.triggered.connect(self.switch_side_bar)

        self.ui.action_certificate_diagnosis.triggered.connect(self._open_subroutine)       # 申請診斷證明書
        self.ui.action_certificate_payment.triggered.connect(self._open_subroutine)         # 申請醫療費用證明書

        self.ui.action_massage_registration.triggered.connect(self._open_subroutine)
        self.ui.action_massage_purchase_list.triggered.connect(self._open_subroutine)
        self.ui.action_massage_income.triggered.connect(self._open_subroutine)
        self.ui.action_massage_customer_list.triggered.connect(self._open_subroutine)
        self.ui.action_massage_case_list.triggered.connect(self._open_subroutine)
        self.ui.action_statistics_massage_income.triggered.connect(self._open_subroutine)

        self.ui.action_event_log.triggered.connect(self._open_subroutine)

        self.ui.tabWidget_window.tabCloseRequested.connect(self.close_tab)                  # 關閉分頁
        self.ui.tabWidget_window.currentChanged.connect(self.tab_changed)                   # 切換分頁

    # 設定 css style
    def _set_style(self):
        self.ui.label_system_name.setText(
            '<b>{clinic_name} 醫療資訊管理系統</b>'.format(
                clinic_name=self.system_settings.field('院所名稱'),
            )
        )
        system_utils.set_background_image(self.ui.tab_home, self.system_settings)
        system_utils.set_css(self, self.system_settings)
        system_utils.center_window(self)
        system_utils.set_theme(self.ui, self.system_settings)

    # 候診名單歸零
    def reset_wait(self):
        today = datetime.datetime.today().strftime('%Y-%m-%d 00:00:00')
        # sql = '''
        #     DELETE FROM wait
        #     WHERE
        #         CaseDate < "{0}" AND
        #         DoctorDone = "True" AND
        #         ChargeDone = "True"
        # '''.format(today)
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
        elif tab_name == '檢驗報告登錄':
            self._add_tab(tab_name, self.database, self.system_settings, None, None, None)
        elif tab_name in ['醫療費用證明書', '健保卡欠還卡']:
            self._add_tab(tab_name, self.database, self.system_settings, None)
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
            '檢驗報告查詢',
            '病歷統計',
            '健保IC卡資料上傳',
            '申報檢查',
            '健保申報',
            '健保抽審',
            '醫師統計',
            '回診率統計',
            '用藥統計',
            '健保申報業績',
            '醫師銷售業績統計',
            '健保門診優惠統計',
            '綜合業績報表',

            '養生館櫃台結帳',
            '消費資料查詢',
            '養生館統計',
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
        elif tab_name.find('養生館購買商品') != -1:
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
                    current_tab.read_purchase_today()
                elif tab_name == '養生館購物':
                    current_tab.ui.tableWidget_purchase_list.setFocus(True)
                    current_tab.read_purchase_today()
                elif tab_name == '門診掛號':
                    current_tab.read_wait()
                elif tab_name == '消費資料查詢':
                    current_tab.refresh_massage_case()
                elif tab_name == '養生館櫃台結帳':
                    current_tab.refresh_massage_case()

                return

    # 開啟病歷資料
    def open_examination(self, examination_key):
        if examination_key is None:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無檢驗報告資料',
                '<font color="red"><h3>檢驗檔主鍵遺失, 請重新查詢!</h3></font>',
                '請至檢驗報告查詢確認此筆資料是否存在.'
            )
            return

        sql = '''
            SELECT Name, ExaminationDate FROM examination
            WHERE
                ExaminationKey = {0}
        '''.format(examination_key)
        rows = self.database.select_record(sql)
        name = string_utils.xstr(rows[0]['Name'])
        examination_date = string_utils.xstr(rows[0]['ExaminationDate'])
        tab_name = '檢驗報告-{name}-{examination_date}'.format(
            name=name,
            examination_date=examination_date,
        )
        self._add_tab(tab_name, self.database, self.system_settings, examination_key, None, None)

    # 開啟病歷資料
    def create_certificate_payment(self, auto_create_list):
        tab_name = '自動產生醫療費用證明書-{name}-{start_date}'.format(
            name=auto_create_list[1],
            start_date=auto_create_list[4],
        )
        self._add_tab(tab_name, self.database, self.system_settings, auto_create_list)

    # 開啟病歷資料
    def open_return_card(self, patient_key):
        tab_name = '健保卡欠還卡'
        self._add_tab(tab_name, self.database, self.system_settings, patient_key)

    # 開啟病歷資料
    def open_medical_record(self, case_key, call_from=None):
        if case_key is None:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無病歷資料',
                '<font color="red"><h3>病歷主鍵遺失, 請重新查詢!</h3></font>',
                '請至病歷查詢確認此筆資料是否存在.'
            )
            return

        script = '''
            SELECT 
                CaseKey, CaseDate, PatientKey, Name, InsType 
            FROM cases 
            WHERE 
                CaseKey = {0}
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
        if call_from == '醫師看診作業' and self.user_name not in position_list:
            if personnel_utils.get_permission(
                    self.database, call_from, '非醫師病歷登錄', self.user_name) != 'Y':
                system_utils.show_message_box(
                    QMessageBox.Critical,
                    '使用者非醫師',
                    '<font color="red"><h3>登入的使用者並非醫師, 無法進行病歷看診作業!</h3></font>',
                    '請重新以醫師身份登入系統.'
                )
                return

        tab_name = '{case_key}-{name}-{ins_type}病歷資料-{case_date}'.format(
            case_key=string_utils.xstr(row['CaseKey']),
            name=string_utils.xstr(row['Name']),
            case_date=string_utils.xstr(row['CaseDate'].date()),
            ins_type=string_utils.xstr(row['InsType']),
        )
        self._add_tab(tab_name, self.database, self.system_settings, row['CaseKey'], call_from)

    # 新增自費病歷
    def append_self_medical_record(self, case_key, patient_key, name):
        tab_name = '{patient_key}-{name}-自費病歷資料'.format(
            patient_key=patient_key,
            name=name,
        )
        self._add_tab(tab_name, self.database, self.system_settings, case_key, '新增自費病歷')

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
    def open_reservation(self, reserve_key, patient_key, doctor):
        tab_name = '預約掛號'
        if self._tab_exists(tab_name):
            current_tab = None
            for i in range(self.ui.tabWidget_window.count()):
                if self.ui.tabWidget_window.tabText(i) == tab_name:
                    current_tab = self.ui.tabWidget_window.widget(i)
                    break

        else:
            current_tab = self._add_tab(
                tab_name, self.database, self.system_settings, reserve_key, patient_key, doctor
            )

        if reserve_key is not None:
            current_tab.set_reservation_arrival(reserve_key)

    # 櫃台購藥
    def open_purchase_tab(self):
        tab_name = '購買商品'
        if self._tab_exists(tab_name):
            current_tab = None
            for i in range(self.ui.tabWidget_window.count()):
                if self.ui.tabWidget_window.tabText(i) == tab_name:
                    current_tab = self.ui.tabWidget_window.widget(i)
                    break
        else:
            self._add_tab(tab_name, self.database, self.system_settings, '櫃台購藥')

    # 養生館購物
    def open_massage_purchase_tab(self, call_from, massage_case_key=None):
        tab_name = '養生館購買商品'
        if self._tab_exists(tab_name):
            current_tab = None
            for i in range(self.ui.tabWidget_window.count()):
                if self.ui.tabWidget_window.tabText(i) == tab_name:
                    current_tab = self.ui.tabWidget_window.widget(i)
                    break
        else:
            self._add_tab(tab_name, self.database, self.system_settings, massage_case_key, call_from)

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

        if current_tab is None:
            return

        current_tab.ui.lineEdit_query.setText(str(new_patient_key))
        current_tab.query_patient()

    # 系統設定
    def open_settings(self):
        dialog = dialog_system_settings.DialogSystemSettings(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()
        self.system_settings = system_settings.SystemSettings(self.database, self.config_file)
        self.label_station_no.setText('工作站編號: {0}'.format(self.system_settings.field('工作站編號')))
        self._set_button_enabled()

    # 分院資料設定
    def open_hosts_settings(self):
        dialog = dialog_hosts.DialogHosts(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    # 匯入病歷
    def open_import_medical_record(self):
        dialog = dialog_import_medical_record.DialogImportMedicalRecord(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

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
        if self.user_name != '超級使用者':
            self.action_convert.setEnabled(False)
        else:
            self.action_convert.setEnabled(True)

    # 驅動 udp socket server
    def _start_udp_socket_server(self):
        self.socket_server.start()

    def _authorize_all_permission(self):
        action_list = [
            self.ui.pushButton_registration,
            self.ui.pushButton_reservation,
            self.ui.pushButton_cashier,
            self.ui.pushButton_return_card,
            self.ui.pushButton_settings,
            self.ui.pushButton_debt,
            self.ui.pushButton_checkout,
            self.ui.pushButton_patient_list,
            self.ui.pushButton_waiting_list,
            self.ui.pushButton_ic_record_upload,
            self.ui.pushButton_medical_record_list,
            self.ui.pushButton_medical_record_statistics,
            self.ui.pushButton_charge,
            self.ui.pushButton_diagnostic,
            self.ui.pushButton_medicine,
            self.ui.pushButton_ic_card,

            self.ui.action_registration,
            self.ui.action_cashier,
            self.ui.action_return_card,
            self.ui.action_purchase,
            self.ui.action_checkout,
            self.ui.action_patient_list,
            self.ui.action_ins_record_upload,

            self.ui.action_waiting_list,
            self.ui.action_medical_record_list,
            self.ui.action_medical_record_statistics,

            self.ui.action_settings,
            self.ui.action_charge,
            self.ui.action_diagnostic,
            self.ui.action_medicine,
            self.ui.action_ic_card,

            self.ui.action_doctor_schedule,
            self.ui.action_doctor_nurse_table,
            self.ui.action_users,
            self.ui.action_ins_drug,

            self.ui.action_export_emr_xml,
            self.ui.action_update,
            self.ui.action_restore_records,

            self.ui.action_certificate_diagnosis,
            self.ui.action_certificate_payment,

            self.ui.action_ins_check,
            self.ui.action_ins_apply,
            self.ui.action_ins_judge,

            self.ui.action_statistics_doctor,
            self.ui.action_statistics_return_rate,
            self.ui.action_statistics_medicine,
            self.ui.action_statistics_ins_performance,
            self.ui.action_statistics_doctor_commission,
            self.ui.action_statistics_ins_performance,
            self.ui.action_statistics_multiple_performance,

            self.ui.action_convert,
        ]

        for action in action_list:
            action.setEnabled(True)

    # 設定權限
    def set_permission(self):
        self._authorize_all_permission()
        self._set_user_name()
        if self.user_name == '超級使用者':
            return

        import copy
        person_list = copy.deepcopy(personnel_utils.PERMISSION_LIST)  # 如果不copy, 會影響到 dialog_permission

        for item in person_list:
            if string_utils.xstr(item[1]) == '執行門診掛號':
                item.append([
                    self.ui.pushButton_registration,
                    self.ui.action_registration
                ])
            elif string_utils.xstr(item[1]) == '執行預約掛號':
                item.append(self.ui.pushButton_reservation)
            elif string_utils.xstr(item[1]) == '執行批價作業':
                item.append([
                    self.ui.pushButton_cashier,
                    self.ui.action_cashier,
                ])
            elif string_utils.xstr(item[1]) == '執行健保卡欠還卡':
                item.append([
                    self.ui.pushButton_return_card,
                    self.ui.action_return_card,
                ])
            elif string_utils.xstr(item[1]) == '執行欠還款作業':
                item.append(self.ui.pushButton_debt)
            elif string_utils.xstr(item[1]) == '執行櫃台購藥':
                item.append(self.ui.action_purchase)
            elif string_utils.xstr(item[1]) == '執行掛號櫃台結帳':
                item.append([
                    self.ui.pushButton_checkout,
                    self.ui.action_checkout,
                ])
            elif string_utils.xstr(item[1]) == '執行病患查詢':
                item.append([
                    self.ui.pushButton_patient_list,
                    self.ui.action_patient_list,
                ])
            elif string_utils.xstr(item[1]) == '執行健保IC卡資料上傳':
                item.append([
                    self.ui.pushButton_ic_record_upload,
                    self.ui.action_ins_record_upload,
                ])

            elif string_utils.xstr(item[1]) == '執行醫師看診作業':
                item.append([
                    self.ui.pushButton_waiting_list,
                    self.ui.action_waiting_list,
                ])
            elif string_utils.xstr(item[1]) == '執行病歷查詢':
                item.append([
                    self.ui.pushButton_medical_record_list,
                    self.ui.action_medical_record_list,
                ])
            elif string_utils.xstr(item[1]) == '執行病歷統計':
                item.append([
                    self.ui.pushButton_medical_record_statistics,
                    self.ui.action_medical_record_statistics,
                ])
            elif string_utils.xstr(item[1]) == '執行系統設定':
                item.append([
                    self.ui.pushButton_settings,
                    self.ui.action_settings,
                ])
            elif string_utils.xstr(item[1]) == '執行收費設定':
                item.append([
                    self.ui.pushButton_charge,
                    self.ui.action_charge,
                ])
            elif string_utils.xstr(item[1]) == '執行診察資料':
                item.append([
                    self.ui.pushButton_diagnostic,
                    self.ui.action_diagnostic,
                ])
            elif string_utils.xstr(item[1]) == '執行處方資料':
                item.append([
                    self.ui.pushButton_medicine,
                    self.ui.action_medicine,
                ])
            elif string_utils.xstr(item[1]) == '執行健保卡讀卡機':
                item.append([
                    self.ui.pushButton_ic_card,
                    self.ui.action_ic_card,
                ])
            elif string_utils.xstr(item[1]) == '執行醫師班表':
                item.append(self.ui.action_doctor_schedule)
            elif string_utils.xstr(item[1]) == '執行護士跟診表':
                item.append(self.ui.action_doctor_nurse_table)
            elif string_utils.xstr(item[1]) == '執行使用者管理':
                item.append(self.ui.action_users)
            elif string_utils.xstr(item[1]) == '執行健保藥品':
                item.append(self.ui.action_ins_drug)
            elif string_utils.xstr(item[1]) == '執行匯出電子病歷交換檔':
                item.append(self.ui.action_export_emr_xml)
            elif string_utils.xstr(item[1]) == '執行醫療軟體更新':
                item.append(self.ui.action_update)
            elif string_utils.xstr(item[1]) == '執行資料回復':
                item.append(self.ui.action_restore_records)

            elif string_utils.xstr(item[1]) == '執行診斷證明書':
                item.append(self.ui.action_certificate_diagnosis)
            elif string_utils.xstr(item[1]) == '執行醫療費用證明書':
                item.append(self.ui.action_certificate_payment)

            elif string_utils.xstr(item[1]) == '執行申報檢查':
                item.append(self.ui.action_ins_check)
            elif string_utils.xstr(item[1]) == '執行健保申報':
                item.append(self.ui.action_ins_apply)
            elif string_utils.xstr(item[1]) == '執行健保抽審':
                item.append(self.ui.action_ins_judge)

            elif string_utils.xstr(item[1]) == '執行醫師統計':
                item.append(self.ui.action_statistics_doctor)
            elif string_utils.xstr(item[1]) == '執行回診率統計':
                item.append(self.ui.action_statistics_return_rate)
            elif string_utils.xstr(item[1]) == '執行用藥統計':
                item.append(self.ui.action_statistics_medicine)
            elif string_utils.xstr(item[1]) == '執行健保申報業績':
                item.append(self.ui.action_statistics_ins_performance)
            elif string_utils.xstr(item[1]) == '執行醫師銷售業績統計':
                item.append(self.ui.action_statistics_doctor_commission)
            elif string_utils.xstr(item[1]) == '執行健保門診優惠統計':
                item.append(self.ui.action_statistics_ins_discount)
            elif string_utils.xstr(item[1]) == '執行綜合業績統計':
                item.append(self.ui.action_statistics_multiple_performance)
            else:
                item.append(None)

        for item in person_list:
            action = item[2]
            if action is None:
                continue

            if personnel_utils.get_permission(
                    self.database, string_utils.xstr(item[0]), string_utils.xstr(item[1]), self.user_name) != 'Y':
                if type(action) is list:
                    for act in action:
                        act.setEnabled(False)
                else:
                    action.setEnabled(False)

    # 重新顯示病歷登錄候診名單
    def _refresh_waiting_data(self, data):
        clinic_name = data.split(',')[0]
        if clinic_name != self.system_settings.field('院所名稱'):  # 其他分院呼叫
            return

        index = self.ui.tabWidget_window.currentIndex()
        current_tab_text = self.ui.tabWidget_window.tabText(index)
        if current_tab_text not in ['門診掛號', '醫師看診作業', '批價作業']:
            return

        tab = self.ui.tabWidget_window.currentWidget()
        call_from = data.split(',')[1]

        if call_from in ['門診掛號']:
            if current_tab_text in ['門診掛號']:
                tab.refresh_wait()
            elif current_tab_text in ['醫師看診作業']:
                tab.read_wait()
        elif call_from in ['醫師看診作業']:
            if current_tab_text in ['門診掛號', '批價作業']:
                tab.refresh_wait()
            elif current_tab_text in ['醫師看診作業']:
                tab.read_wait()
        elif call_from in ['批價作業']:
            if current_tab_text in ['批價作業']:
                tab.refresh_wait()
        else:
            pass

    # 重新顯示狀態列
    def refresh_status_bar(self):
        self.label_user_name.setText('使用者: {0}'.format(self.system_settings.field('使用者')))
        self.label_station_no.setText('工作站編號: {0}'.format(self.system_settings.field('工作站編號')))
        self.label_ip.setText('IP: {0}'.format(self.system_settings.field('使用者ip')))
        self.label_config_file.setText('設定檔: {0}'.format(self.config_file))

    # 登出
    def logout(self):
        login_dialog = login.Login(self, self.database, self.system_settings)
        login_dialog.exec_()
        if not login_dialog.login_ok:
            return

        user_name = login_dialog.user_name
        self.system_settings.post('使用者', user_name)
        self._set_user_name()
        self.refresh_status_bar()
        self.set_root_permission()
        self.set_permission()

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
        # ic_card.reset_reader(show_message=False)

    def _update_files(self):
        dialog = system_update.SystemUpdate(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    # 資料庫修復
    def _database_repair(self):
        dialog = dialog_database_repair.DialogDatabaseRepair(self.ui, self.database, self.system_settings)
        dialog.exec_()
        dialog.deleteLater()

    # 重新啟動系統
    def restart_pymedical(self):
        if sys.platform == 'win32':
            os.execv(sys.executable,
                     [sys.executable, os.path.join(sys.path[0], __file__)] + sys.argv[1:])
            # os.execv(sys.executable, [sys.executable, __file__] + sys.argv)
        else:
            os.execv(__file__, sys.argv)


# 主程式
def main():
    # QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_Use96Dpi, True)

    app = QtWidgets.QApplication(sys.argv)

    splash_pix = QtGui.QPixmap('images/login_green.jpg')
    splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
    splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
    splash.setEnabled(False)
    splash.show()
    splash.showMessage(
        "<h1><font color='darkgreen'>系統程式載入中, 請稍後...</font></h1>",
        QtCore.Qt.AlignCenter, QtCore.Qt.black
    )

    py_medical = PyMedical(None, sys.argv)
    check_db = check_database.CheckDatabase(py_medical, py_medical.database, py_medical.system_settings)
    check_db.check_database()
    del check_db
    splash.finish(py_medical)

    current_ip_address = system_utils.get_ip()
    last_ip_address = py_medical.system_settings.field('使用者ip')
    if last_ip_address is not None and current_ip_address != last_ip_address:
        system_utils.show_message_box(
            QMessageBox.Critical,
            '識別編號重複',
            '''
                <font size="4" color="red"><b>
                    已經有IP位置{ip_address}的電腦正在使用相同的識別編號, 請查明是哪一台電腦使用此IP, 並調整識別編號.
                </b></font>
            '''.format(
                ip_address=last_ip_address,
            ),
            '您的IP是{ip_address}, 請至系統設定更正識別編號, 以免使用者名稱重複.'.format(
                ip_address=current_ip_address,
            )
        )

    login_dialog = login.Login(py_medical, py_medical.database, py_medical.system_settings)
    login_dialog.exec_()
    if not login_dialog.login_ok:
        return

    py_medical.system_settings.post('使用者', None)
    py_medical.system_settings.post('使用者ip', None)
    py_medical.system_settings.post('登入日期', None)
    login_dialog.deleteLater()
    user_name = login_dialog.user_name

    statistics = login_statistics.LoginStatistics(
        py_medical, py_medical.database, py_medical.system_settings)
    statistics.start_statistics()
    py_medical.statistics_dicts = statistics.statistics_dicts
    del statistics

    py_medical.system_settings.post('使用者', user_name)
    py_medical.system_settings.post('使用者ip', current_ip_address)
    py_medical.system_settings.post('登入日期', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    py_medical.refresh_status_bar()
    py_medical.set_root_permission()
    py_medical.set_permission()

    py_medical.showMaximized()

    py_medical.check_ic_card()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
