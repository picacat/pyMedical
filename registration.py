#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
import re

from classes import table_widget
from classes import cshis

from libs import ui_utils
from libs import system_utils
from libs import patient_utils
from libs import nhi_utils
from libs import number_utils
from libs import string_utils
from libs import registration_utils
from libs import charge_utils
from libs import date_utils
from libs import validator_utils
from libs import cshis_utils
from libs import case_utils
from libs import personnel_utils

from printer import print_registration
from dialog import dialog_past_history
from classes import udp_socket_client


# 門診掛號 2018.01.22
class Registration(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Registration, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None
        self.dialog_history = dialog_past_history.DialogPastHistory(self, self.database, self.system_settings)
        self.socket_client = udp_socket_client.UDPSocketClient()

        self._set_ui()
        self._set_signal()
        # self.read_wait()   # activate by pymedical.py->tab_changed

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_REGISTRATION, self)
        ui_utils.set_completer(
            self.database,
            'SELECT Name FROM patient GROUP BY Name ORDER BY Name',
            'Name',
            self.ui.lineEdit_query
        )
        self.table_widget_wait = table_widget.TableWidget(self.ui.tableWidget_wait, self.database)
        self.table_widget_wait.set_column_hidden([0, 1])
        self.ui.lineEdit_query.setFocus()
        self._set_reg_mode(True)
        self._set_combobox()
        # self._set_table_width()
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.action_ic_card.setEnabled(False)

    # 設定信號
    def _set_signal(self):
        self.ui.action_new_patient.triggered.connect(self._new_patient)
        self.ui.action_cancel.triggered.connect(self._cancel_registration)
        self.ui.action_ic_card.triggered.connect(self._registration_by_ic_card)
        self.ui.action_save.triggered.connect(self._save_files)
        self.ui.action_close.triggered.connect(self.close_registration)
        self.ui.toolButton_query.clicked.connect(self._query_patient)
        self.ui.toolButton_delete_wait.clicked.connect(self.delete_wait_list)
        self.ui.toolButton_ic_cancel.clicked.connect(self.cancel_ic_card)
        self.ui.toolButton_print_wait.clicked.connect(self.print_registration_form)
        self.ui.toolButton_modify_patient.clicked.connect(self._modify_patient)
        self.ui.toolButton_modify_wait.clicked.connect(self._modify_wait)
        self.ui.lineEdit_query.returnPressed.connect(self._query_patient)
        self.ui.comboBox_patient_share.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_patient_discount.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_ins_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_share_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_treat_type.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_card.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_course.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_massager.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_period.currentIndexChanged.connect(self._selection_changed)
        self.ui.comboBox_room.currentIndexChanged.connect(self._selection_changed)
        self.ui.lineEdit_regist_fee.textChanged.connect(self._selection_changed)
        self.ui.lineEdit_diag_share_fee.textChanged.connect(self._selection_changed)
        self.ui.lineEdit_deposit_fee.textChanged.connect(self._selection_changed)
        self.ui.lineEdit_traditional_health_care_fee.textChanged.connect(self._selection_changed)

    def _registration_by_ic_card(self):
        ic_card = cshis.CSHIS(self.system_settings)
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
        sql = 'SELECT * FROM patient WHERE ID = "{0}"'.format(ic_card.basic_data['patient_id'])
        row = self.database.select_record(sql)
        if not row:  # 找不到資料
            self._select_new_patient(ic_card)
        else:
            self._get_patient(row[0]['ID'], ic_card)

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

    def _modify_patient(self):
        patient_key = self.table_widget_wait.field_value(2)
        self.parent.open_patient_record(patient_key, '門診掛號')

    def _set_table_width(self):
        width = [70, 70, 60, 80, 40, 50, 80, 80, 80, 60, 80, 40, 30, 50, 80]
        self.table_widget_wait.set_table_heading_width(width)

    def read_wait(self):
        sql = '''
            SELECT wait.*, patient.Gender FROM wait
            LEFT JOIN patient ON wait.PatientKey = patient.PatientKey
            WHERE 
            DoctorDone = "False"
            ORDER BY CaseDate, RegistNo
        '''
        self.table_widget_wait.set_db_data(sql, self._set_table_data)
        row_count = self.table_widget_wait.row_count()

        if row_count > 0:
            self._set_tool_button(True)
        else:
            self._set_tool_button(False)

    def _set_table_data(self, rec_no, rec):
        wait_rec = [
            string_utils.xstr(rec['WaitKey']),
            string_utils.xstr(rec['CaseKey']),
            string_utils.xstr(rec['PatientKey']),
            string_utils.xstr(rec['Name']),
            string_utils.xstr(rec['Gender']),
            string_utils.xstr(rec['InsType']),
            string_utils.xstr(rec['RegistType']),
            string_utils.xstr(rec['Share']),
            string_utils.xstr(rec['TreatType']),
            string_utils.xstr(rec['Visit']),
            string_utils.xstr(rec['Card']),
            string_utils.int_to_str(rec['Continuance']).strip('0'),
            string_utils.xstr(rec['Room']),
            string_utils.xstr(rec['RegistNo']),
            string_utils.xstr(rec['Massager']),
        ]

        for column in range(0, self.ui.tableWidget_wait.columnCount()):
            self.ui.tableWidget_wait.setItem(rec_no, column, QtWidgets.QTableWidgetItem(wait_rec[column]))
            if column in [2, 11, 12, 13]:
                self.ui.tableWidget_wait.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [4, 9]:
                self.ui.tableWidget_wait.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            if rec['InsType'] == '自費':
                self.ui.tableWidget_wait.item(rec_no, column).setForeground(QtGui.QColor('blue'))

    def _set_tool_button(self, enabled):
        self.ui.toolButton_modify_wait.setEnabled(enabled)
        self.ui.toolButton_delete_wait.setEnabled(enabled)
        self.ui.toolButton_ic_cancel.setEnabled(enabled)
        self.ui.toolButton_modify_patient.setEnabled(enabled)
        self.ui.toolButton_print_wait.setEnabled(enabled)
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.toolButton_ic_cancel.setEnabled(False)

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
        self.ui.action_new_patient.setEnabled(enabled)
        self.ui.action_reg_reserve.setEnabled(enabled)
        self.ui.action_cancel.setEnabled(not enabled)
        self.ui.action_save.setEnabled(not enabled)

        self.ui.groupBox_search_patient.setEnabled(enabled)
        self.ui.tabWidget_list.setEnabled(enabled)
        self.ui.groupBox_patient.setEnabled(not enabled)
        self.ui.groupBox_registration.setEnabled(not enabled)

        self._clear_group_box_patient()
        self._clear_group_box_registration()

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
        self.ui.lineEdit_regist_fee.clear()
        self.ui.lineEdit_diag_share_fee.clear()
        self.ui.lineEdit_deposit_fee.clear()
        self.ui.lineEdit_traditional_health_care_fee.clear()
        self.ui.lineEdit_total_amount.clear()
        self.ui.comboBox_patient_share.setCurrentIndex(0)
        self.ui.comboBox_patient_discount.setCurrentIndex(0)
        self.ui.comboBox_gender.setCurrentIndex(0)
        self.ui.label_age.setText('年齡')

    # 清除掛號資料欄位
    def _clear_group_box_registration(self):
        self.ui.comboBox_ins_type.setCurrentIndex(0)
        self.ui.comboBox_reg_type.setCurrentIndex(0)
        self.ui.comboBox_share_type.setCurrentIndex(0)
        self.ui.comboBox_injury_type.setCurrentIndex(0)
        self.ui.comboBox_treat_type.setCurrentIndex(0)
        self.ui.comboBox_card.setCurrentIndex(0)
        self.ui.comboBox_course.setCurrentIndex(0)
        self.ui.comboBox_massager.setCurrentIndex(0)
        self.ui.comboBox_room.setCurrentIndex(0)
        self.ui.lineEdit_regist_fee.clear()
        self.ui.lineEdit_diag_share_fee.clear()
        self.ui.lineEdit_deposit_fee.clear()
        self.ui.lineEdit_traditional_health_care_fee.clear()
        self.ui.lineEdit_total_amount.clear()
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
        ui_utils.set_combo_box(self.ui.comboBox_course, nhi_utils.COURSE)
        ui_utils.set_combo_box(self.ui.comboBox_card_abnormal, nhi_utils.ABNORMAL_CARD_WITH_HINT, None)
        ui_utils.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)
        ui_utils.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)
        ui_utils.set_combo_box(self.ui.comboBox_gender, nhi_utils.GENDER)
        ui_utils.set_combo_box(
            self.ui.comboBox_massager,
            personnel_utils.get_personnel(self.database, '推拿師父'), None)

    def _reset_action_button_text(self):
        self.ui.action_save.setText('掛號存檔')
        self.ui.action_cancel.setText('取消掛號')

    # 取消掛號
    def _cancel_registration(self):
        self._reset_action_button_text()
        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.ui.lineEdit_query.setFocus()
        self.dialog_history.close()

    # 掛號存檔/修正存檔
    def _save_files(self):
        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]

        ic_card = self._process_ic_card(card)
        if not ic_card:
            return

        self._save_patient()
        case_key = self._save_medical_record(ic_card)
        self.insert_wait(case_key)
        if card == '欠卡':
            self._insert_deposit(case_key)

        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.read_wait()
        self._reset_action_button_text()
        self.ui.lineEdit_query.setFocus()
        self.dialog_history.close()

        self.socket_client.send_data('新增掛號資料')
        self.print_registration_form(case_key)

    def _process_ic_card(self, card):
        ic_card = None
        ins_type = self.ui.comboBox_ins_type.currentText()

        if ins_type != '健保':
            return ic_card

        if self.system_settings.field('產生安全簽章位置') != '掛號':
            return ic_card

        if self.system_settings.field('使用讀卡機') != 'Y':
            return ic_card

        if card == '欠卡':
            return ic_card

        if card in nhi_utils.ABNORMAL_CARD:
            return ic_card

        ic_card = self._write_ic_card()

        return ic_card

    def _write_ic_card(self):
        ic_card = cshis_utils.write_ic_card(
            '掛號寫卡',
            self.database,
            self.system_settings,
            self.ui.lineEdit_patient_key.text(),
            self.ui.comboBox_course.currentText(),
            cshis_utils.NORMAL_CARD,
        )

        if ic_card:
            self.ui.comboBox_card.setCurrentText(ic_card.treat_data['seq_number'])
            return ic_card
        else:
            return False

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
            self._set_charge()
        elif sender_name == 'comboBox_treat_type':
            self._set_charge()
        elif sender_name == 'comboBox_card':
            self._set_charge()
        elif sender_name == 'comboBox_course':
            self._set_charge()
            if self.ui.comboBox_course.currentText() is None:
                self.ui.comboBox_card_abnormal.setEnabled(False)
            else:
                self.ui.comboBox_card_abnormal.setEnabled(True)
        elif sender_name == 'comboBox_massager':
            self._set_charge()
        elif (sender_name == 'comboBox_period' or sender_name == 'comboBox_room') and \
                self.ui.action_save.text() == '掛號存檔':
            period = self.ui.comboBox_period.currentText()
            room = self.ui.comboBox_room.currentText()
            reg_no = registration_utils.get_reg_no(self.database, self.system_settings, room, period)  # 取得診號
            self.ui.spinBox_reg_no.setValue(int(reg_no))
        elif sender_name == 'lineEdit_regist_fee':
            self._set_total_amount()
        elif sender_name == 'lineEdit_diag_share_fee':
            self._set_total_amount()
        elif sender_name == 'lineEdit_deposit_fee':
            self._set_total_amount()
        elif sender_name == 'lineEdit_traditional_health_care_fee':
            self._set_total_amount()

    # 開始查詢病患資料
    def _query_patient(self):
        keyword = str(self.ui.lineEdit_query.text())
        if keyword == '':
            return

        pattern = re.compile(validator_utils.DATE_REGEXP)
        if pattern.match(keyword):
            keyword = date_utils.date_to_west_date(keyword)

        self._get_patient(keyword)

    def _get_patient(self, keyword, ic_card=None):
        row = patient_utils.search_patient(self.ui, self.database, self.system_settings, keyword)
        if row is None: # 找不到資料
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無資料',
                '<font size="4" color="red"><b>找不到有關的病患資料, 請檢查關鍵字是否有誤.</b></font>',
                '請確定輸入資料的正確性, 生日請輸入YYYY-MM-DD.'
            )
            self.ui.lineEdit_query.setFocus()
        elif row == -1:  # 取消查詢
            self.ui.lineEdit_query.setFocus()
        else:  # 已選取病患
            self._prepare_registration_data(row, ic_card)

        self.ui.lineEdit_query.clear()

    # 掛號修正
    def _modify_wait(self):
        self._set_reg_mode(False)
        self.ui.action_save.setText('修正存檔')
        self.ui.action_cancel.setText('取消修正')
        patient_key = self.table_widget_wait.field_value(2)
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        patient_record = self.database.select_record(sql)[0]

        case_key = self.table_widget_wait.field_value(1)
        sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(case_key)
        medical_record = self.database.select_record(sql)[0]

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

        self._registration_precheck(patient_key)
        self._completion_course(patient_key)
        self._set_charge()
        self._show_past_history(patient_key)

    # 自動連續療程
    def _completion_course(self, patient_key):
        today = datetime.date.today()
        last_treat_date = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
        sql = '''
            SELECT Card, Continuance FROM cases WHERE
            (CaseDate >= "{0}") AND
            (PatientKey = {1}) AND
            (InsType = "健保") AND
            (Continuance >= 1) 
            ORDER BY CaseDate DESC LIMIT 1
        '''.format(last_treat_date, patient_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        if row['Continuance'] >= 6:  # 療程已滿
            return

        course = str(row['Continuance'] + 1)  # 療程自動續1次
        self.ui.comboBox_card.setCurrentText(row['Card'])
        self.ui.comboBox_course.setCurrentText(course)

    # 掛號預檢
    def _registration_precheck(self, patient_key):
        warning_message = []

        # 檢查當月健保針傷次數
        message = registration_utils.check_treat_times(self.database, self.system_settings, patient_key)
        if message is not None:
            warning_message.append(message)

        # 檢查當月健保診察費次數
        message = registration_utils.check_diag_fee_times(self.database, self.system_settings, patient_key)
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
        message = registration_utils.check_prescription_finished(self.database, patient_key)
        if message is not None:
            warning_message.append(message)

        if len(warning_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Warning,
                '掛號檢查結果提醒',
                '<h4>{0}</h4>'.format('\n'.join(warning_message)),
                '請注意! 以上的狀況提示並非資料產生錯誤, 若有疑問, 請至 [病歷查詢] 檢查該筆資料的內容.'
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
        self.ui.label_age.setText(age)
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
            ins_type = self.system_settings.field('預設門診類別')
            share_type = self.ui.comboBox_patient_share.currentText()
            room = self.system_settings.field('診療室')  # 取得預設診療室
            reg_no = registration_utils.get_reg_no(self.database, self.system_settings, room)  # 取得診號
            period = registration_utils.get_period(self.system_settings)
            massager = None
            remark = None
        else:  # 掛號修正
            reg_type = medical_record['RegistType']
            injury_type = medical_record['Injury']
            treat_type = medical_record['TreatType']
            visit = medical_record['Visit']
            ins_type = medical_record['InsType']
            share_type = medical_record['Share']
            room = str(medical_record['Room'])
            reg_no = medical_record['RegistNo']
            period = medical_record['Period']
            card = medical_record['Card']
            course = str(medical_record['Continuance'])
            massager = medical_record['Massager']
            remark = string_utils.get_str(medical_record['Remark'], 'utf8')

        self.ui.comboBox_reg_type.setCurrentText(reg_type)
        self.ui.comboBox_injury_type.setCurrentText(injury_type)
        self.ui.comboBox_treat_type.setCurrentText(treat_type)
        self.ui.comboBox_visit.setCurrentText(visit)
        self.ui.comboBox_card.setCurrentText(card)
        self.ui.comboBox_course.setCurrentText(course)
        self.ui.comboBox_ins_type.setCurrentText(ins_type)
        self.ui.comboBox_share_type.setCurrentText(share_type)
        self.ui.comboBox_room.setCurrentText(room)
        self.ui.spinBox_reg_no.setValue(reg_no)
        self.ui.comboBox_period.setCurrentText(period)
        self.ui.comboBox_massager.setCurrentText(massager)
        self.ui.comboBox_remark.setCurrentText(remark)

    # 設定收費資料
    def _set_charge(self, medical_record=None):
        if medical_record is None:
            regist_fee = charge_utils.get_regist_fee(
                self.database,
                self.ui.comboBox_patient_discount.currentText(),
                self.ui.comboBox_ins_type.currentText(),
                self.ui.comboBox_share_type.currentText(),
                self.ui.comboBox_treat_type.currentText(),
                self.ui.comboBox_course.currentText(),
            )
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
        regist_fee = number_utils.get_integer(self.ui.lineEdit_regist_fee.text())
        diag_share_fee = number_utils.get_integer(self.ui.lineEdit_diag_share_fee.text())
        deposit_fee = number_utils.get_integer(self.ui.lineEdit_deposit_fee.text())
        traditional_health_care_fee = number_utils.get_integer(self.ui.lineEdit_traditional_health_care_fee.text())
        total_amount = regist_fee + diag_share_fee + deposit_fee + traditional_health_care_fee

        self.ui.lineEdit_regist_fee.setText(str(regist_fee))
        self.ui.lineEdit_diag_share_fee.setText(str(diag_share_fee))
        self.ui.lineEdit_deposit_fee.setText(str(deposit_fee))
        self.ui.lineEdit_traditional_health_care_fee.setText(str(traditional_health_care_fee))
        self.ui.lineEdit_total_amount.setText(str(total_amount))

    def _show_past_history(self, patient_key):
        self.dialog_history.show_past_history(patient_key)

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
        fields = ['CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType', 'Injury',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'XCard', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Register',
                  'ApplyType', 'PharmacyType',
                  'RegistFee', 'DiagShareFee', 'SDiagShareFee', 'DepositFee', 'SMassageFee', 'Security', 'Remark']

        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database,
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_course.currentText())

        card = string_utils.xstr(self.ui.comboBox_card.currentText()).split(' ')[0]
        card_abnormal = string_utils.xstr(self.ui.comboBox_card_abnormal.currentText()).split(' ')[0]
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
            ic_card.treat_data_to_xml() if ic_card else None,
            self.ui.comboBox_remark.currentText(),
        ]
        case_key = self.database.insert_record('cases', fields, data)

        return case_key

    # 新增候診名單
    def insert_wait(self, case_key):
        fields = ['CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Remark']
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
            self.ui.comboBox_massager.currentText(),
            self.ui.comboBox_remark.currentText(),
        ]
        self.database.insert_record('wait', fields, data)

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
        fields = ['Name', 'Visit', 'RegistType', 'Injury',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period', 'XCard',
                  'Room', 'RegistNo', 'Massager', 'Register',
                  'ApplyType', 'PharmacyType',
                  'RegistFee', 'DiagShareFee', 'SDiagShareFee', 'DepositFee', 'SMassageFee', 'Remark']
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
        case_key = self.table_widget_wait.field_value(1)
        wait_key = self.table_widget_wait.field_value(0)
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)
        self.update_wait(wait_key)

        return case_key

    # 修正候診名單
    def update_wait(self, wait_key):
        fields = ['Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Remark']
        data = [
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_card.currentText(),
            number_utils.str_to_int(self.ui.comboBox_course.currentText()),
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_massager.currentText(),
            self.ui.comboBox_remark.currentText()[:100],
        ]
        self.database.update_record('wait', fields, 'WaitKey', wait_key, data)

    # 刪除候診名單
    def delete_wait_list(self, skip_warning=None):
        if not skip_warning:
            name = self.table_widget_wait.field_value(3)
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('刪除掛號資料')
            msg_box.setText("<font size='4' color='red'><b>確定刪除 <font color='blue'>{0}</font> 的掛號資料?</b></font>"
                            .format(name))
            msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            delete_record = msg_box.exec_()
            if not delete_record:
                return

        wait_key = self.table_widget_wait.field_value(0)
        case_key = self.table_widget_wait.field_value(1)

        self.database.delete_record('wait', 'WaitKey', wait_key)
        self.database.delete_record('deposit', 'CaseKey', case_key)
        self.database.delete_record('debt', 'CaseKey', case_key)
        self.database.delete_record('cases', 'CaseKey', case_key)
        self.database.delete_record('prescript', 'CaseKey', case_key)
        self.ui.tableWidget_wait.removeRow(self.ui.tableWidget_wait.currentRow())
        if self.ui.tableWidget_wait.rowCount() <= 0:
            self._set_tool_button(False)
        self.socket_client.send_data('刪除掛號資料')

    # IC卡退掛
    def cancel_ic_card(self):
        name = self.table_widget_wait.field_value(3)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('健保IC卡退掛')
        msg_box.setText("<font size='4' color='red'><b>確定將<font color='blue'>{0}</font>的IC卡掛號資料退掛?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！IC卡退掛後, 將回復原來健保卡序!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        cancel_ic_card = msg_box.exec_()
        if not cancel_ic_card:
            return

        case_key = self.table_widget_wait.field_value(1)
        sql = '''
            SELECT Security FROM cases WHERE
            CaseKey = {0}
        '''.format(case_key)
        row = self.database.select_record(sql)[0]
        if len(row) <= 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無資料',
                '<font size="4" color="red"><b>找不到病歷資料, 無法執行IC卡退掛作業.</b></font>',
                '請確定資料是否存在, 如不存在, 請直接刪除掛號資料.'
            )
            return

        ic_card = cshis.CSHIS(self.system_settings)
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

    # 初診掛號
    def _new_patient(self):
        self.parent.open_patient_record(None, '門診掛號')

    # 補印收據
    def print_registration_form(self, case_key=False):
        if not case_key:
            case_key = self.table_widget_wait.field_value(1)

        print_regist = print_registration.PrintRegistration(
            self, self.database, self.system_settings, case_key)
        print_regist.print()
        del print_regist

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_registration(self):
        self.close_all()
        self.close_tab()
