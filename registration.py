#!/usr/bin/env python3
#coding: utf-8

import datetime
import re
import sys
import webbrowser

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

from classes import table_widget
from classes import udp_socket_client
from dialog import dialog_past_history
from dialog import dialog_select_patient
from libs import case_utils
from libs import charge_utils
from libs import cshis_utils
from libs import date_utils
from libs import nhi_utils
from libs import number_utils
from libs import patient_utils
from libs import personnel_utils
from libs import registration_utils
from libs import string_utils
from libs import system_utils
from libs import ui_utils
from libs import validator_utils
from libs import dialog_utils
from printer import print_registration

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 門診掛號 2018.01.22
class Registration(QtWidgets.QMainWindow):
    program_name = '門診掛號'

    # 初始化
    def __init__(self, parent=None, *args):
        super(Registration, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None
        self.dialog_history = dialog_past_history.DialogPastHistory(
            self, self.database, self.system_settings
        )
        self.socket_client = udp_socket_client.UDPSocketClient()
        self.reserve_key = None

        self.user_name = self.system_settings.field('使用者')

        self._set_ui()
        self._set_signal()
        self._set_permission()
        # self.read_wait()   # activate by pymedical.py->tab_changed

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_registration(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_REGISTRATION, self)
        system_utils.set_css(self, self.system_settings)
        ui_utils.set_completer(
            self.database,
            'SELECT Name FROM patient GROUP BY Name ORDER BY Name',
            'Name',
            self.ui.lineEdit_query
        )
        self.table_widget_wait = table_widget.TableWidget(self.ui.tableWidget_wait, self.database)
        self.table_widget_wait.set_column_hidden([0, 1])
        self.table_widget_wait_completed = table_widget.TableWidget(
            self.ui.tableWidget_wait_completed, self.database)
        self.table_widget_wait_completed.set_column_hidden([0, 1])
        self.ui.lineEdit_query.setFocus()
        self._set_reg_mode(True)
        self._set_combobox()
        self._set_table_width()
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.action_ic_card.setEnabled(False)

        self.ui.tabWidget_list.setCurrentIndex(0)

    # 設定信號
    def _set_signal(self):
        self.ui.action_new_patient.triggered.connect(self._new_patient)
        self.ui.action_reservation.triggered.connect(self._reservation)
        self.ui.action_cancel.triggered.connect(self._cancel_registration)
        self.ui.action_ic_card.triggered.connect(self._registration_by_ic_card)
        self.ui.action_save.triggered.connect(self._save_files)
        self.ui.action_save_no_print.triggered.connect(self._save_files)
        self.ui.action_close.triggered.connect(self.close_registration)
        self.ui.action_clear_wait.triggered.connect(self._clear_wait)
        self.ui.action_med_vpn.triggered.connect(self._open_med_vpn)

        self.ui.toolButton_query.clicked.connect(self.query_patient)
        self.ui.toolButton_delete_wait.clicked.connect(self.delete_wait_list)
        self.ui.toolButton_ic_cancel.clicked.connect(self.cancel_ic_card)
        self.ui.toolButton_print_wait.clicked.connect(self.print_wait)
        self.ui.toolButton_print_wait_2.clicked.connect(self.print_wait)
        self.ui.toolButton_modify_patient.clicked.connect(self._modify_patient)
        self.ui.toolButton_modify_patient2.clicked.connect(self._modify_patient)
        self.ui.toolButton_modify_wait.clicked.connect(self._modify_wait)
        self.ui.toolButton_edit_cases.clicked.connect(self._modify_wait)
        self.ui.toolButton_ic_cancel_2.clicked.connect(self.cancel_ic_card)
        self.ui.toolButton_write_ic.clicked.connect(self.write_ic_treatment)
        self.ui.toolButton_rewrite_ic_prescript.clicked.connect(self.rewrite_ic_card)
        self.ui.toolButton_quick_ic_card.clicked.connect(self._quick_write_ic_treatment)

        self.ui.tableWidget_wait.doubleClicked.connect(self._modify_wait)
        self.ui.tableWidget_wait_completed.doubleClicked.connect(self._modify_wait)

        self.ui.lineEdit_query.returnPressed.connect(self.query_patient)
        self.ui.comboBox_patient_share.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_patient_discount.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_ins_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_share_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_injury_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_treat_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_card.currentTextChanged.connect(self._selection_changed)
        self.ui.comboBox_course.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_doctor.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_massager.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_period.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_room.currentIndexChanged.connect(self._selection_changed)
        self.ui.lineEdit_regist_fee.textChanged.connect(self._selection_changed)
        self.ui.lineEdit_diag_share_fee.textChanged.connect(self._selection_changed)
        self.ui.lineEdit_deposit_fee.textChanged.connect(self._selection_changed)
        self.ui.lineEdit_traditional_health_care_fee.textChanged.connect(self._selection_changed)
        self.ui.tabWidget_list.currentChanged.connect(self._waiting_list_tab_changed)    # 切換分頁
        self.ui.tableWidget_wait_completed.itemSelectionChanged.connect(
            self._wait_completed_table_item_changed
        )

    def _set_permission(self):
        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '預約掛號', '執行預約掛號', self.user_name) != 'Y':
            self.ui.action_reservation.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '修正候診名單', self.user_name) != 'Y':
            self.ui.toolButton_modify_wait.setEnabled(False)
            self.ui.toolButton_edit_cases.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '刪除候診名單', self.user_name) != 'Y':
            self.ui.toolButton_delete_wait.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '健保卡退掛', self.user_name) != 'Y':
            self.ui.toolButton_ic_cancel.setEnabled(False)
            self.ui.toolButton_ic_cancel_2.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '健保卡寫卡', self.user_name) != 'Y':
            self.ui.toolButton_write_ic.setEnabled(False)
            self.ui.toolButton_rewrite_ic_prescript.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '病患資料修正', self.user_name) != 'Y':
            self.ui.toolButton_modify_patient.setEnabled(False)
            self.ui.toolButton_modify_patient2.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '補印收據', self.user_name) != 'Y':
            self.ui.toolButton_print_wait.setEnabled(False)
            self.ui.toolButton_print_wait_2.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '初診掛號', self.user_name) != 'Y':
            self.ui.action_new_patient.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '清除非本日候診名單', self.user_name) != 'Y':
            self.ui.action_clear_wait.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '開啟雲端藥歷', self.user_name) != 'Y':
            self.ui.action_med_vpn.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '健保卡掛號', self.user_name) != 'Y':
            self.ui.action_ic_card.setEnabled(False)

        if personnel_utils.get_permission(
                self.database, self.program_name, '人工手動掛號', self.user_name) != 'Y':
            self.ui.groupBox_search_patient.setEnabled(False)

    def _registration_by_ic_card(self):
        ic_card = cshis.CSHIS(self.database, self.system_settings)
        if ic_card.cshis is None:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '無法驅動讀卡機',
                '<font size="4" color="red"><b>無法載入健保讀卡機驅動程式, 無法執行健保卡掛號.</b></font>',
                '請確定讀卡機驅動程式是否正確.'
            )
            return

        if not ic_card.read_basic_data():
            return

        available_date, available_count = ic_card.get_card_status()
        ic_card.basic_data['card_valid_date'] = available_date
        ic_card.basic_data['card_available_count'] = available_count

        # if available_count <= 0:
        #     ic_card.update_hc()

        sql = 'SELECT * FROM patient WHERE ID = "{0}"'.format(ic_card.basic_data['patient_id'])
        row = self.database.select_record(sql)
        if not row:  # 找不到資料
            if self._check_first_visit_reservation(ic_card):
                return

            self._select_new_patient(ic_card)
        else:
            self._get_patient(row[0]['ID'], ic_card)

    # 檢查是否有網路初診預約
    def _check_first_visit_reservation(self, ic_card):
        reservation_exists = False

        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

        sql = '''
            SELECT temp_patient.*, reserve.* FROM temp_patient 
                LEFT JOIN reserve ON temp_patient.TempPatientKey = reserve.PatientKey
            WHERE 
                ReserveDate BETWEEN "{start_date}" AND "{end_date}" AND
                Arrival = "False" AND
                temp_patient.ID = "{patient_id}" AND
                reserve.Source = "網路初診預約"
        '''.format(
            start_date=start_date,
            end_date=end_date,
            patient_id=ic_card.basic_data['patient_id'],
        )
        rows = self.database.select_record(sql)

        if len(rows) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('今日已有初診預約掛號')
            msg_box.setText(
                '''
                <font size="4" color="blue">
                  <b>此人今日已已有網路初診預約掛號, 是否預約報到!<br>
                </font>
                '''
            )
            msg_box.setInformativeText('網路初診預約掛號已存在')
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            arrival = msg_box.exec_()
            if arrival:
                reservation_exists = True
                self._cancel_registration()
                reserve_key = rows[0]['ReserveKey']
                self.parent.open_reservation(reserve_key)

            return reservation_exists

    def _select_new_patient(self, ic_card):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('查無資料')
        msg_box.setText(
            '''
            <font size="5" color="red">
              <b>資料庫內找不到此病患的資料, 是否為初診病患?</b><br><br>
            </font>
            <font size="4" color="black">
              <b>卡片號碼</b>: {0}<br>
              <b>病患姓名</b>: {1}<br>
              <b>身分證號</b>: {2}<br>
              <b>出生日期</b>: {3}<br>
              <b>病患性別</b>: {4}<br>
              <b>發卡日期</b>: {5}<br>
              <b>卡片註記</b>: {6}<br>
              <b>緊急電話</b>: {7}<br>
            </font> 
        '''.format(
                ic_card.basic_data['card_no'],
                ic_card.basic_data['name'],
                ic_card.basic_data['patient_id'],
                ic_card.basic_data['birthday'],
                ic_card.basic_data['gender'],
                ic_card.basic_data['card_date'],
                ic_card.basic_data['cancel_mark'],
                ic_card.basic_data['emg_phone'],
            )
        )
        msg_box.setInformativeText(
            '''
            <font color="blue">
              <b>如果不是初診病患, 請確定此人基本資料的身分證欄位是否正確!</b><br>
            <font>
            <font color="green">
              (請至->病患資料->查詢此人資料->修正身分證資料)
            <font>
            '''
        )
        msg_box.addButton(QPushButton("確定初診病患"), QMessageBox.AcceptRole)  # 0
        msg_box.addButton(QPushButton("確定此人正確"), QMessageBox.AcceptRole)  # 1
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)  # 2
        result = msg_box.exec_()
        if result == 0:
            if not ic_card.read_register_basic_data():
                return

            self.parent.open_patient_record(None, '門診掛號', ic_card)
        elif result == 1:  # 此人正確
            sql = '''
                SELECT PatientKey, ID FROM patient WHERE
                Name = "{0}" AND Birthday = "{1}"
            '''.format(ic_card.basic_data['name'], ic_card.basic_data['birthday'])
            rows = self.database.select_record(sql)
            if len(rows) != 1:
                return

            patient_key = rows[0]['PatientKey']
            sql = '''
                UPDATE patient SET ID = "{0}" WHERE PatientKey = {1}
            '''.format(ic_card.basic_data['patient_id'], patient_key)
            self.database.exec_sql(sql)
            self._get_patient(ic_card.basic_data['patient_id'], ic_card)

    # 初診掛號
    def _new_patient(self):
        self.parent.open_patient_record(None, '門診掛號')

    def _modify_patient(self):
        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            patient_key = self.ui.tableWidget_wait.item(self.ui.tableWidget_wait.currentRow(), 3)
        else:
            patient_key = self.ui.tableWidget_wait_completed.item(
                self.ui.tableWidget_wait_completed.currentRow(), 2
            )

        if patient_key is None:
            return

        patient_key = patient_key.text()
        self.parent.open_patient_record(patient_key, '門診掛號')

    def _set_table_width(self):
        width = [100, 100, 45, 70, 80, 45, 45, 45, 80, 80, 100, 50, 80, 30, 30, 80, 80, 80, 80, 80, 80]
        self.table_widget_wait.set_table_heading_width(width)
        width = [
            100, 100, 70, 90, 45, 50, 80, 100, 50, 65, 30, 30, 50, 60,
            80,
            80, 80, 80, 80, 400,
        ]
        self.table_widget_wait_completed.set_table_heading_width(width)

    def refresh_wait(self):
        if not self.ui.tabWidget_list.isEnabled():
            return

        self.read_wait()

    def read_wait(self):
        sql = '''
            SELECT 
                wait.*, patient.Gender , 
                cases.RegistFee, cases.SDiagShareFee, cases.DepositFee, cases.SMassageFee
            FROM wait
            LEFT JOIN patient ON wait.PatientKey = patient.PatientKey
            LEFT JOIN cases ON wait.CaseKey = cases.CaseKey
            WHERE 
            wait.DoctorDone = "False"
            ORDER BY wait.RegistNo
        '''
        self.table_widget_wait.set_db_data(sql, self._set_wait_data)
        row_count = self.table_widget_wait.row_count()

        if row_count > 0:
            self._set_wait_tool_button(True)
        else:
            self._set_wait_tool_button(False)

    def _set_wait_data(self, row_no, row):
        wait_row = [
            string_utils.xstr(row['WaitKey']),
            string_utils.xstr(row['CaseKey']),
            None,
            row['PatientKey'],
            string_utils.xstr(row['Name']),
            row['RegistNo'],
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['RegistType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Visit']),
            string_utils.xstr(row['Card']),
            row['Continuance'],
            row['Room'],
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['Massager']),
            string_utils.xstr(row['RegistFee']),
            string_utils.xstr(row['SDiagShareFee']),
            string_utils.xstr(row['DepositFee']),
            string_utils.xstr(row['SMassageFee']),
        ]

        in_progress = string_utils.xstr(row['InProgress'])
        case_utils.set_in_progress_icon(self.ui.tableWidget_wait, row_no, 2, in_progress)

        for col_no in range(len(wait_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, wait_row[col_no])
            self.ui.tableWidget_wait.setItem(
                row_no, col_no, item,
            )
            if col_no in [3, 5, 13, 14, 17, 18, 19, 20]:
                self.ui.tableWidget_wait.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [2, 5, 6, 11]:
                self.ui.tableWidget_wait.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            color = None
            if in_progress == 'Y':
                color = 'red'
            elif row['Visit'] == '初診':
                color = 'darkgreen'
            elif row['InsType'] == '自費':
                color = 'blue'

            if color is not None:
                self.ui.tableWidget_wait.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor(color)
                )

    def _set_wait_tool_button(self, enabled):
        self.ui.toolButton_modify_wait.setEnabled(enabled)
        self.ui.toolButton_delete_wait.setEnabled(enabled)
        self.ui.toolButton_ic_cancel.setEnabled(enabled)
        self.ui.toolButton_modify_patient.setEnabled(enabled)
        self.ui.toolButton_print_wait.setEnabled(enabled)
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.toolButton_ic_cancel.setEnabled(False)

        self._set_permission()

    def _set_wait_completed_tool_button(self, enabled):
        self.ui.toolButton_edit_cases.setEnabled(enabled)
        self.ui.toolButton_write_ic.setEnabled(enabled)
        self.ui.toolButton_ic_cancel_2.setEnabled(enabled)
        self.ui.toolButton_modify_patient2.setEnabled(enabled)
        self.ui.toolButton_print_wait_2.setEnabled(enabled)
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.toolButton_write_ic.setEnabled(False)
            self.ui.toolButton_ic_cancel_2.setEnabled(False)

        self._set_permission()

    # 設定掛號模式
    def _set_reg_mode(self, enabled, ic_card=None):
        if ic_card:
            self.ui.groupBox_patient.setTitle(
                '病患資料 - (健保卡有效期限至: {0} 可用次數: {1}次)'.format(
                    ic_card.basic_data['card_valid_date'], ic_card.basic_data['card_available_count'])
            )
        else:
            self.ui.groupBox_patient.setTitle('病患資料')

        self.ui.action_ic_card.setEnabled(enabled)
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.action_ic_card.setEnabled(False)

        self.ui.action_new_patient.setEnabled(enabled)
        self.ui.action_reservation.setEnabled(enabled)
        self.ui.action_cancel.setEnabled(not enabled)
        self.ui.action_save.setEnabled(not enabled)
        self.ui.action_save_no_print.setEnabled(not enabled)

        self.ui.groupBox_search_patient.setEnabled(enabled)
        self.ui.tabWidget_list.setEnabled(enabled)
        self.ui.groupBox_patient.setEnabled(not enabled)
        self.ui.groupBox_registration.setEnabled(not enabled)

        self.ui.comboBox_card_abnormal.setEnabled(False)
        # self.ui.tabWidget_list.setCurrentIndex(0)

        self._clear_group_box_patient()
        self._clear_group_box_registration()

        self._set_permission()

    # 清除病患資料欄位
    def _clear_group_box_patient(self):
        self.ui.lineEdit_patient_key.clear()
        self.ui.lineEdit_name.clear()
        self.ui.lineEdit_id.clear()
        self.ui.lineEdit_birthday.clear()
        self.ui.lineEdit_telephone.clear()
        self.ui.lineEdit_cellphone.clear()
        self.ui.lineEdit_address.clear()
        self.ui.lineEdit_patient_remark.clear()
        self.ui.comboBox_patient_share.setCurrentIndex(0)
        self.ui.comboBox_patient_discount.setCurrentIndex(0)
        self.ui.comboBox_gender.setCurrentIndex(0)
        self.ui.lineEdit_age.setText(None)

    # 清除掛號資料欄位
    def _clear_group_box_registration(self):
        self.ui.comboBox_ins_type.setCurrentIndex(0)
        self.ui.comboBox_reg_type.setCurrentIndex(0)
        self.ui.comboBox_share_type.setCurrentIndex(0)
        self.ui.comboBox_injury_type.setCurrentIndex(0)
        self.ui.comboBox_treat_type.setCurrentIndex(0)
        self.ui.comboBox_card.setCurrentIndex(0)
        self.ui.comboBox_course.setCurrentIndex(0)
        self.ui.comboBox_doctor.setCurrentIndex(0)
        self.ui.comboBox_massager.setCurrentIndex(0)
        self.ui.spinBox_reg_no.setValue(0)
        self.ui.comboBox_room.setCurrentIndex(0)
        self.ui.lineEdit_regist_fee.clear()
        self.ui.lineEdit_diag_share_fee.clear()
        self.ui.lineEdit_deposit_fee.clear()
        self.ui.lineEdit_traditional_health_care_fee.clear()
        self.ui.lineEdit_total_amount.clear()
        self.ui.lineEdit_receipt_fee.clear()
        self.ui.comboBox_remark.setCurrentIndex(0)

    # 設定 comboBox
    def _set_combobox(self):
        ui_utils.set_combo_box(self.ui.comboBox_patient_share, nhi_utils.SHARE_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_patient_discount, '掛號優待', self.database)
        ui_utils.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_visit, nhi_utils.VISIT)
        ui_utils.set_combo_box(self.ui.comboBox_reg_type, nhi_utils.REG_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_share_type, nhi_utils.SHARE_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_treat_type, nhi_utils.TREAT_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_injury_type, nhi_utils.INJURY_TYPE)
        ui_utils.set_combo_box(self.ui.comboBox_card, nhi_utils.CARD)
        ui_utils.set_combo_box(self.ui.comboBox_course, nhi_utils.COURSE, None)
        ui_utils.set_combo_box(self.ui.comboBox_card_abnormal, nhi_utils.ABNORMAL_CARD_WITH_HINT, None)
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)
        ui_utils.set_combo_box(self.ui.comboBox_gender, nhi_utils.GENDER, None)
        ui_utils.set_combo_box(
            self.ui.comboBox_doctor,
            personnel_utils.get_personnel(self.database, '醫師'), None)
        ui_utils.set_combo_box(
            self.ui.comboBox_massager,
            personnel_utils.get_personnel(self.database, '推拿師父'), None)
        self._set_combo_box_remark()

    def _set_combo_box_remark(self):
        sql = '''
            SELECT ClinicName FROM clinic
            WHERE
                ClinicType = "備註"
            ORDER BY LENGTH(ClinicName), CAST(CONVERT(`ClinicName` using big5) AS BINARY)
        '''
        rows = self.database.select_record(sql)
        remark_list = []
        for row in rows:
            remark_list.append(string_utils.xstr(row['ClinicName']))

        ui_utils.set_combo_box(self.ui.comboBox_remark, remark_list, None)

    def _reset_action_button_text(self):
        self.ui.action_save.setText('掛號存檔')
        self.ui.action_save_no_print.setText('掛號存檔不印')
        self.ui.action_cancel.setText('取消掛號')

    # 取消掛號
    def _cancel_registration(self):
        self.reserve_key = None
        self._reset_action_button_text()
        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.ui.lineEdit_query.setFocus()
        self.dialog_history.close()

    # comboBox 內容變更
    def _selection_changed(self, i):
        sender_name = self.sender().objectName()
        if sender_name == 'comboBox_patient_share':
            self.ui.comboBox_share_type.setCurrentText(self.ui.comboBox_patient_share.currentText())
        elif sender_name == 'comboBox_patient_discount':
            self._set_charge()
            self.ui.comboBox_share_type.setCurrentText(self.ui.comboBox_patient_share.currentText())
        elif sender_name == 'comboBox_ins_type':
            if self.ui.comboBox_ins_type.currentText() == '健保':
                self.ui.comboBox_card.setCurrentText('自動取得')
            else:
                self.ui.comboBox_card.setCurrentText('不需取得')

            self._set_charge()
        elif sender_name == 'comboBox_share_type':
            if self.ui.comboBox_share_type.currentText() == '職業傷害':
                if self.ui.comboBox_injury_type.currentText() not in ['職業傷害', '職業病']:
                    self.ui.comboBox_injury_type.setCurrentText('職業傷害')
                card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
                if card != 'IC06':
                    self.ui.comboBox_card.setCurrentText(nhi_utils.INJURY_CARD_DICT['IC06'])
            else:
                if self.ui.comboBox_injury_type.currentText() != '普通疾病':
                    self.ui.comboBox_injury_type.setCurrentText('普通疾病')
                    self.ui.comboBox_card.setCurrentText('自動取得')

            self._set_charge()
        elif sender_name == 'comboBox_injury_type':
            if self.ui.comboBox_injury_type.currentText() in ['職業傷害', '職業病']:
                if self.ui.comboBox_share_type.currentText() != '職業傷害':
                    self.ui.comboBox_share_type.setCurrentText('職業傷害')
                card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
                if card != 'IC06':
                    self.ui.comboBox_card.setCurrentText(nhi_utils.INJURY_CARD_DICT['IC06'])
            else:
                if self.ui.comboBox_share_type.currentText() != self.ui.comboBox_patient_share.currentText():
                    self.ui.comboBox_share_type.setCurrentText(
                        self.ui.comboBox_patient_share.currentText()
                    )
                    self.ui.comboBox_card.setCurrentText('自動取得')

        elif sender_name == 'comboBox_treat_type':
            self._set_charge()
        elif sender_name == 'comboBox_card':
            # if self.ui.comboBox_card.currentText() == '自動取得':
            self.ui.comboBox_course.setCurrentText(None)

            self._set_charge()
        elif sender_name == 'comboBox_course':
            self._set_charge()
            if number_utils.get_integer(self.ui.comboBox_course.currentText()) >= 2:
                self.ui.comboBox_card_abnormal.setEnabled(True)
            else:
                self.ui.comboBox_card_abnormal.setCurrentText(None)
                self.ui.comboBox_card_abnormal.setEnabled(False)

        elif sender_name == 'comboBox_massager':
            self._set_charge()
        elif sender_name == 'comboBox_doctor':
            period = self.ui.comboBox_period.currentText()
            doctor = self.ui.comboBox_doctor.currentText()
            room = registration_utils.get_room(self.database, period, doctor)
            # self.ui.comboBox_room.setCurrentText(string_utils.xstr(room))
        elif (sender_name in ['comboBox_period', 'comboBox_room'] and
              self.ui.action_save.text() == '掛號存檔'):
            period = self.ui.comboBox_period.currentText()
            room = self.ui.comboBox_room.currentText()
            doctor = self.ui.comboBox_doctor.currentText()

            schedule_doctor = registration_utils.get_doctor(self.database, period, room)  # 2019.04.23 新增
            if schedule_doctor != '' and schedule_doctor != doctor:
                self.ui.comboBox_doctor.setCurrentText(schedule_doctor)

            if self.ui.spinBox_reg_no.value() == 0:
                reg_no = registration_utils.get_reg_no(
                    self.database, self.system_settings, room, doctor, period, self.reserve_key,
                )  # 取得診號
                self.ui.spinBox_reg_no.setValue(int(reg_no))
        elif sender_name == 'lineEdit_regist_fee':
            self._set_total_amount()
        elif sender_name == 'lineEdit_diag_share_fee':
            self._set_total_amount()
        elif sender_name == 'lineEdit_deposit_fee':
            self._set_total_amount()
        elif sender_name == 'lineEdit_traditional_health_care_fee':
            self._set_total_amount()

        if 'IC06' in self.ui.comboBox_card.currentText():
            self.ui.comboBox_card_abnormal.setEnabled(True)

    # 開始查詢病患資料
    def query_patient(self):
        keyword = string_utils.xstr(self.ui.lineEdit_query.text())
        if keyword == '':
            return

        pattern = re.compile(validator_utils.DATE_REGEXP)
        if pattern.match(keyword):
            keyword = date_utils.date_to_west_date(keyword)

        self._get_patient(keyword)

    def _get_patient(self, keyword, ic_card=None):
        row = patient_utils.search_patient(self.ui, self.database, self.system_settings, keyword)
        if row is None: # 找不到資料
            dialog = dialog_select_patient.DialogSelectPatient(
                self, self.database, self.system_settings, keyword
            )
            if dialog.table_widget_patient_list.row_count() <= 0:
                system_utils.show_message_box(
                    QMessageBox.Critical,
                    '查無資料',
                    '<font size="4" color="red"><b>找不到有關的病患資料, 請檢查關鍵字是否有誤.</b></font>',
                    '請確定輸入資料的正確性, 生日請輸入YYYY-MM-DD.'
                )
                self.ui.lineEdit_query.setFocus()
                return

            if dialog.exec_():
                patient_key = dialog.get_patient_key()
                self._get_patient(patient_key)

            del dialog
        elif row == -1:  # 取消查詢
            self.ui.lineEdit_query.setFocus()
        else:  # 已選取病患
            self._prepare_registration_data(row, ic_card)

        self.ui.lineEdit_query.clear()

    # 掛號修正
    def _modify_wait(self):
        if (self.user_name != '超級使用者' and
                personnel_utils.get_permission(
                    self.database, self.program_name, '修正候診名單', self.user_name) != 'Y'):
            return

        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            case_key = self.ui.tableWidget_wait.item(self.ui.tableWidget_wait.currentRow(), 1)
        else:
            case_key = self.ui.tableWidget_wait_completed.item(
                self.ui.tableWidget_wait_completed.currentRow(), 1
            )

        if case_key is None:
            return

        case_key = case_key.text()

        self._set_reg_mode(False)
        self.ui.action_save.setText('修正存檔')
        self.ui.action_save_no_print.setText('修正存檔不印')
        self.ui.action_cancel.setText('取消修正')

        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        medical_record = rows[0]
        patient_key = medical_record['PatientKey']
        if patient_key is None:
            return

        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        patient_record = rows[0]
        self._set_patient_data(patient_record)
        self._set_registration_data(patient_key, medical_record)
        self._set_charge(medical_record)

    # 準備掛號
    def _prepare_registration_data(self, row, ic_card=None):
        patient_key = row[0]['PatientKey']
        self._set_reg_mode(False, ic_card)
        self._set_patient_data(row[0])
        self._set_registration_data(patient_key)

        if not self._check_registration_duplicate(patient_key):
            return False

        if self._check_reservation_exists(patient_key):
            return False

        self._registration_precheck(patient_key)
        if self.ui.comboBox_ins_type.currentText() == '健保':  # 健保才自動連續療程
            self._completion_course(patient_key)

            card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
            course = self.ui.comboBox_course.currentText()
            message = registration_utils.check_course_complete_in_days(
                self.database, patient_key, card, course, 30)
            if message is not None:
                system_utils.show_message_box(
                    QMessageBox.Warning,
                    '療程已超過30日',
                    '<font size="4" color="red"><b>{0}</b></font>'.format(message),
                    '即將開啟新的療程.'
                )
                self.ui.comboBox_card.setCurrentText('自動取得')
                self.ui.comboBox_course.setCurrentIndex(0)

        self._set_charge()
        self._show_past_history(patient_key, ic_card)

    # 檢查今日是否有預約
    def _check_reservation_exists(self, patient_key):
        if self.reserve_key is not None:  # 預約報到, 不需檢查
            return

        reservation_exists = False

        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate BETWEEN "{0}" AND "{1}" AND
                Arrival = "False" AND
                PatientKey = {2}
        '''.format(
            start_date, end_date, patient_key
        )

        rows = self.database.select_record(sql)
        if len(rows) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setWindowTitle('今日已有預約掛號')
            msg_box.setText(
                '''
                <font size="4" color="blue">
                  <b>此人今日已已有預約掛號, 是否預約報到!<br>
                </font>
                '''
            )
            msg_box.setInformativeText('預約掛號資料已存在')
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            arrival = msg_box.exec_()
            if arrival:
                reservation_exists = True
                self._cancel_registration()
                reserve_key = rows[0]['ReserveKey']
                self.parent.open_reservation(reserve_key)

        return reservation_exists

    # 自動連續療程 - 30天內
    def _completion_course(self, patient_key):
        today = datetime.date.today()
        last_treat_date = (today - datetime.timedelta(days=30-1)).strftime('%Y-%m-%d 00:00:00')
        # sql = '''
        #     SELECT Continuance FROM cases WHERE
        #     (CaseDate >= "{0}") AND
        #     (PatientKey = {1}) AND
        #     (InsType = "健保") AND
        #     (Continuance = 1)
        #     ORDER BY CaseDate DESC LIMIT 1
        # '''.format(last_treat_date, patient_key)
        # rows = self.database.select_record(sql)
        # if len(rows) <= 0:  # 療程首次已經超過30天
        #     return

        sql = '''
            SELECT TreatType, Card, Continuance, Share, Injury, XCard FROM cases WHERE
            (CaseDate >= "{0}") AND
            (PatientKey = {1}) AND
            (InsType = "健保") 
            ORDER BY CaseDate DESC LIMIT 1
        '''.format(last_treat_date, patient_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]

        # 2019.04.29 上次為內科, 為避免療程中刷卡, 不要自動續療程
        if number_utils.get_integer(row['Continuance']) <= 0:
            return

        if number_utils.get_integer(row['Continuance']) >= 6:  # 療程已滿
            return

        share_type = string_utils.xstr(row['Share'])
        treat_type = string_utils.xstr(row['TreatType'])
        injury_type = string_utils.xstr(row['Injury'])
        card = string_utils.xstr(row['Card'])
        course = string_utils.xstr(row['Continuance'] + 1)  # 療程自動續1次

        self.ui.comboBox_share_type.setCurrentText(share_type)
        self.ui.comboBox_injury_type.setCurrentText(injury_type)
        self.ui.comboBox_treat_type.setCurrentText(treat_type)
        self.ui.comboBox_card.setCurrentText(card)
        self.ui.comboBox_course.setCurrentText(course)

        # xcard = string_utils.xstr(row['XCard'])
        # if xcard in nhi_utils.ABNORMAL_CARD:
        #     xcard = nhi_utils.ABNORMAL_CARD_DICT[xcard]
        #     self.ui.comboBox_card_abnormal.setCurrentText(xcard)

    # 掛號預檢
    def _registration_precheck(self, patient_key):
        if self.ui.comboBox_ins_type.currentText() != '健保':  # 自費不檢查
            return

        warning_message = []

        # 檢查當月健保針傷次數
        message = registration_utils.check_treat_times(
            self.database, self.system_settings, patient_key
        )
        if message is not None:
            warning_message.append(message)

        # 檢查當月健保診察費次數
        message = registration_utils.check_diag_fee_times(
            self.database, self.system_settings, patient_key
        )
        if message is not None:
            warning_message.append(message)

        # 檢查欠卡
        message = registration_utils.check_deposit(self.database, patient_key)
        if message is not None:
            warning_message.append(message)

        # 檢查欠款
        message = registration_utils.check_debt(self.database, patient_key)
        if message is not None:
            warning_message.append(message)

        # 檢查隔日過卡
        message = registration_utils.check_card_yesterday(self.database, patient_key)
        if message is not None:
            warning_message.append(message)

        # 檢查上次健保給藥是否服藥完畢
        message = registration_utils.check_prescription_finished(
            self.database, None, patient_key
        )
        if message is not None:
            warning_message.append(message)

        if len(warning_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Warning,
                '掛號檢查結果提醒',
                '<h4><font color="red">{0}</font></h4>'.format('<br>'.join(warning_message)),
                '請注意! 以上的狀況提示並非資料發生錯誤, 若有疑問, 請至 [病歷查詢] 檢查該筆資料的內容.'
            )

    # 檢查當日重複就診
    def _check_registration_duplicate(self, patient_key):
        if registration_utils.check_record_duplicated(self.database, patient_key, datetime.datetime.now()):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('重複就診')
            msg_box.setText(
                '''
                <font size="4" color="red">
                  <b>此人今日已有門診, 請改掛自費或取消掛號!<br>
                </font>
                '''
            )
            msg_box.setInformativeText("健保規定不可同日重複就診")
            msg_box.addButton(QPushButton("改掛自費"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消掛號"), QMessageBox.NoRole)
            cancel = msg_box.exec_()
            if cancel:
                self._cancel_registration()
                return False

            self.ui.comboBox_ins_type.setCurrentText('自費')

        return True

    # 顯示病患資料
    def _set_patient_data(self, row):
        self.ui.lineEdit_patient_key.setText(str(row['PatientKey']))
        self.ui.lineEdit_name.setText(string_utils.xstr(row['Name']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']).strip(None))
        share_type = nhi_utils.get_share_type(string_utils.xstr(row['InsType']).strip(None))
        self.ui.comboBox_patient_share.setCurrentText(share_type)
        self.ui.comboBox_patient_discount.setCurrentText(string_utils.xstr(row['DiscountType']).strip(None))
        self.ui.comboBox_gender.setCurrentText(string_utils.xstr(row['Gender']).strip(None))
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']).strip(None))
        age_year, age_month = date_utils.get_age(row['Birthday'], datetime.datetime.now())
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)
        self.ui.lineEdit_age.setText(age)
        self.ui.lineEdit_telephone.setText(string_utils.xstr(row['Telephone']))
        self.ui.lineEdit_cellphone.setText(string_utils.xstr(row['Cellphone']))
        self.ui.lineEdit_address.setText(string_utils.xstr(row['Address']).strip(None))
        self.ui.lineEdit_patient_remark.setText(string_utils.get_str(row['Remark'], 'utf8'))
        self._verify_id(self.ui.lineEdit_id.text())
        self.ui.comboBox_card.setFocus()

    # 檢查身分證
    @staticmethod
    def _verify_id(patient_id):
        pattern = re.compile(validator_utils.ID_REGEXP)
        if not pattern.match(patient_id):  # 測試卡
            return

        if not validator_utils.verify_id(patient_id):
            system_utils.show_message_box(
                QMessageBox.Warning,
                '身分證檢查錯誤',
                '<font size="4" color="red"><b>身分證可能有誤，請確認身分證號碼是否輸入正確!</b></font>',
                '如果確定身分證號正確，可以忽略此項警告.'
            )

    # 設定掛號資料
    def _set_registration_data(self, patient_key, medical_record=None):
        if medical_record is None:  # 門診掛號
            reg_type = '一般門診'
            injury_type = '普通疾病'
            treat_type = '內科'
            visit = patient_utils.get_visit(self.database, patient_key)
            card = '自動取得'
            course = None
            xcard = None
            ins_type = self.system_settings.field('預設門診類別')
            share_type = self.ui.comboBox_patient_share.currentText()
            room = self.system_settings.field('診療室')  # 取得預設診療室
            period = registration_utils.get_period(self.system_settings)
            doctor = self._get_doctor_schedule(room, period)  # 醫師要先取得，以便確定是否佔用預約號

            doctor_found = False
            if doctor is None or doctor == '':
                for i in range(1, 20):
                    room = string_utils.xstr(i)
                    doctor = self._get_doctor_schedule(room, period)  # 醫師要先取得，以便確定是否佔用預約號
                    if doctor is not None and doctor != '':
                        doctor_found = True
                        break

            if not doctor_found:
                room = 1

            if self.ui.spinBox_reg_no.value() == 0:
                reg_no = registration_utils.get_reg_no(
                    self.database, self.system_settings, room, doctor, period, self.reserve_key,
                )  # 取得診號  (已在room, doctor, period on changed時取得, 不需要重複再取)
                self.ui.spinBox_reg_no.setValue(reg_no)
            massager = None
            remark = None
        else:  # 掛號修正
            reg_type = medical_record['RegistType']
            injury_type = medical_record['Injury']
            treat_type = medical_record['TreatType']
            visit = medical_record['Visit']
            ins_type = medical_record['InsType']
            share_type = medical_record['Share']
            room = medical_record['Room']

            reg_no = number_utils.get_integer(medical_record['RegistNo'])
            self.ui.spinBox_reg_no.setValue(reg_no)

            period = medical_record['Period']
            card = medical_record['Card']
            course = str(medical_record['Continuance'])
            xcard = string_utils.xstr(medical_record['XCard'])
            if xcard in nhi_utils.ABNORMAL_CARD:
                xcard = nhi_utils.ABNORMAL_CARD_DICT[xcard]
            doctor = self.table_widget_wait.field_value(15)
            if doctor is None:
                doctor = str(medical_record['Doctor'])
            massager = medical_record['Massager']
            remark = string_utils.get_str(medical_record['Remark'], 'utf8')

        self.ui.comboBox_reg_type.setCurrentText(reg_type)
        self.ui.comboBox_injury_type.setCurrentText(injury_type)
        self.ui.comboBox_treat_type.setCurrentText(treat_type)
        self.ui.comboBox_visit.setCurrentText(visit)
        self.ui.comboBox_card.setCurrentText(card)
        self.ui.comboBox_course.setCurrentText(course)
        self.ui.comboBox_card_abnormal.setCurrentText(xcard)
        self.ui.comboBox_ins_type.setCurrentText(ins_type)
        self.ui.comboBox_share_type.setCurrentText(share_type)
        self.ui.comboBox_doctor.setCurrentText(doctor)
        self.ui.comboBox_room.setCurrentText(string_utils.xstr(room))
        self.ui.comboBox_period.setCurrentText(period)
        self.ui.comboBox_massager.setCurrentText(massager)
        self.ui.comboBox_remark.setCurrentText(remark)

    # Monday=0, Tuesday=1...Sunday=6
    def _get_doctor_schedule(self, room, period):
        sql = '''
            SELECT * FROM doctor_schedule
            WHERE
                Room = {room} AND
                Period = "{period}" 
        '''.format(
            room=room,
            period=period,
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return None

        row = rows[0]
        doctor_list = [
            string_utils.xstr(row['Monday']),
            string_utils.xstr(row['Tuesday']),
            string_utils.xstr(row['Wednesday']),
            string_utils.xstr(row['Thursday']),
            string_utils.xstr(row['Friday']),
            string_utils.xstr(row['Saturday']),
            string_utils.xstr(row['Sunday']),
        ]

        today = datetime.datetime.now().weekday()

        return doctor_list[today]

    # 設定收費資料
    def _set_charge(self, medical_record=None):
        if medical_record is None:
            regist_fee = charge_utils.get_regist_fee(
                self.database, self.system_settings,
                self.ui.lineEdit_birthday.text(),
                self.ui.comboBox_patient_discount.currentText(),
                self.ui.comboBox_ins_type.currentText(),
                self.ui.comboBox_share_type.currentText(),
                self.ui.comboBox_treat_type.currentText(),
                self.ui.comboBox_course.currentText(),
            )

            if self.ui.comboBox_ins_type.currentText() == '健保':
                diag_share_fee = charge_utils.get_diag_share_fee(
                    self.database,
                    self.ui.comboBox_share_type.currentText(),
                    self.ui.comboBox_treat_type.currentText(),
                    self.ui.comboBox_course.currentText())
                deposit_fee = charge_utils.get_deposit_fee(
                    self.database,
                    self.ui.comboBox_card.currentText())

                traditional_health_care_fee = charge_utils.get_deposit_fee(
                    self.database,
                    self.ui.comboBox_ins_type.currentText())
            else:
                diag_share_fee = 0
                deposit_fee = 0
                traditional_health_care_fee = 0
        else:
            regist_fee = medical_record['RegistFee']
            diag_share_fee = medical_record['SDiagShareFee']
            deposit_fee = medical_record['DepositFee']
            traditional_health_care_fee = medical_record['SMassageFee']

        self.ui.lineEdit_regist_fee.setText(str(regist_fee))
        self.ui.lineEdit_diag_share_fee.setText(str(diag_share_fee))
        self.ui.lineEdit_deposit_fee.setText(str(deposit_fee))
        self.ui.lineEdit_traditional_health_care_fee.setText(str(traditional_health_care_fee))
        self._set_total_amount()

    # 設定收費總金額
    def _set_total_amount(self):
        try:
            regist_fee = number_utils.get_integer(self.ui.lineEdit_regist_fee.text())
        except ValueError:
            regist_fee = 0

        try:
            diag_share_fee = number_utils.get_integer(self.ui.lineEdit_diag_share_fee.text())
        except ValueError:
            diag_share_fee = 0

        try:
            deposit_fee = number_utils.get_integer(self.ui.lineEdit_deposit_fee.text())
        except ValueError:
            deposit_fee = 0

        try:
            traditional_health_care_fee = number_utils.get_integer(
                self.ui.lineEdit_traditional_health_care_fee.text()
            )
        except ValueError:
            traditional_health_care_fee = 0

        total_amount = regist_fee + diag_share_fee + deposit_fee + traditional_health_care_fee

        self.ui.lineEdit_regist_fee.setText(str(regist_fee))
        self.ui.lineEdit_diag_share_fee.setText(str(diag_share_fee))
        self.ui.lineEdit_deposit_fee.setText(str(deposit_fee))
        self.ui.lineEdit_traditional_health_care_fee.setText(str(traditional_health_care_fee))
        self.ui.lineEdit_total_amount.setText(str(total_amount))
        self.ui.lineEdit_receipt_fee.setText(str(total_amount))

    def _show_past_history(self, patient_key, ic_card=None):
        self.dialog_history.show_past_history(patient_key, ic_card)

    # 刪除候診名單
    def delete_wait_list(self, skip_warning=None):
        if not skip_warning:
            name = self.table_widget_wait.field_value(4)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('刪除掛號資料')
            msg_box.setText(
                "<font size='4' color='red'><b>確定刪除 <font color='blue'>{0}</font> 的掛號資料?</b></font>".format(
                    name
                )
            )
            msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            delete_record = msg_box.exec_()
            if not delete_record:
                return

        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            wait_key = self.table_widget_wait.field_value(0)
            case_key = self.table_widget_wait.field_value(1)
        else:
            wait_key = self.table_widget_wait_completed.field_value(0)
            case_key = self.table_widget_wait_completed.field_value(1)

        self.database.delete_record('wait', 'WaitKey', wait_key)
        self.database.delete_record('deposit', 'CaseKey', case_key)
        self.database.delete_record('debt', 'CaseKey', case_key)
        self.database.delete_record('cases', 'CaseKey', case_key)

        sql = '''
            SELECT PrescriptKey FROM prescript
            WHERE
                CaseKey = {case_key}
        '''.format(case_key=case_key)
        rows = self.database.select_record(sql)
        for row in rows:
            prescript_key = row['PrescriptKey']
            self.database.delete_record('presextend', 'PrescriptKey', prescript_key)

        self.database.delete_record('prescript', 'CaseKey', case_key)

        self.ui.tableWidget_wait.removeRow(self.ui.tableWidget_wait.currentRow())
        if self.ui.tableWidget_wait.rowCount() <= 0:
            self._set_wait_tool_button(False)
        self.socket_client.send_data('刪除掛號資料')

    # IC卡退掛
    def cancel_ic_card(self):
        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            case_key = self.table_widget_wait.field_value(1)
            name = self.table_widget_wait.field_value(4)
        else:
            case_key = self.table_widget_wait_completed.field_value(1)
            name = self.table_widget_wait_completed.field_value(4)

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('健保IC卡退掛')
        msg_box.setText(
            "<font size='4' color='red'><b>確定將<font color='blue'>{0}</font>的IC卡掛號資料退掛?</b></font>".format(
                name
            )
        )
        msg_box.setInformativeText("注意！IC卡退掛後, 將回復原來健保卡序!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        cancel_ic_card = msg_box.exec_()
        if not cancel_ic_card:
            return

        sql = '''
            SELECT Continuance, Security FROM cases WHERE
            CaseKey = {0}
        '''.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無資料',
                '<font size="4" color="red"><b>找不到病歷資料, 無法執行IC卡退掛作業.</b></font>',
                '請確定資料是否存在, 如不存在, 請直接刪除掛號資料.'
            )
            return

        row = rows[0]
        if number_utils.get_integer(row['Continuance']) >= 2:  # 療程不須退掛, 直接刪除
            self.delete_wait_list(True)
            tab_name = self.ui.tabWidget_list.tabText(
                self.ui.tabWidget_list.currentIndex()
            )
            if tab_name == '候診名單':
                self.read_wait()
            else:
                self._read_wait_completed()
            return

        ic_card = cshis.CSHIS(self.database, self.system_settings)
        card_datetime = case_utils.extract_security_xml(row['Security'], '寫卡時間')
        if string_utils.xstr(card_datetime) == '':
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無資料',
                '<font size="4" color="red"><b>找不到健保IC卡讀卡資料, 無法執行IC卡退掛作業.</b></font>',
                '請確定此筆病歷是否成功的讀卡, 如不成功, 請直接刪除掛號資料.'
            )
            return

        nhi_datetime = date_utils.west_datetime_to_nhi_datetime(card_datetime)
        if ic_card.return_seq_number(nhi_datetime):
            self.delete_wait_list(True)

        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            self.read_wait()
        else:
            self._read_wait_completed()

    # 掛號存檔/修正存檔
    def _save_files(self):
        if self.ui.comboBox_doctor.currentText() in [None, '']:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '醫師欄位空白',
                '<font size="4" color="red"><b>尚未選擇門診醫師, 請選擇門診醫師後再存檔.</b></font>',
                '請確定醫師班表是否設定.'
            )
            return

        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]

        if self.ui.action_save.text() == '掛號存檔' and not self._verify_registration_data(card):
            return

        ic_card = self._process_ic_card(card)

        if ic_card is None:  # 不須讀卡
            if card == '自動取得':
                system_utils.show_message_box(
                    QMessageBox.Critical,
                    '卡序有誤',
                    '<font size="4" color="red"><b>讀卡機無法作業, 請選擇異常卡序後再存檔.</b></font>',
                    '讀卡機無法作業.'
                )
                return
            else:
                pass
        elif not ic_card:  # 取得安全簽章失敗
            return

        self._save_patient()
        case_key = self._save_medical_record(ic_card)

        self._save_wait(case_key)
        self._save_deposit(case_key, card)
        self._save_debt(case_key)

        if self.reserve_key is not None:
            self._update_reservation(self.reserve_key)

        self.reserve_key = None
        self.dialog_history.close()
        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.ui.lineEdit_query.setFocus()
        self._reset_action_button_text()
        self.read_wait()

        self.socket_client.send_data('新增掛號資料')

        sender_name = self.sender().objectName()
        if sender_name == 'action_save':
            self.print_registration_form('系統設定', case_key)

    def _update_reservation(self, reserve_key):
        sql = 'UPDATE reserve SET Arrival = "True" WHERE ReserveKey = {0}'.format(
            reserve_key
        )
        self.database.exec_sql(sql)

    # 存檔前檢查
    def _verify_registration_data(self, card):
        if self.ui.comboBox_ins_type.currentText() != '健保':  # 自費不檢查
            return True

        patient_key = self.ui.lineEdit_patient_key.text()
        warning_message = []
        course = self.ui.comboBox_course.currentText()

        # 檢查隔日過卡
        message = registration_utils.check_card_yesterday(
            self.database, patient_key, course)
        if message is not None:
            warning_message.append(message)

        message = registration_utils.check_course_complete_in_days(
            self.database, patient_key, card, course, 14)
        if message is not None:
            warning_message.append(message)

        message = registration_utils.check_course_complete(
            self.database, patient_key, course)
        if message is not None:
            warning_message.append(message)

        if len(warning_message) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('掛號存檔前檢查結果')
            msg_box.setText(
                '<h3>{0}</h3>'.format('\n'.join(warning_message)),
            )
            msg_box.setInformativeText('請詢問主治醫師此病患是否繼續以此方式掛號, 或變更其他方式掛號')
            msg_box.addButton(QPushButton("繼續掛號"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消掛號"), QMessageBox.NoRole)
            cancel = msg_box.exec_()
            if cancel:
                self._cancel_registration()
                return False

        return True

    def _process_ic_card(self, card):
        ic_card = None
        card_abnormal = string_utils.xstr(self.ui.comboBox_card_abnormal.currentText()).split(' ')[0]

        if self.ui.comboBox_ins_type.currentText() != '健保':
            return ic_card

        if self.ui.action_save.text() == '修正存檔' or self.ui.action_save_no_print == '修正存檔不印':
            return ic_card

        if card in ('欠卡', '不需取得') or card in nhi_utils.ABNORMAL_CARD:
            return ic_card

        if card_abnormal in nhi_utils.ABNORMAL_CARD:
            return ic_card

        if (self.system_settings.field('產生安全簽章位置') != '掛號' or
                self.system_settings.field('使用讀卡機') != 'Y'):
            return ic_card

        ic_card = self._write_ic_card(cshis_utils.NORMAL_CARD)

        return ic_card

    def _write_ic_card(self, treat_after_check):
        ic_card = cshis.CSHIS(self.database, self.system_settings)

        available_date, available_count = ic_card.get_card_status()
        if available_count is None:
            return False

        if available_count <= 0:
            ic_card.update_hc(False)

        ic_card_ok = ic_card.write_ic_card(
            '掛號寫卡',
            self.ui.lineEdit_patient_key.text(),
            self.ui.comboBox_course.currentText(),
            treat_after_check
        )

        if ic_card_ok:
            seq_number = string_utils.xstr(ic_card.treat_data['seq_number'])  # 有產生卡號才更新
            if seq_number != '':
                self.ui.comboBox_card.setCurrentText(seq_number)

            return ic_card_ok
        else:
            return False

    # 病患資料存檔
    def _save_patient(self):
        patient_modified = False
        if self.ui.lineEdit_name.isModified() or \
                self.ui.lineEdit_id.isModified() or \
                self.ui.lineEdit_birthday.isModified() or \
                self.ui.lineEdit_telephone.isModified() or \
                self.ui.lineEdit_cellphone.isModified() or \
                self.ui.lineEdit_address.isModified() or \
                self.ui.lineEdit_patient_remark.isModified():
            patient_modified = True

        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.ui.lineEdit_patient_key.text())
        try:
            row = self.database.select_record(sql)[0]
            share_type = nhi_utils.get_share_type(row['InsType'])
            discount = string_utils.xstr(row['DiscountType'])
            gender = string_utils.xstr(row['Gender'])
            if self.ui.comboBox_patient_share.currentText() != share_type:
                patient_modified = True
            if self.ui.comboBox_patient_discount.currentText() != discount:
                patient_modified = True
            if self.ui.comboBox_gender.currentText() != gender:
                patient_modified = True
        except IndexError:
            pass

        if not patient_modified:
            return

        fields = ['Name', 'ID', 'Birthday', 'Telephone', 'Cellphone', 'Address', 'InsType',
                  'DiscountType', 'Gender', 'Remark']
        data = [
            self.ui.lineEdit_name.text(),
            self.ui.lineEdit_id.text(),
            self.ui.lineEdit_birthday.text(),
            self.ui.lineEdit_telephone.text(),
            self.ui.lineEdit_cellphone.text(),
            self.ui.lineEdit_address.text(),
            self.ui.comboBox_patient_share.currentText(),
            self.ui.comboBox_patient_discount.currentText(),
            self.ui.comboBox_gender.currentText(),
            self.ui.lineEdit_patient_remark.text()
        ]
        self.database.update_record('patient', fields, 'PatientKey',
                                    self.ui.lineEdit_patient_key.text(), data)

    # 病歷存檔
    def _save_medical_record(self, ic_card=None):
        if self.ui.action_save.text() == '掛號存檔':
            case_key = self._insert_medical_record(ic_card)
        else:
            case_key = self._update_medical_record()

        return case_key

    # 新增病歷
    def _insert_medical_record(self, ic_card=None):
        fields = [
            'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType', 'Injury',
            'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'XCard', 'Period',
            'Room', 'RegistNo', 'Massager', 'Register',
            'ApplyType', 'PharmacyType',
            'RegistFee', 'DiagShareFee', 'SDiagShareFee', 'DepositFee', 'SMassageFee', 'Security', 'Remark'
        ]

        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database,
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_course.currentText())

        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
        card_abnormal = string_utils.xstr(self.ui.comboBox_card_abnormal.currentText()).split(' ')[0]
        if ic_card is None:
            security = case_utils.create_security_xml()
        else:
            security = ic_card.treat_data_to_xml(ic_card.treat_data)

        upload_type = '1'  # 上傳格式
        if card in nhi_utils.ABNORMAL_CARD or card_abnormal in nhi_utils.ABNORMAL_CARD:
            upload_type = '2'

        treat_after_check = '1'  # 補卡註記
        if card == '欠卡':
            treat_after_check = '2'

        security = case_utils.update_xml_doc(
            security, 'upload_type', upload_type)

        security = case_utils.update_xml_doc(
            security, 'treat_after_check', treat_after_check)

        data = [
            string_utils.xstr(datetime.datetime.now()),
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_injury_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            card,
            number_utils.str_to_int(self.ui.comboBox_course.currentText()),
            card_abnormal,
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_massager.currentText(),
            self.system_settings.field('使用者'),
            '申報',
            '申報' if self.system_settings.field('申報藥事服務費') == 'Y' else '不申報',
            self.ui.lineEdit_regist_fee.text(),
            diag_share_fee,
            self.ui.lineEdit_diag_share_fee.text(),
            self.ui.lineEdit_deposit_fee.text(),
            self.ui.lineEdit_traditional_health_care_fee.text(),
            security,
            self.ui.comboBox_remark.currentText(),
        ]
        case_key = self.database.insert_record('cases', fields, data)

        return case_key

    def _save_wait(self, case_key):
        if self.ui.action_save.text() == '掛號存檔':
            self.insert_wait(case_key)
        else:
            tab_name = self.ui.tabWidget_list.tabText(
                self.ui.tabWidget_list.currentIndex()
            )
            if tab_name == '候診名單':
                wait_key = self._get_wait_key(case_key, self.ui.tableWidget_wait)
            else:
                wait_key = self._get_wait_key(case_key, self.ui.tableWidget_wait_completed)

            if wait_key is None:
                return

            self.update_wait(wait_key)

            if tab_name == '候診名單':
                self.read_wait()
            else:
                self._read_wait_completed()

    @staticmethod
    def _get_wait_key(case_key, table_widget_wait):
        wait_key = None

        for row_no in range(table_widget_wait.rowCount()):
            if table_widget_wait.item(row_no, 1).text() == case_key:
                wait_key = table_widget_wait.item(row_no, 0).text()
                break

        return wait_key

    # 新增候診名單
    def insert_wait(self, case_key):
        fields = ['CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Doctor', 'Massager', 'Remark']
        data = [
            case_key,
            string_utils.xstr(datetime.datetime.now()),
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0],
            number_utils.str_to_int(self.ui.comboBox_course.currentText()),
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_doctor.currentText(),
            self.ui.comboBox_massager.currentText(),
            self.ui.comboBox_remark.currentText(),
        ]
        self.database.insert_record('wait', fields, data)

    def _save_deposit(self, case_key, card):
        if card != '欠卡':
            return

        sql = '''
            SELECT * FROM deposit WHERE
                CaseKey = {0}
        '''.format(case_key)
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            return

        self._insert_deposit(case_key)

    def _save_debt(self, case_key):
        total_amount = number_utils.get_integer(self.ui.lineEdit_total_amount.text())
        receipt_fee = number_utils.get_integer(self.ui.lineEdit_receipt_fee.text())
        if receipt_fee >= total_amount:  # 無欠款
            return

        fields = [
            'CaseKey', 'PatientKey', 'DebtType', 'Name', 'CaseDate', 'Period', 'Doctor', 'Fee'
        ]

        data = [
            case_key,
            self.ui.lineEdit_patient_key.text(),
            '掛號欠款',
            self.ui.lineEdit_name.text(),
            string_utils.xstr(datetime.datetime.now()),
            self.ui.comboBox_period.currentText(),
            None,
            total_amount - receipt_fee,
        ]

        self.database.insert_record('debt', fields, data)

    def _insert_deposit(self, case_key):
        fields = [
            'CaseKey', 'PatientKey', 'Name', 'DepositDate',
            'Register', 'Fee'
        ]

        data = [
            case_key,
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            string_utils.xstr(datetime.datetime.now()),
            self.system_settings.field('使用者'),
            self.ui.lineEdit_deposit_fee.text(),
        ]

        self.database.insert_record('deposit', fields, data)

    # 修正病歷
    def _update_medical_record(self):
        fields = [
            'Name', 'Visit', 'RegistType', 'Injury',
            'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'XCard', 'Period',
            'Room', 'RegistNo', 'Massager', 'Register',
            'ApplyType', 'PharmacyType',
            'RegistFee', 'DiagShareFee', 'SDiagShareFee', 'DepositFee', 'SMassageFee', 'Remark'
        ]

        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database,
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_course.currentText())
        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
        card_abnormal = string_utils.xstr(self.ui.comboBox_card_abnormal.currentText()).split(' ')[0]

        data = [
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_injury_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            card,
            number_utils.str_to_int(self.ui.comboBox_course.currentText()),
            card_abnormal,
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_massager.currentText(),
            self.system_settings.field('使用者'),
            '申報',
            '申報' if self.system_settings.field('申報藥事服務費') == 'Y' else '不申報',
            self.ui.lineEdit_regist_fee.text(),
            diag_share_fee,
            self.ui.lineEdit_diag_share_fee.text(),
            self.ui.lineEdit_deposit_fee.text(),
            self.ui.lineEdit_traditional_health_care_fee.text(),
            self.ui.comboBox_remark.currentText(),
        ]

        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            case_key = self.table_widget_wait.field_value(1)
        else:
            case_key = self.table_widget_wait_completed.field_value(1)

        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

        return case_key

    # 修正候診名單
    def update_wait(self, wait_key):
        fields = ['Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Doctor', 'Massager', 'Remark']

        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
        data = [
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            card,
            number_utils.str_to_int(self.ui.comboBox_course.currentText()),
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_doctor.currentText(),
            self.ui.comboBox_massager.currentText(),
            self.ui.comboBox_remark.currentText()[:100],
        ]
        self.database.update_record('wait', fields, 'WaitKey', wait_key, data)

    # 補印收據
    def print_wait(self):
        tab_name = self.ui.tabWidget_list.tabText(
            self.ui.tabWidget_list.currentIndex()
        )
        if tab_name == '候診名單':
            case_key = self.table_widget_wait.field_value(1)
        else:
            case_key = self.table_widget_wait_completed.field_value(1)

        self.print_registration_form('直接列印', case_key)

    # 列印收據
    def print_registration_form(self, printable, case_key=False):
        if not case_key:
            case_key = self.table_widget_wait.field_value(1)

        print_regist = print_registration.PrintRegistration(
            self, self.database, self.system_settings, case_key, printable)
        print_regist.print()
        del print_regist

    def _reservation(self):
        self.parent.open_reservation(None)

    def reservation_arrival(self, reserve_key):
        self.reserve_key = None
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveKey = {0}
        '''.format(reserve_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        self.reserve_key = reserve_key
        row = rows[0]
        doctor = string_utils.xstr(row['Doctor'])
        period = string_utils.xstr(row['Period'])
        self._get_patient(string_utils.xstr(row['PatientKey']))
        self.ui.comboBox_reg_type.setCurrentText('預約門診')
        self.ui.comboBox_doctor.setCurrentText(doctor)

        room = registration_utils.get_room(self.database, period, doctor)
        self.ui.comboBox_room.setCurrentText(string_utils.xstr(room))

    def _waiting_list_tab_changed(self, i):
        tab_name = self.ui.tabWidget_list.tabText(i)

        if tab_name == '候診名單':
            self.read_wait()
        else:
            self._read_wait_completed()

    def _read_wait_completed(self):
        sql = '''
            SELECT 
                wait.WaitKey, cases.*, patient.Gender 
            FROM wait
                LEFT JOIN patient ON wait.PatientKey = patient.PatientKey
                LEFT JOIN cases ON wait.CaseKey = cases.CaseKey
            WHERE 
                cases.DoctorDone = "True"
            ORDER BY FIELD(cases.Period, "晚班", "午班", "早班"), cases.RegistNo DESC
        '''
        self.table_widget_wait_completed.set_db_data(sql, self._set_wait_completed_data)
        row_count = self.table_widget_wait_completed.row_count()

        if row_count > 0:
            self._set_wait_completed_tool_button(True)
        else:
            self._set_wait_completed_tool_button(False)

        self._wait_completed_table_item_changed()

    def _set_wait_completed_data(self, row_no, row):
        signature = case_utils.extract_security_xml(row['Security'], '醫令時間')
        ins_type = string_utils.xstr(row['InsType'])
        card = string_utils.xstr(row['Card'])
        xcard = string_utils.xstr(row['XCard'])

        if ins_type != '健保' or card in nhi_utils.ABNORMAL_CARD or xcard in nhi_utils.ABNORMAL_CARD:
            ic_wrote = '略'
        elif signature is None:
            ic_wrote = '否'
        else:
            ic_wrote = '是'

        remark = string_utils.get_str(row['Remark'], 'utf8')[:20]
        remark = string_utils.replace_ascii_char(['\n'], remark)
        wait_row = [
            string_utils.xstr(row['WaitKey']),
            string_utils.xstr(row['CaseKey']),
            row['PatientKey'],
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['Gender']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Visit']),
            card,
            row['Continuance'],
            row['Room'],
            row['RegistNo'],
            string_utils.xstr(ic_wrote),
            string_utils.xstr(row['Doctor']),
            number_utils.get_integer(row['RegistFee']),
            number_utils.get_integer(row['SDiagShareFee']),
            number_utils.get_integer(row['DrugShareFee']),
            number_utils.get_integer(row['TotalFee']),
            remark,
        ]

        for col_no in range(len(wait_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, wait_row[col_no])

            self.ui.tableWidget_wait_completed.setItem(
                row_no, col_no, item,
            )
            if col_no in [2, 11, 12, 15, 16, 17, 18]:
                self.ui.tableWidget_wait_completed.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [4, 8, 10, 13]:
                self.ui.tableWidget_wait_completed.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費':
                self.ui.tableWidget_wait_completed.item(
                    row_no, col_no).setForeground(
                    QtGui.QColor('blue')
                )

    def _wait_completed_table_item_changed(self):
        row_no = self.ui.tableWidget_wait_completed.currentRow()
        ic_wrote = self.ui.tableWidget_wait_completed.item(row_no, 13)
        if ic_wrote is not None:
            ic_wrote = ic_wrote.text()

        self.ui.toolButton_write_ic.setEnabled(False)
        self.ui.toolButton_ic_cancel_2.setEnabled(False)
        self.ui.toolButton_rewrite_ic_prescript.setEnabled(False)

        if ic_wrote in ['是', '否']:
            self.ui.toolButton_ic_cancel_2.setEnabled(True)
            self.ui.toolButton_rewrite_ic_prescript.setEnabled(True)

        if ic_wrote == '否':
            self.ui.toolButton_write_ic.setEnabled(True)

        self._set_permission()

    def _quick_write_ic_treatment(self):
        current_row = self.ui.tableWidget_wait_completed.currentRow()
        ic_card = cshis.CSHIS(self.database, self.system_settings)
        if not ic_card.read_basic_data():
            return

        patient_found = False
        for row_no in range(self.ui.tableWidget_wait_completed.rowCount()):
            self.ui.tableWidget_wait_completed.setCurrentCell(row_no, 2)
            ins_type = self.table_widget_wait_completed.field_value(5)
            if ins_type != '健保':
                continue

            patient_key = self.table_widget_wait_completed.field_value(2)
            patient_id = patient_utils.get_patient_id(self.database, patient_key)

            if ic_card.basic_data['patient_id'] == patient_id:
                patient_found = True
                break

        if not patient_found:
            name = ic_card.basic_data['name']
            system_utils.show_message_box(
                QMessageBox.Critical,
                '找不到此人的病歷',
                '''<font size="4" color="red"><b>找不到{name}的病歷, 
                    無法執行健保卡就醫資料寫入作業.</b></font>'''.format(
                   name=name,
                ),
                '請確定插入的健保卡是否正確.'
            )
            self.ui.tableWidget_wait_completed.setCurrentCell(current_row, 2)
            return

        if self.table_widget_wait_completed.field_value(13) == '是':
            name = self.table_widget_wait_completed.field_value(3)
            system_utils.show_message_box(
                QMessageBox.Critical,
                '健保卡病歷已寫入',
                '''<font size="4" color="red"><b>{name}的健保卡病歷已寫入, 
                    不需要再執行健保卡就醫資料寫入作業.</b></font>'''.format(
                    name=name,
                ),
                '請取出健保卡.'
            )
            return

        case_key = self.table_widget_wait_completed.field_value(1)
        card = string_utils.xstr(self.table_widget_wait_completed.field_value(9))

        if card == '':
            self.rewrite_ic_card()
            self._read_wait_completed()
            return

        ic_card.write_ic_medical_record(case_key, cshis_utils.NORMAL_CARD)
        self._read_wait_completed()

    def write_ic_treatment(self):
        msg_box = dialog_utils.get_message_box(
            '寫入健保卡就醫資料', QMessageBox.Question,
            '<h3>確定寫入{0}的健保卡就醫資料?</h3>'.format(self.table_widget_wait_completed.field_value(3)),
            '注意！請插入健保卡!'
        )
        write_ic_card = msg_box.exec_()
        if not write_ic_card:
            return

        case_key = self.table_widget_wait_completed.field_value(1)
        card = string_utils.xstr(self.table_widget_wait_completed.field_value(9))

        if card == '':
            self.rewrite_ic_card()
            self._read_wait_completed()
            return

        ic_card = cshis.CSHIS(self.database, self.system_settings)
        ic_card.write_ic_medical_record(case_key, cshis_utils.NORMAL_CARD)
        self._read_wait_completed()

    def _clear_wait(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('清除候診名單')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>確定清除非今日的候診名單?<br>
            </font>
            '''
        )
        msg_box.setInformativeText("只會清除昨天未看診完畢的候診名單.")
        msg_box.addButton(QPushButton("清除候診名單"), QMessageBox.YesRole)
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        cancel = msg_box.exec_()
        if cancel:
            return

        self.parent.reset_wait()
        self.read_wait()

    def rewrite_ic_card(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('重新寫入健保卡')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>確定要將病歷重新寫入健保卡?<br>
            </font>
            '''
        )
        msg_box.setInformativeText(
            "請注意! 如果要取得新卡序, 請先修正掛號資料, 將原來的卡序清除, 這樣才會產生新的卡序，否則只會重寫診療及醫令資料."
        )
        msg_box.addButton(QPushButton("重新寫入"), QMessageBox.YesRole)
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        cancel = msg_box.exec_()
        if cancel:
            return

        case_key = self.table_widget_wait_completed.field_value(1)
        patient_key = self.table_widget_wait_completed.field_value(2)

        card = string_utils.xstr(self.table_widget_wait_completed.field_value(9))
        course = number_utils.get_integer(self.table_widget_wait_completed.field_value(10))

        if course == 0:
            course = None

        ic_card = cshis.CSHIS(self.database, self.system_settings)
        ic_card_ok = ic_card.write_ic_card(
            '掛號寫卡',
            patient_key,
            course,
            cshis_utils.NORMAL_CARD,
        )
        if not ic_card_ok:
            return

        self.update_cases_by_ic_card(ic_card, case_key, card, course)
        ic_card.write_ic_medical_record(case_key, cshis_utils.NORMAL_CARD)
        self.update_wait_by_ic_card(ic_card, case_key)
        self._read_wait_completed()

    def update_cases_by_ic_card(self, ic_card, case_key, original_card, course):
        if ic_card is None:
            return

        fields = [
            'Card', 'Continuance', 'Security',
        ]
        card = string_utils.xstr(ic_card.treat_data['seq_number'])
        if card == '':
            card = original_card

        security = ic_card.treat_data_to_xml(ic_card.treat_data)

        treat_after_check = '1'  # 1:正常 2:補卡
        security = case_utils.update_xml_doc(
            security, 'treat_after_check', treat_after_check)
        security = case_utils.update_xml_doc(
            security, 'prescript_sign_time', date_utils.now_to_str())
        security = case_utils.update_xml_doc(
            security, 'upload_type', '1')
        data = [
            card,
            course,
            security,
        ]
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

    def update_wait_by_ic_card(self, ic_card, case_key):
        if ic_card is None:
            return

        sql = '''
            UPDATE wait SET Card = "{0}" WHERE CaseKey = {1}
        '''.format(ic_card.treat_data['seq_number'], case_key)
        self.database.exec_sql(sql)

    def _open_med_vpn(self):
        med_vpn_addr = 'https://medcloud.nhi.gov.tw/imme0008/IMME0008S01.aspx'
        webbrowser.open(med_vpn_addr, new=0)  # 0: open in existing tab, 2: new tab
