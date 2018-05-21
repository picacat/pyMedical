#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
import re
import sys

from classes import table_widget
from classes import cshis

from libs import ui_settings
from libs import patient_utils
from libs import nhi_utils
from libs import number
from libs import strings
from libs import register_utils
from libs import charge_utils
from libs import date_utils
from libs import validator_utils

import print_registration
from dialog import dialog_past_history


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
        self.ui = ui_settings.load_ui_file(ui_settings.UI_REGISTRATION, self)
        ui_settings.set_completer(self.database,
                                  'SELECT Name FROM patient GROUP BY Name ORDER BY Name',
                                  'Name',
                                  self.ui.lineEdit_query)
        self.table_widget_wait = table_widget.TableWidget(self.ui.tableWidget_wait, self.database)
        self.table_widget_wait.set_column_hidden([0, 1])
        self.ui.lineEdit_query.setFocus()
        self._set_reg_mode(True)
        self._set_combobox()
        if self.system_settings.field('使用讀卡機') == 'N':
            self.ui.action_ic_card.setEnabled(False)
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_new_patient.triggered.connect(self._new_patient)
        self.ui.action_cancel.triggered.connect(self.action_cancel_triggered)
        self.ui.action_ic_card.triggered.connect(self.regist_by_ic_card)
        self.ui.action_save.triggered.connect(self.action_save_triggered)
        self.ui.action_close.triggered.connect(self.close_registration)
        self.ui.toolButton_query.clicked.connect(self.query_clicked)
        self.ui.toolButton_delete_wait.clicked.connect(self.delete_wait_clicked)
        self.ui.toolButton_print_wait.clicked.connect(self.print_wait_clicked)
        self.ui.toolButton_modify_patient.clicked.connect(self.modify_patient)
        self.ui.toolButton_modify_wait.clicked.connect(self.modify_wait)
        self.ui.lineEdit_query.returnPressed.connect(self.query_clicked)
        self.ui.comboBox_patient_share.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_patient_discount.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_ins_type.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_share_type.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_treat_type.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_card.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_course.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_massager.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_period.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_room.currentIndexChanged.connect(self.selection_changed)
        self.ui.lineEdit_regist_fee.textChanged.connect(self.selection_changed)
        self.ui.lineEdit_diag_share_fee.textChanged.connect(self.selection_changed)
        self.ui.lineEdit_deposit_fee.textChanged.connect(self.selection_changed)
        self.ui.lineEdit_traditional_health_care_fee.textChanged.connect(self.selection_changed)

    def regist_by_ic_card(self):
        ic_card = cshis.CSHIS(self.system_settings)
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
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)  # 0
        msg_box.addButton(QPushButton("確定初診病患"), QMessageBox.AcceptRole)  # 1
        new_patient = msg_box.exec_()
        if new_patient:
            if not ic_card.read_register_basic_data():
                return

            self.parent.open_patient_record(None, '門診掛號', ic_card)

    def modify_patient(self):
        patient_key = self.table_widget_wait.field_value(2)
        self.parent.open_patient_record(patient_key, '門診掛號')

    def _set_table_width(self):
        width = [70, 70, 60, 80, 40, 50, 80, 80, 80, 60, 80, 40, 30, 50, 80]
        self.table_widget_wait.set_table_heading_width(width)

    def read_wait(self):
        sql = ('SELECT wait.*, patient.Gender FROM wait '
               'LEFT JOIN patient ON wait.PatientKey = patient.PatientKey '
               ' WHERE '
               'DoctorDone = "False" '
               'ORDER BY CaseDate, RegistNo')
        self.table_widget_wait.set_db_data(sql, self._set_table_data)
        row_count = self.table_widget_wait.row_count()

        if row_count > 0:
            self._set_tool_button(True)
        else:
            self._set_tool_button(False)

    def _set_table_data(self, rec_no, rec):
        wait_rec = [
            str(rec['WaitKey']),
            str(rec['CaseKey']),
            str(rec['PatientKey']),
            str(rec['Name']),
            str(rec['Gender']),
            str(rec['InsType']),
            str(rec['RegistType']),
            str(rec['Share']),
            str(rec['TreatType']),
            str(rec['Visit']),
            str(rec['Card']),
            strings.int_to_str(rec['Continuance']).strip('0'),
            str(rec['Room']),
            str(rec['RegistNo']),
            str(rec['Massager']),
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
        ui_settings.set_combo_box(self.ui.comboBox_patient_share, nhi_utils.SHARE_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_patient_discount, '掛號優待', self.database)
        ui_settings.set_combo_box(self.ui.comboBox_ins_type, nhi_utils.INS_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_visit, nhi_utils.VISIT)
        ui_settings.set_combo_box(self.ui.comboBox_reg_type, nhi_utils.REG_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_share_type, nhi_utils.SHARE_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_treat_type, nhi_utils.TREAT_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_injury_type, nhi_utils.INJURY_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_card, nhi_utils.CARD)
        ui_settings.set_combo_box(self.ui.comboBox_course, nhi_utils.COURSE)
        ui_settings.set_combo_box(self.ui.comboBox_period, nhi_utils.PERIOD)
        ui_settings.set_combo_box(self.ui.comboBox_room, nhi_utils.ROOM)
        ui_settings.set_combo_box(self.ui.comboBox_gender, nhi_utils.GENDER)

    def _reset_action_button_text(self):
        self.ui.action_save.setText('掛號存檔')
        self.ui.action_cancel.setText('取消掛號')

    # 取消掛號
    def action_cancel_triggered(self):
        self.dialog_history.close()
        self._reset_action_button_text()
        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.ui.lineEdit_query.setFocus()

    # 存檔
    def action_save_triggered(self):
        ic_card = None
        if self.system_settings.field('使用讀卡機') == 'Y' and self.ui.comboBox_card.currentText() == '自動取得':
            ic_card = self._write_ic_card()
            if not ic_card:
                return

        self.dialog_history.close()
        self._save_files(ic_card)
        self._set_reg_mode(True)

        self.ui.groupBox_search_patient.setEnabled(True)
        self.read_wait()
        self._reset_action_button_text()
        self.ui.lineEdit_query.setFocus()

    def _insert_correct_ic_card(self, ic_card):
        try:
            if not ic_card.read_basic_data():
                return False
        except AttributeError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('無法使用健保卡')
            msg_box.setText(
                '''
                <font size="4" color="red">
                  <b>無法使用讀卡機, 請改掛異常卡序或欠卡<br>
                </font>
                '''
            )
            msg_box.setInformativeText("請確定讀卡機使用正常使用")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return False

        if ic_card.basic_data['patient_id'] != self.ui.lineEdit_id.text():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('健保卡身分不符')
            msg_box.setText(
                '''
                <font size="4" color="red">
                  <b>此健保卡基本資料為<br>
                  </font>
                    <font size="4" color="blue">
                    {0}: {1}<br>
                    </font>
                    <font size="4" color="red">
                    與現行掛號病患<br>
                    </font>
                    <font size="4" color="blue">
                    {2}: {3}<br>
                    </font>
                    <font size="4" color="red">
                    身分明顯不相符, 請檢查是否插入錯誤的健保卡.</b>
                </font>
                '''.format(ic_card.basic_data['name'],
                           ic_card.basic_data['patient_id'],
                           self.ui.lineEdit_name.text(),
                           self.ui.lineEdit_id.text())
            )
            msg_box.setInformativeText("請確定插入的健保卡是否為此病患所有.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return False
        else:
            return True

    def _write_ic_card(self):
        ic_card = cshis.CSHIS(self.system_settings)
        if not self._insert_correct_ic_card(ic_card):
            return False

        available_date, available_count = ic_card.get_card_status()
        if available_count <= 0:
            ic_card.update_hc(False)

        if not ic_card.get_seq_number_256('03', ' ', '1'):
            return False

        self.ui.comboBox_card.setCurrentText(ic_card.treat_data['seq_number'])
        return ic_card

    # comboBox 內容變更
    def selection_changed(self, i):
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
        elif sender_name == 'comboBox_massager':
            self._set_charge()
        elif (sender_name == 'comboBox_period' or sender_name == 'comboBox_room') and \
                self.ui.action_save.text() == '掛號存檔':
            period = self.ui.comboBox_period.currentText()
            room = self.ui.comboBox_room.currentText()
            reg_no = register_utils.get_reg_no(self.database, self.system_settings, room, period)  # 取得診號
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
    def query_clicked(self):
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
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('查無資料')
            msg_box.setText("<font size='4' color='red'><b>找不到有關的病患資料, 請檢查關鍵字是否有誤.</b></font>")
            msg_box.setInformativeText("請確定輸入資料的正確性, 生日請輸入YYYY-MM-DD.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            self.ui.lineEdit_query.setFocus()
        elif row == -1:  # 取消查詢
            self.ui.lineEdit_query.setFocus()
        else:  # 已選取病患
            self._prepare_registration_data(row, ic_card)

        self.ui.lineEdit_query.clear()

    # 掛號修正
    def modify_wait(self):
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

        if not self._register_precheck(patient_key):
            return
        self._set_charge()
        self._show_past_history(patient_key)

    # 掛號預檢
    def _register_precheck(self, patient_key):
        if register_utils.check_record_duplicated(self.database, patient_key, datetime.datetime.now()):
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
            cancel_register = msg_box.exec_()
            if cancel_register:
                self.action_cancel_triggered()
                return False
            else:
                self.ui.comboBox_ins_type.setCurrentText('自費')
                return True

        return True

    # 顯示病患資料
    def _set_patient_data(self, row):
        self.ui.lineEdit_patient_key.setText(str(row['PatientKey']))
        self.ui.lineEdit_name.setText(strings.xstr(row['Name']))
        self.ui.lineEdit_id.setText(strings.xstr(row['ID']).strip(None))
        share_type = nhi_utils.get_share_type(strings.xstr(row['InsType']).strip(None))
        self.ui.comboBox_patient_share.setCurrentText(share_type)
        self.ui.comboBox_patient_discount.setCurrentText(strings.xstr(row['DiscountType']).strip(None))
        self.ui.comboBox_gender.setCurrentText(strings.xstr(row['Gender']).strip(None))
        self.ui.lineEdit_birthday.setText(strings.xstr(row['Birthday']).strip(None))
        age_year, age_month = date_utils.get_age(row['Birthday'], datetime.datetime.now())
        if age_year is None:
            age = 'N/A'
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)
        self.ui.label_age.setText(age)
        self.ui.lineEdit_telephone.setText(strings.xstr(row['Telephone']))
        self.ui.lineEdit_cellphone.setText(strings.xstr(row['Cellphone']))
        self.ui.lineEdit_address.setText(strings.xstr(row['Address']).strip(None))
        self.ui.lineEdit_patient_remark.setText(strings.get_str(row['Remark'], 'utf8'))
        self._verify_id(self.ui.lineEdit_id.text())
        self.ui.comboBox_card.setFocus()

    # 檢查身分證
    @staticmethod
    def _verify_id(patient_id):
        pattern = re.compile(validator_utils.ID_REGEXP)
        if not pattern.match(patient_id):  # 測試卡
            return

        if not validator_utils.verify_id(patient_id):
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('身分證檢查錯誤')
            msg_box.setText("<font size='4' color='red'><b>身分證可能有誤，請確認身分證號碼是否輸入正確!</b></font>")
            msg_box.setInformativeText("如果確定身分證號正確，可以忽略此項警告.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()

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
            reg_no = register_utils.get_reg_no(self.database, self.system_settings, room)  # 取得診號
            period = register_utils.get_period(self.system_settings)
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
            remark = strings.get_str(medical_record['Remark'], 'utf8')

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
        regist_fee = number.get_integer(self.ui.lineEdit_regist_fee.text())
        diag_share_fee = number.get_integer(self.ui.lineEdit_diag_share_fee.text())
        deposit_fee = number.get_integer(self.ui.lineEdit_deposit_fee.text())
        traditional_health_care_fee = number.get_integer(self.ui.lineEdit_traditional_health_care_fee.text())
        total_amount = regist_fee + diag_share_fee + deposit_fee + traditional_health_care_fee

        self.ui.lineEdit_regist_fee.setText(str(regist_fee))
        self.ui.lineEdit_diag_share_fee.setText(str(diag_share_fee))
        self.ui.lineEdit_deposit_fee.setText(str(deposit_fee))
        self.ui.lineEdit_traditional_health_care_fee.setText(str(traditional_health_care_fee))
        self.ui.lineEdit_total_amount.setText(str(total_amount))

    def _show_past_history(self, patient_key):
        self.dialog_history.show_past_history(patient_key)

    # 掛號存檔/修正存檔
    def _save_files(self, ic_card=None):
        self._save_patient()
        self._save_medical_record(ic_card)

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
            discount = strings.xstr(row['DiscountType'])
            gender = strings.xstr(row['Gender'])
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
        data = (
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
        )
        self.database.update_record('patient', fields, 'PatientKey',
                                    self.ui.lineEdit_patient_key.text(), data)

    # 病歷存檔
    def _save_medical_record(self, ic_card=None):
        if self.ui.action_save.text() == '掛號存檔':
            self._insert_medical_record(ic_card)
        else:
            self._update_medical_record()

    # 新增病歷
    def _insert_medical_record(self, ic_card=None):
        fields = ['CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType', 'Injury',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager',
                  'RegistFee', 'DiagShareFee', 'SDiagShareFee', 'DepositFee', 'SMassageFee', 'Security', 'Remark']

        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database,
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_course.currentText())

        data = (
            str(datetime.datetime.now()),
            self.ui.lineEdit_patient_key.text(),
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_injury_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            str(self.ui.comboBox_card.currentText()).split(' ')[0],
            number.str_to_int(self.ui.comboBox_course.currentText()),
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_massager.currentText(),
            self.ui.lineEdit_regist_fee.text(),
            diag_share_fee,
            self.ui.lineEdit_diag_share_fee.text(),
            self.ui.lineEdit_deposit_fee.text(),
            self.ui.lineEdit_traditional_health_care_fee.text(),
            ic_card.treat_data_to_xml() if ic_card else None,
            self.ui.comboBox_remark.currentText(),
        )
        case_key = self.database.insert_record('cases', fields, data)
        self.insert_wait(case_key)

    # 修正病歷
    def _update_medical_record(self):
        fields = ['Name', 'Visit', 'RegistType', 'Injury',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager',
                  'RegistFee', 'DiagShareFee', 'SDiagShareFee', 'DepositFee', 'SMassageFee', 'Remark']
        diag_share_fee = charge_utils.get_diag_share_fee(
            self.database,
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_course.currentText())
        data = (
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_injury_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_card.currentText(),
            number.str_to_int(self.ui.comboBox_course.currentText()),
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_massager.currentText(),
            self.ui.lineEdit_regist_fee.text(),
            diag_share_fee,
            self.ui.lineEdit_diag_share_fee.text(),
            self.ui.lineEdit_deposit_fee.text(),
            self.ui.lineEdit_traditional_health_care_fee.text(),
            self.ui.comboBox_remark.currentText(),
        )
        case_key = self.table_widget_wait.field_value(1)
        wait_key = self.table_widget_wait.field_value(0)
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)
        self.update_wait(wait_key)

    # 新增候診名單
    def insert_wait(self, case_key):
        fields = ['CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Remark']
        data = (case_key,
                str(datetime.datetime.now()),
                self.ui.lineEdit_patient_key.text(),
                self.ui.lineEdit_name.text(),
                self.ui.comboBox_visit.currentText(),
                self.ui.comboBox_reg_type.currentText(),
                self.ui.comboBox_treat_type.currentText(),
                self.ui.comboBox_share_type.currentText(),
                self.ui.comboBox_ins_type.currentText(),
                str(self.ui.comboBox_card.currentText()).split(' ')[0],
                number.str_to_int(self.ui.comboBox_course.currentText()),
                self.ui.comboBox_period.currentText(),
                self.ui.comboBox_room.currentText(),
                self.ui.spinBox_reg_no.value(),
                self.ui.comboBox_massager.currentText(),
                self.ui.comboBox_remark.currentText(),
                )

        self.database.insert_record('wait', fields, data)

    # 修正候診名單
    def update_wait(self, wait_key):
        fields = ['Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Remark']
        data = (
            self.ui.lineEdit_name.text(),
            self.ui.comboBox_visit.currentText(),
            self.ui.comboBox_reg_type.currentText(),
            self.ui.comboBox_treat_type.currentText(),
            self.ui.comboBox_share_type.currentText(),
            self.ui.comboBox_ins_type.currentText(),
            self.ui.comboBox_card.currentText(),
            number.str_to_int(self.ui.comboBox_course.currentText()),
            self.ui.comboBox_period.currentText(),
            self.ui.comboBox_room.currentText(),
            self.ui.spinBox_reg_no.value(),
            self.ui.comboBox_massager.currentText(),
            self.ui.comboBox_remark.currentText(),
        )
        self.database.update_record('wait', fields, 'WaitKey', wait_key, data)

    # 刪除候診名單
    def delete_wait_clicked(self):
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
        self.database.delete_record('cases', 'CaseKey', case_key)
        self.ui.tableWidget_wait.removeRow(self.ui.tableWidget_wait.currentRow())
        if self.ui.tableWidget_wait.rowCount() <= 0:
            self._set_tool_button(False)

    # 初診掛號
    def _new_patient(self):
        self.parent.open_patient_record(None, '門診掛號')

    # 補印收據
    def print_wait_clicked(self):
        case_key = self._get_tabWidget_wait_row_data(1)
        print_regist = print_registration.PrintRegistration(case_key, self.database, self.system_settings)
        print_regist.printing()
        del print_regist

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_registration(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = Registration()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
