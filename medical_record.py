#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox, QAction
import datetime
import sip
import sys

from classes import udp_socket_client
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import date_utils
from libs import cshis_utils
from libs import nhi_utils
from libs import system_utils
from libs import db_utils
from libs import dialog_utils
from libs import registration_utils
from libs import personnel_utils
from libs import prescript_utils
from libs import charge_utils

from printer import print_prescription
from printer import print_receipt
from printer import print_misc

import ins_prescript_record
import ins_care_record
import self_prescript_record
import medical_record_recently_history
import medical_record_fees
import medical_record_registration
import medical_record_family
import medical_record_examination
import medical_record_check

from dialog import dialog_diagnostic_picker
from dialog import dialog_disease_picker
from dialog import dialog_inquiry
from dialog import dialog_diagnosis
from dialog import dialog_disease
from dialog import dialog_medicine
from dialog import dialog_medical_record_past_history
from dialog import dialog_medical_record_reference
from dialog import dialog_medical_record_hosts
from dialog import dialog_medical_record_collection
from dialog import dialog_add_diagnostic_dict

if sys.platform == 'win32':
    from classes import cshis_win32 as cshis
else:
    from classes import cshis


# 病歷資料 2018.01.31
class MedicalRecord(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.case_key = args[2]
        self.call_from = args[3]

        self.medical_record = None
        self.patient_record = None
        self.patient_key = None
        self.ins_type = None
        self.record_saved = False
        self.first_record = None
        self.last_record = None
        self.input_code = ''
        self.ui = None
        self._init_tab()
        self.close_tab_warning = True
        self.user_name = self.system_settings.field('使用者')

        if not self._read_data():
            return

        self._set_ui()
        self._set_signal()
        self._set_data()
        if self.call_from == '醫師看診作業':
            self._set_in_progress('"Y"')

        self._set_permission()

    def _init_tab(self):
        self.tab_ins_prescript = None
        self.tab_self_prescript1 = None
        self.tab_self_prescript2 = None
        self.tab_self_prescript3 = None
        self.tab_self_prescript4 = None
        self.tab_self_prescript5 = None
        self.tab_self_prescript6 = None
        self.tab_self_prescript7 = None
        self.tab_self_prescript8 = None
        self.tab_self_prescript9 = None
        self.tab_self_prescript10 = None
        self.tab_self_prescript11 = None
        self.tab_list = [
            self.tab_ins_prescript,
            self.tab_self_prescript1,
            self.tab_self_prescript2,
            self.tab_self_prescript3,
            self.tab_self_prescript4,
            self.tab_self_prescript5,
            self.tab_self_prescript6,
            self.tab_self_prescript7,
            self.tab_self_prescript8,
            self.tab_self_prescript9,
            self.tab_self_prescript10,
            self.tab_self_prescript11,
        ]
        self.max_tab = len(self.tab_list)

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        if self.call_from == '醫師看診作業':
            self._set_in_progress('NULL')

    # 設定GUI
    def _set_ui(self):
        ui_file = ui_utils.get_medical_record_ui_file(self.system_settings)
        self.ui = ui_utils.load_ui_file(ui_file, self)

        system_utils.set_css(self, self.system_settings)

        self.add_tab_button = QtWidgets.QToolButton()
        self.add_tab_button.setIcon(QtGui.QIcon('./icons/document-new.svg'))
        self.ui.tabWidget_prescript.setCornerWidget(self.add_tab_button, QtCore.Qt.TopLeftCorner)
        self.ui.toolButton_add_symptom_dict.setEnabled(False)

        self.tab_registration = medical_record_registration.MedicalRecordRegistration(
            self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_medical.addTab(self.tab_registration, '門診資料')
        self.tab_registration.set_special_code()

        self.disease_code_changed()

        self._set_timer()
        self._set_hosts()

        if self.patient_key is None:
            self.ui.action_patient.setEnabled(False)
            self.ui.action_past_history.setEnabled(False)
            self.ui.action_open_hosts.setEnabled(False)
            self.ui.action_append_self_medical_record.setEnabled(False)
            return

        self.tab_family = medical_record_family.MedicalRecordFamily(
            self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_medical.addTab(self.tab_family, '家族病歷')

        self.tab_examination = medical_record_examination.MedicalRecordExamination(
            self, self.database, self.system_settings, self.patient_key, self.call_from)
        self.ui.tabWidget_medical.addTab(self.tab_examination, '檢驗報告')

        self._set_event_filter()

        doctor = self.medical_record['Doctor']
        if doctor is not None:
            self.ui.groupBox_diagnostic.setTitle('診斷  (主治醫師: {0})'.format(doctor))

    def _set_event_filter(self):
        self.ui.textEdit_symptom.installEventFilter(self)
        self.ui.textEdit_tongue.installEventFilter(self)
        self.ui.textEdit_pulse.installEventFilter(self)
        self.ui.textEdit_remark.installEventFilter(self)
        self.ui.lineEdit_disease_code1.installEventFilter(self)
        self.ui.lineEdit_disease_code2.installEventFilter(self)
        self.ui.lineEdit_disease_code3.installEventFilter(self)
        self.ui.lineEdit_distinguish.installEventFilter(self)
        self.ui.lineEdit_cure.installEventFilter(self)

    def eventFilter(self, source, event):
        obj_name = source.objectName()

        if obj_name in [
            'textEdit_symptom',
            'textEdit_tongue',
            'textEdit_pulse',
            'textEdit_remark'
        ]:
            if event.type() == QtCore.QEvent.FocusIn:
                system_utils.set_keyboard_layout('中文')
        elif obj_name in [
            'lineEdit_disease_code1',
            'lineEdit_disease_code2',
            'lineEdit_disease_code3',
            'lineEdit_distinguish',
            'lineEdit_cure',
        ]:
            if event.type() == QtCore.QEvent.FocusIn:
                system_utils.set_keyboard_layout('英文')

        return False

    # 看診時間提醒
    def _set_timer(self):
        if self.call_from not in ['醫師看診作業', '新增自費病歷']:
            self.ui.lcdNumber.setVisible(False)
            return

        self.BLINKING_TIME = 9999  # 看診警告時間
        self.ui.lcdNumber.display('00:00')
        self.timer = QtCore.QTimer(self)
        self.set_blinking = False
        self.minutes = 0
        self.seconds = 0
        self.timer.start(1000)
        self.timer.timeout.connect(self._timeout)

    def _timeout(self):
        self.seconds += 1
        if self.seconds >= 60:
            self.minutes += 1
            self.seconds = 0

        self.ui.lcdNumber.display('{minutes:0>2}:{seconds:0>2}'.format(
            minutes=self.minutes, seconds=self.seconds,
        ))

        if self.minutes >= self.BLINKING_TIME and not self.set_blinking:
            self.set_blinking = True
            self.ui.lcdNumber.setStyleSheet('color: red')
            self._set_blinking_timer()

    def _set_blinking_timer(self):
        self.micro_seconds = 0

        self.blink_timer = QtCore.QTimer(self)
        self.blink_timer.start(100)
        self.blink_timer.timeout.connect(self._blink_timeout)

    def _blink_timeout(self):
        self.micro_seconds += 1
        if self.micro_seconds >= 5:
            self.micro_seconds = 0

        if self.micro_seconds == 0:
            self.ui.lcdNumber.hide()
        else:
            self.ui.lcdNumber.show()

    def _set_hosts(self):
        sql = '''
            SELECT * FROM hosts
            ORDER BY HostsKey
        '''
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            self.ui.action_open_hosts.setVisible(False)

    def _open_medical_record_hosts(self):
        patient_id = string_utils.xstr(self.patient_record['ID'])
        if patient_id == '':
            return

        dialog = dialog_medical_record_hosts.DialogMedicalRecordHosts(
            self, self.database, self.system_settings, patient_id,
        )

        dialog.exec_()
        dialog.deleteLater()

    def _open_medical_record_collection(self):
        dialog = dialog_medical_record_collection.DialogMedicalRecordCollection(
            self, self.database, self.system_settings,
        )

        dialog.exec_()
        dialog.deleteLater()

    # 設定信號
    def _set_signal(self):
        self.ui.action_past_history.triggered.connect(self._open_past_history)
        self.ui.action_save.triggered.connect(self.save_medical_record)

        self.ui.action_save_and_print.triggered.connect(self.save_medical_record)
        self.ui.action_save_and_print_prescript.triggered.connect(self.save_medical_record)
        self.ui.action_save_and_print_receipt.triggered.connect(self.save_medical_record)
        self.ui.action_save_and_print_misc.triggered.connect(self.save_medical_record)

        self.ui.action_dictionary.triggered.connect(self.open_dictionary)
        self.ui.action_reference.triggered.connect(self._open_medical_record_reference)
        self.ui.action_close.triggered.connect(self.close_medical_record)
        self.ui.action_patient.triggered.connect(self.modify_patient)
        self.ui.action_append_self_medical_record.triggered.connect(self._append_new_self_medical_record)
        self.ui.action_open_hosts.triggered.connect(self._open_medical_record_hosts)
        self.ui.action_medical_record_collection.triggered.connect(self._open_medical_record_collection)
        self.ui.action_reservation.triggered.connect(self._open_reservation)

        self.ui.lineEdit_disease_code1.textChanged.connect(self.disease_code_changed)
        self.ui.lineEdit_disease_code1.returnPressed.connect(self.disease_code_return_pressed)
        self.ui.lineEdit_disease_code1.editingFinished.connect(self.disease_code_editing_finished)

        self.ui.lineEdit_disease_code2.textChanged.connect(self.disease_code_changed)
        self.ui.lineEdit_disease_code2.editingFinished.connect(self.disease_code_editing_finished)
        self.ui.lineEdit_disease_code2.returnPressed.connect(self.disease_code_return_pressed)

        self.ui.lineEdit_disease_code3.textChanged.connect(self.disease_code_changed)
        self.ui.lineEdit_disease_code3.returnPressed.connect(self.disease_code_return_pressed)
        self.ui.lineEdit_disease_code3.editingFinished.connect(self.disease_code_editing_finished)

        self.add_tab_button.clicked.connect(self.add_prescript_tab)

        self.ui.toolButton_symptom.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_tongue.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_pulse.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_remark.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_today.clicked.connect(self._insert_today)
        self.ui.toolButton_add_symptom_dict.clicked.connect(self._add_symptom_dict)
        self.ui.textEdit_symptom.selectionChanged.connect(self._symptom_selection_changed)

        self.ui.toolButton_disease1.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_disease2.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_disease3.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_distincts.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.toolButton_cure.clicked.connect(self._tool_button_dictionary_clicked)

        self.ui.pushButton_symptom.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_tongue.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_pulse.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_remark.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_disease1.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_disease2.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_disease3.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_distincts.clicked.connect(self._tool_button_dictionary_clicked)
        self.ui.pushButton_cure.clicked.connect(self._tool_button_dictionary_clicked)

        self.ui.tabWidget_prescript.tabCloseRequested.connect(self.close_prescript_tab)                  # 關閉分頁
        self.ui.tabWidget_prescript.tabBar().tabMoved.connect(self._tab_moved)
        self.ui.tabWidget_prescript.currentChanged.connect(self._tab_changed)                   # 切換分頁

        self.ui.textEdit_symptom.keyPressEvent = self._text_edit_key_press
        self.ui.textEdit_tongue.keyPressEvent = self._text_edit_key_press
        self.ui.textEdit_pulse.keyPressEvent = self._text_edit_key_press
        self.ui.textEdit_remark.keyPressEvent = self._text_edit_key_press

    def _tab_moved(self, move_to_index):
        tab_no = 0
        for tab_index in range(self.ui.tabWidget_prescript.count()):
            tab_name = self.ui.tabWidget_prescript.tabText(tab_index)
            if tab_name == '健保':
                continue

            tab_no += 1
            self.ui.tabWidget_prescript.setTabText(tab_index, '自費{0}'.format(tab_no))
            tab = self.ui.tabWidget_prescript.widget(tab_index)
            tab.medicine_set = tab_no + 1
            for row_no in range(tab.tableWidget_prescript.rowCount()):
                tab.tableWidget_prescript.setItem(row_no, 0, QtWidgets.QTableWidgetItem('-1'))

        self._adjust_tabs()

    def _adjust_tabs(self):
        tab_index_dict = {
            '健保': 0,
            '自費1': 1,
            '自費2': 2,
            '自費3': 3,
            '自費4': 4,
            '自費5': 5,
            '自費6': 6,
            '自費7': 7,
            '自費8': 8,
            '自費9': 9,
            '自費10': 10,
            '加強照護': 11,
        }

        for tab_index in range(self.ui.tabWidget_prescript.count()):
            tab_name = self.ui.tabWidget_prescript.tabText(tab_index)
            current_tab = self.ui.tabWidget_prescript.widget(tab_index)

            self.tab_list[tab_index_dict[tab_name]] = current_tab

    def _tab_changed(self, i):
        tab_name = self.ui.tabWidget_prescript.tabText(i)

        if (self.call_from != '醫師看診作業' and
                personnel_utils.get_permission(self.database, '病歷資料', '病歷修正', self.user_name) != 'Y'):
            movable = False
        elif tab_name == '健保':
            movable = False
        else:
            movable = True

        self.ui.tabWidget_prescript.setMovable(movable)

    def close_prescript_tab(self, current_index):
        current_tab = self.ui.tabWidget_prescript.widget(current_index)
        tab_name = self.ui.tabWidget_prescript.tabText(current_index)
        if tab_name == '健保':
            return

        if self.close_tab_warning:
            msg_box = dialog_utils.get_message_box(
                '關閉{0}頁面'.format(tab_name), QMessageBox.Warning,
                '<font size="4" color="red"><b>確定關閉{0}病歷處方頁面?</b></font>'.format(tab_name),
                '注意！資料刪除後, 將無法回復!'
            )
            close_tab = msg_box.exec_()
            if not close_tab:
                return

        self.close_tab_warning = True

        for i in range(1, len(self.tab_list)):
            if tab_name == '自費{0}'.format(i):
                self.tab_list[i] = None

        self.tab_medical_record_fees.calculate_fees()
        current_tab.close_all()
        current_tab.deleteLater()

        sip.delete(current_tab)  # 真正的刪除分頁

        self.tab_medical_record_fees.calculate_fees()

    # 關閉所有自費處方頁
    def close_all_self_prescript_tabs(self):
        for i in range(len(self.tab_list), 0, -1):
            current_tab = self.ui.tabWidget_prescript.widget(i)
            if current_tab is not None:
                tab_name = self.ui.tabWidget_prescript.tabText(i)
                if tab_name == '加強照護':  # 加強照護不要關閉
                    continue

                self.close_tab_warning = False
                self.close_prescript_tab(i)

    def close_medical_record(self):
        self.close_all()
        self.close_tab()

    def modify_patient(self):
        self.parent.open_patient_record(self.patient_key, '門診掛號')

    def disease_code_editing_finished(self):
        disease_list = [
            [self.ui.lineEdit_disease_code1, self.ui.lineEdit_disease_name1],
            [self.ui.lineEdit_disease_code2, self.ui.lineEdit_disease_name2],
            [self.ui.lineEdit_disease_code3, self.ui.lineEdit_disease_name3],
        ]

        for i in range(len(disease_list)):
            if disease_list[i][1].text() == '':
                disease_list[i][0].setText('')
                if i == 0:
                    self.tab_registration.ui.lineEdit_special_code.setText('')

    # 設定診斷碼輸入狀態
    def disease_code_changed(self):
        disease_list = [
            [
                self.ui.lineEdit_disease_code1,
                self.ui.lineEdit_disease_name1,
                self.ui.toolButton_disease1,
                self.ui.pushButton_disease1,
            ],
            [
                self.ui.lineEdit_disease_code2,
                self.ui.lineEdit_disease_name2,
                self.ui.toolButton_disease2,
                self.ui.pushButton_disease2,
            ],
            [
                self.ui.lineEdit_disease_code3,
                self.ui.lineEdit_disease_name3,
                self.ui.toolButton_disease3,
                self.ui.pushButton_disease3,
            ],
        ]

        for row_no in reversed(range(len(disease_list))):
            icd_code = str(disease_list[row_no][0].text()).strip()
            if icd_code == '':
                disease_list[row_no][1].setText(None)
                if row_no > 0:
                    if disease_list[row_no-1][0].text() == '':
                        disease_list[row_no][0].setEnabled(False)
                        disease_list[row_no][2].setEnabled(False)
                        disease_list[row_no][3].setEnabled(False)
                    else:
                        disease_list[row_no][0].setEnabled(True)
                        disease_list[row_no][2].setEnabled(True)
                        disease_list[row_no][3].setEnabled(True)

            for i in range(len(disease_list)):
                if i == len(disease_list) - 1:
                    break

                if disease_list[i][0].text() == '' and disease_list[i+1][0].text() != '':
                    self.tab_registration.ui.lineEdit_special_code.setText('')
                    disease_list[i][0].setText(disease_list[i+1][0].text())
                    disease_list[i][1].setText(disease_list[i+1][1].text())
                    disease_list[i+1][0].setText(None)

        self._check_primary_disease()

    # 檢查主診斷是否為慢性病
    def _check_primary_disease(self):
        icd_code = self.ui.lineEdit_disease_code1.text()
        if icd_code == '':
            return

        sql = '''
            SELECT * FROM icd10
            WHERE
                ICDCode = "{icd_code}"
        '''.format(
            icd_code=icd_code,
        )

        rows = self.database.select_record(sql)
        if len(rows) <= 0 or len(rows) >= 2:
            return

        row = rows[0]
        self.tab_registration.ui.lineEdit_special_code.setText(
            string_utils.xstr(row['SpecialCode'])
        )

    def disease_code_return_pressed(self):
        icd_code = self.sender().text()
        if icd_code == '':
            return

        sender_name = self.sender().objectName()
        if sender_name == 'lineEdit_disease_code1':
            line_edit_disease_name = self.ui.lineEdit_disease_name1
        elif sender_name == 'lineEdit_disease_code2':
            line_edit_disease_name = self.ui.lineEdit_disease_name2
        elif sender_name == 'lineEdit_disease_code3':
            line_edit_disease_name = self.ui.lineEdit_disease_name3
        else:
            return

        if icd_code.isdigit():
            # 只讀兩筆確定是否要開啟視窗
            sql = '''
                SELECT
                    icd10.ICD10Key,
                    icd10.ICDCode,
                    icd10.ChineseName,
                    icd10.EnglishName,
                    icd10.SpecialCode
                FROM icdmap
                    LEFT JOIN icd10
                    ON icdmap.ICD10Code = icd10.ICDCode
                WHERE
                    ICD9Code LIKE "{0}%"
                ORDER BY icd10.ICDCode LIMIT 2
            '''.format(icd_code)
        else:
            keyword_list = icd_code.split()
            chinese_name_script = []
            for keyword in keyword_list:
                chinese_name_script.append('ChineseName LIKE "%{0}%"'.format(keyword))

            if len(chinese_name_script) > 0:
                chinese_name_script = ' AND '.join(chinese_name_script)
                chinese_name_script = 'OR ({0})'.format(chinese_name_script)

            # 只讀兩筆確定是否要開啟視窗
            sql = '''
                SELECT * FROM icd10
                WHERE
                    ICDCode LIKE "{icd_code}%" OR
                    InputCode LIKE "%{icd_code}%"
                    {chinese_name_script}
                    LIMIT 2 
            '''.format(
                icd_code=icd_code,
                chinese_name_script=chinese_name_script,
            )

        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '無此病名',
                '<font size="4" color="red"><b>找不到此關鍵字的病名, 請重新輸入.</b></font>',
                '請確定輸入的關鍵字是否正確.'
            )
            self.sender().setText(None)
            return
        elif len(rows) == 1:
            self._set_disease(
                self.sender(), line_edit_disease_name,
                string_utils.xstr(rows[0]['ICDCode']),
                string_utils.xstr(rows[0]['ChineseName'])
            )
            if self.sender().objectName() == 'lineEdit_disease_code1':
                self.tab_registration.ui.lineEdit_special_code.setText(
                    string_utils.xstr(rows[0]['SpecialCode'])
                )
        elif len(rows) >= 2:
            self._open_disease_dialog(icd_code, self.sender(), line_edit_disease_name)

        if line_edit_disease_name == self.ui.lineEdit_disease_name1:
            self.ui.lineEdit_disease_code2.setFocus(True)
        elif line_edit_disease_name == self.ui.lineEdit_disease_name2:
            self.ui.lineEdit_disease_code3.setFocus(True)

    def _open_disease_dialog(self, icd_code, line_edit_disease_code, line_edit_disease_name):
        dialog = dialog_disease_picker.DialogDiseasePicker(
            self, self.database, self.system_settings, icd_code
        )

        if dialog.exec_():
            icd10_key = dialog.icd10_key
            icd_code = dialog.icd_code
            disease_name = dialog.chinese_name
            special_code = dialog.special_code
            self._set_disease(
                line_edit_disease_code, line_edit_disease_name,
                icd_code, disease_name,
            )

            if line_edit_disease_code == self.ui.lineEdit_disease_code1:
                self.tab_registration.ui.lineEdit_special_code.setText(
                    string_utils.xstr(special_code)
                )
            db_utils.increment_hit_rate(self.database, 'icd10', 'ICD10Key', icd10_key)

        dialog.close_all()
        dialog.deleteLater()

    def _set_disease(self, line_edit_disease_code, line_edit_disease_name, icd_code, disease_name):
        line_edit_disease_code.setText(icd_code)
        line_edit_disease_name.setText(disease_name)

    def _read_data(self):
        read_result = True
        try:
            sql = 'SELECT * FROM cases WHERE CaseKey = {0}'.format(self.case_key)
            self.medical_record = self.database.select_record(sql)[0]
            self.ins_type = string_utils.xstr(self.medical_record['InsType'])
        except IndexError:
            system_utils.show_message_box(
                QtWidgets.QMessageBox.Critical,
                '資料遺失',
                '<font size="4" color="red"><b>找不到病歷資料, 請重新掛號.</b></font>',
                '資料不明原因遺失.'
            )
            read_result = False

        if self.medical_record['PatientKey'] == 0:
            return read_result

        try:
            sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(self.medical_record['PatientKey'])
            self.patient_record = self.database.select_record(sql)[0]
            self.patient_key = self.patient_record['PatientKey']
        except IndexError:
            system_utils.show_message_box(
                QtWidgets.QMessageBox.Critical,
                '資料遺失',
                '<font size="4" color="red"><b>找不到病患資料, 請更新病歷內的病歷號碼.</b></font>',
                '資料不明原因遺失.'
            )
            # read_result = False

        return read_result

    def _set_data(self):
        self._set_patient_data()
        if self.call_from == '新增自費病歷':
            self._read_recently_history()
            self.case_key = -1
            self.ins_type = '自費'
            self._read_fees()
            self.add_prescript_tab(2)
            return

        self._set_medical_record()
        self._set_prescripts()
        self._set_fees()
        self._set_misc()

    def _set_permission(self):
        if self.call_from == '醫師看診作業':
            return

        if self.user_name == '超級使用者':
            return

        if personnel_utils.get_permission(self.database, '病歷資料', '病歷修正', self.user_name) == 'Y':
            return

        self.ui.action_save.setEnabled(False)
        self.ui.action_save_and_print.setEnabled(False)
        self.ui.action_save_and_print_prescript.setEnabled(False)
        self.ui.action_save_and_print_receipt.setEnabled(False)
        self.ui.action_save_and_print_misc.setEnabled(False)

        self.ui.action_dictionary.setEnabled(False)
        self.ui.action_append_self_medical_record.setEnabled(False)
        self.ui.action_reference.setEnabled(False)
        self.ui.action_reservation.setEnabled(False)

        self.ui.textEdit_symptom.setReadOnly(True)
        self.ui.textEdit_tongue.setReadOnly(True)
        self.ui.textEdit_pulse.setReadOnly(True)
        self.ui.textEdit_remark.setReadOnly(True)

        self.ui.lineEdit_disease_code1.setReadOnly(True)
        self.ui.lineEdit_disease_code2.setReadOnly(True)
        self.ui.lineEdit_disease_code3.setReadOnly(True)

        self.ui.lineEdit_distinguish.setReadOnly(True)
        self.ui.lineEdit_cure.setReadOnly(True)

        self.ui.toolButton_symptom.setEnabled(False)
        self.ui.toolButton_today.setEnabled(False)
        self.ui.toolButton_add_symptom_dict.setEnabled(False)
        self.ui.checkBox_reference.setEnabled(False)

        self.ui.toolButton_tongue.setEnabled(False)
        self.ui.toolButton_pulse.setEnabled(False)
        self.ui.toolButton_remark.setEnabled(False)

        self.ui.toolButton_disease1.setEnabled(False)
        self.ui.toolButton_disease2.setEnabled(False)
        self.ui.toolButton_disease3.setEnabled(False)

        self.ui.toolButton_distincts.setEnabled(False)
        self.ui.toolButton_cure.setEnabled(False)

        self.ui.tabWidget_prescript.setTabsClosable(False)
        self.ui.tabWidget_prescript.setMovable(False)

    # 設定看診中
    def _set_in_progress(self, in_progress):
        wait_key = self._get_wait_key()

        if wait_key is None:
            return

        sql = '''
            UPDATE wait
            SET
                InProgress = {in_progress}
            WHERE
                WaitKey = {wait_key}
        '''.format(
            in_progress=in_progress,
            wait_key=wait_key,
        )
        self.database.exec_sql(sql)

        if in_progress == '"Y"':
            progress_type = '診療中'
        else:
            progress_type = '診療結束'

        socket_client = udp_socket_client.UDPSocketClient()
        socket_client.send_data(progress_type)

    def _get_wait_key(self):
        sql = '''
            SELECT WaitKey FROM wait
            WHERE
                CaseKey = {case_key}
        '''.format(
            case_key=self.case_key,
        )
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            wait_key = None
        else:
            wait_key = rows[0]['WaitKey']

        return wait_key

    def _set_patient_data(self):
        if self.patient_record is None:
            name = string_utils.xstr(self.medical_record['Name'])
            self.ui.label_case_date.setText(string_utils.xstr(self.medical_record['CaseDate']))
            self.ui.label_ins_type.setText(self.ins_type)
            self.ui.label_patient_name.setText(string_utils.xstr(name))
            self.ui.label_regist_no.setText('')
            self.ui.label_share_type.setText('')
            self.ui.label_card.setText('')
            return

        patient_key = string_utils.xstr(self.patient_record['PatientKey'])
        regist_type = string_utils.xstr(self.medical_record['RegistType'])
        self.ui.groupBox_patient.setTitle(
            '病患基本資料 (病歷號: {patient_key}, {regist_type})'.format(
                patient_key=patient_key,
                regist_type=regist_type,
            )
        )
        name = string_utils.xstr(self.patient_record['Name'])

        age_year, age_month = date_utils.get_age(
            self.patient_record['Birthday'], self.medical_record['CaseDate'])
        if age_year is None:
            age = ''
        else:
            age = '{0}歲{1}月'.format(age_year, age_month)

        gender = self.patient_record['Gender']
        if gender in ['男', '女']:
            gender = '({0})'.format(gender)
        else:
            gender = ''

        name += ' {0} {1}'.format(gender, age)

        card = string_utils.xstr(self.medical_record['Card'])
        if number_utils.get_integer(self.medical_record['Continuance']) >= 1:
            card += '-' + string_utils.xstr(self.medical_record['Continuance'])

        self.ui.label_case_date.setText(string_utils.xstr(self.medical_record['CaseDate']))
        self.ui.label_ins_type.setText(string_utils.xstr(self.ins_type))
        self.ui.label_patient_name.setText(string_utils.xstr(name))
        self.ui.label_regist_no.setText(string_utils.xstr(self.medical_record['RegistNo']))
        self.ui.label_share_type.setText(string_utils.xstr(self.medical_record['Share']))
        self.ui.label_card.setText(string_utils.xstr(card))

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def record_modified(self):
        modified = False
        try:
            if self.ui.textEdit_symptom.document().isModified() or \
                    self.ui.textEdit_tongue.document().isModified() or \
                    self.ui.textEdit_pulse.document().isModified() or \
                    self.ui.textEdit_remark.document().isModified() or \
                    self.ui.lineEdit_disease_code1.isModified() or \
                    self.ui.lineEdit_disease_code2.isModified() or \
                    self.ui.lineEdit_disease_code3.isModified() or \
                    self.ui.lineEdit_distinguish.isModified() or \
                    self.ui.lineEdit_cure.isModified():
                modified = True
        except AttributeError:
            pass

        return modified

    def _tool_button_dictionary_clicked(self):
        sender_name = self.sender().objectName()
        tool_button_dict = {
            'toolButton_symptom': '主訴',
            'toolButton_tongue': '舌診',
            'toolButton_pulse': '脈象',
            'toolButton_remark': '備註',
            'toolButton_disease1': '病名1',
            'toolButton_disease2': '病名2',
            'toolButton_disease3': '病名3',
            'toolButton_distincts': '辨證',
            'toolButton_cure': '治則',

            'pushButton_symptom': '主訴',
            'pushButton_tongue': '舌診',
            'pushButton_pulse': '脈象',
            'pushButton_remark': '備註',
            'pushButton_disease1': '病名1',
            'pushButton_disease2': '病名2',
            'pushButton_disease3': '病名3',
            'pushButton_distincts': '辨證',
            'pushButton_cure': '治則',
        }

        self.open_dictionary(None, tool_button_dict[sender_name])

    def open_dictionary(self, medicine_set, dialog_type=None):
        if not dialog_type:
            if self.ui.textEdit_symptom.hasFocus():
                dialog_type = '主訴'
            elif self.ui.textEdit_tongue.hasFocus():
                dialog_type = '舌診'
            elif self.ui.textEdit_pulse.hasFocus():
                dialog_type = '脈象'
            elif self.ui.textEdit_remark.hasFocus():
                dialog_type = '備註'
            elif self.ui.lineEdit_distinguish.hasFocus():
                dialog_type = '辨證'
            elif self.ui.lineEdit_cure.hasFocus():
                dialog_type = '治則'
            elif self.ui.lineEdit_disease_code1.hasFocus():
                dialog_type = '病名1'
            elif self.ui.lineEdit_disease_code2.hasFocus():
                dialog_type = '病名2'
            elif self.ui.lineEdit_disease_code3.hasFocus():
                dialog_type = '病名3'
            else:
                for i in range(len(self.tab_list)):
                    if self.tab_list[i] is not None and self.tab_list[i].ui.tableWidget_prescript.hasFocus():
                        if i == 0:
                            dialog_type = '健保處方'
                        else:
                            dialog_type = '自費處方'

                        medicine_set = i + 1
                    elif self.tab_list[0].ui.tableWidget_treat.hasFocus():
                        dialog_type = '健保處置'
                        medicine_set = 1

        if dialog_type is None:
            return

        text_edit = {
            '主訴': self.ui.textEdit_symptom,
            '舌診': self.ui.textEdit_tongue,
            '脈象': self.ui.textEdit_pulse,
            '備註': self.ui.textEdit_remark,
            '辨證': self.ui.lineEdit_distinguish,
            '治則': self.ui.lineEdit_cure,
            '病名1': self.ui.lineEdit_disease_code1,
            '病名2': self.ui.lineEdit_disease_code2,
            '病名3': self.ui.lineEdit_disease_code3,
        }
        dialog = None
        if dialog_type in ['主訴', '舌診', '脈象', '備註']:
            dialog = dialog_inquiry.DialogInquiry(
                self, self.database, self.system_settings, dialog_type, text_edit[dialog_type])
        elif dialog_type in ['辨證']:
            dialog = dialog_diagnosis.DialogDiagnosis(
                self, self.database, self.system_settings,
                dialog_type,
                text_edit[dialog_type],
                text_edit['治則'],
            )
        elif dialog_type in ['治則']:
            dialog = dialog_diagnosis.DialogDiagnosis(
                self, self.database, self.system_settings, dialog_type, text_edit[dialog_type], None)
        elif dialog_type in ['病名1', '病名2', '病名3']:
            line_edit = self.ui.lineEdit_disease_name1

            if dialog_type == '病名1':
                line_edit = self.ui.lineEdit_disease_name1
            elif dialog_type == '病名2':
                line_edit = self.ui.lineEdit_disease_name2
            elif dialog_type == '病名3':
                line_edit = self.ui.lineEdit_disease_name3

            line_special_code = self.tab_registration.ui.lineEdit_special_code

            dialog = dialog_disease.DialogDisease(
                self, self.database, self.system_settings,
                text_edit[dialog_type], line_edit,
                line_special_code,
                self.ui.lineEdit_disease_code2, self.ui.lineEdit_disease_name2,
                '所有病名',
            )
        elif dialog_type in ['健保處方', '自費處方'] and medicine_set is not None:
            if dialog_type == '健保處方':
                dict_type = '健保藥品'
            else:
                dict_type = '藥品'

            dialog = dialog_medicine.DialogMedicine(
                self, self.database, self.system_settings,
                self.tab_list[medicine_set-1].tableWidget_prescript, medicine_set,
                dict_type,
            )
        elif dialog_type in ['健保處置', '自費處置'] and medicine_set is not None:
            dialog = dialog_medicine.DialogMedicine(
                self, self.database, self.system_settings,
                self.tab_list[medicine_set-1].tableWidget_prescript, medicine_set,
                '處置',
            )

        if dialog is None:
            return

        dialog.exec_()
        dialog.deleteLater()

    # 顯示病歷
    def _set_medical_record(self):
        self.ui.textEdit_symptom.setText(string_utils.get_str(self.medical_record['Symptom'], 'utf8'))
        self.ui.textEdit_tongue.setText(string_utils.get_str(self.medical_record['Tongue'], 'utf8'))
        self.ui.textEdit_pulse.setText(string_utils.get_str(self.medical_record['Pulse'], 'utf8'))
        self.ui.textEdit_remark.setText(string_utils.get_str(self.medical_record['Remark'], 'utf8'))
        self.ui.lineEdit_disease_code1.setText(string_utils.get_str(self.medical_record['DiseaseCode1'], 'utf8'))
        self.ui.lineEdit_disease_name1.setText(string_utils.get_str(self.medical_record['DiseaseName1'], 'utf8'))
        self.ui.lineEdit_disease_code2.setText(string_utils.get_str(self.medical_record['DiseaseCode2'], 'utf8'))
        self.ui.lineEdit_disease_name2.setText(string_utils.get_str(self.medical_record['DiseaseName2'], 'utf8'))
        self.ui.lineEdit_disease_code3.setText(string_utils.get_str(self.medical_record['DiseaseCode3'], 'utf8'))
        self.ui.lineEdit_disease_name3.setText(string_utils.get_str(self.medical_record['DiseaseName3'], 'utf8'))
        self.ui.lineEdit_distinguish.setText(string_utils.get_str(self.medical_record['Distincts'], 'utf8'))
        self.ui.lineEdit_cure.setText(string_utils.get_str(self.medical_record['Cure'], 'utf8'))

        if self.medical_record['Reference'] == 'True':
            self.ui.checkBox_reference.setChecked(True)
        else:
            self.ui.checkBox_reference.setChecked(False)

    # 顯示處方
    def _set_prescripts(self):
        if self.ins_type == '健保':  # 健保一定要開啟
            self.add_prescript_tab(1)

        # 讀取自費資料
        sql = '''
            SELECT MedicineSet 
            FROM prescript 
            WHERE
                CaseKey = {0} AND MedicineSet >= 2 AND MedicineSet != 11
            GROUP BY MedicineSet ORDER BY MedicineSet
        '''.format(self.case_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            rows = []
            rows.append({'MedicineSet': 2})

        for row in rows:
            self.add_prescript_tab(row['MedicineSet'])

    def _set_fees(self):
        if self.call_from == '醫師看診作業':
            self._read_recently_history()
            self._read_fees()
        else:
            self._read_fees()
            self._read_recently_history()

    # 設定雜項 (這個要在 _set_fees 之後才能執行)
    def _set_misc(self):
        if self.call_from != '醫師看診作業':
            return

        if self.system_settings.field('自動顯示過去病歷') == 'Y':
            self._open_past_history()

        if self.ins_type == '健保':
            self._medical_record_precheck()

    def _get_new_tab(self, max_medicine_set):
        tab_name = None
        medicine_set = 2
        for i in range(2, max_medicine_set + 1):  # MedicineSet2 ~ MedicineSet7  最多六帖藥
            tab_name = '自費{0}'.format(medicine_set-1)
            if self._tab_exists(tab_name):
                medicine_set += 1
                if medicine_set > max_medicine_set:
                    return False, None
                else:
                    continue
            else:
                break

        return tab_name, medicine_set

    # 新增自費處方
    def add_prescript_tab(self, medicine_set=None):
        if medicine_set in (1, 11):  # 健保處方頁  1=健保 11=加強照護
            self.tab_list[0] = ins_prescript_record.InsPrescriptRecord(
                self, self.database, self.system_settings, self.case_key, 1, self.call_from)
            self.ui.tabWidget_prescript.addTab(self.tab_list[0], '健保')
            self.ui.tabWidget_prescript.tabBar().setTabButton(
                self.ui.tabWidget_prescript.indexOf(self.tab_list[0]), QtWidgets.QTabBar.RightSide, None
            )

            if self.medical_record['TreatType'] in nhi_utils.IMPROVE_CARE_TREAT + ['小兒氣喘', '小兒腦性麻痺']:
                medicine_set = 11
                self.tab_list[medicine_set] = ins_care_record.InsCareRecord(
                    self, self.database, self.system_settings, self.case_key, medicine_set)
                self.tab_list[medicine_set].refresh_prescript()
                self.ui.tabWidget_prescript.addTab(self.tab_list[medicine_set], '加強照護')
                self.ui.tabWidget_prescript.tabBar().setTabButton(
                    self.ui.tabWidget_prescript.indexOf(
                        self.tab_list[medicine_set]), QtWidgets.QTabBar.RightSide, None
                )

            return

        set_current_tab = False
        clear_prescript = False
        if not medicine_set:  # 新增自費處方按鈕
            medicine_set = 2
            set_current_tab = True
            clear_prescript = True

        tab_name = '自費{0}'.format(medicine_set-1)
        if self._tab_exists(tab_name):
            tab_name, medicine_set = self._get_new_tab(self.max_tab)

        if not tab_name:
            return

        current_tab = None
        new_tab = self_prescript_record.SelfPrescriptRecord(
            self, self.database, self.system_settings, self.case_key, medicine_set, self.call_from)

        for i in range(1, self.max_tab):
            if tab_name == '自費{0}'.format(i):
                self.tab_list[i] = new_tab
                self.tab_list[i].append_null_medicine()
                current_tab = self.tab_list[i]

        if current_tab is None:
            return

        self.ui.tabWidget_prescript.addTab(current_tab, tab_name)
        if clear_prescript:
            current_tab.tableWidget_prescript.setRowCount(0)
            current_tab.append_null_medicine()

        if set_current_tab:
            self.ui.tabWidget_prescript.setCurrentWidget(current_tab)

        return current_tab

    # 檢查是否開啟tab
    def _tab_exists(self, tab_text):
        if self.ui.tabWidget_prescript.count() <= 0:
            return False

        for i in range(self.ui.tabWidget_prescript.count()):
            if self.ui.tabWidget_prescript.tabText(i) == tab_text:
                return True

        return False

    def _read_recently_history(self):
        if self.patient_record is None:
            return

        self.tab_medical_record_recently_history = \
            medical_record_recently_history.MedicalRecordRecentlyHistory(
                self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_past_record.addTab(self.tab_medical_record_recently_history, '最近病歷')

    def _read_fees(self):
        self.tab_medical_record_fees = medical_record_fees.MedicalRecordFees(
            self, self.database, self.system_settings, self.case_key, self.call_from)
        self.ui.tabWidget_past_record.addTab(self.tab_medical_record_fees, '批價明細')
        self.calculate_ins_fees()

    # 新增自費病歷
    def save_new_self_medical_record(self):
        self.record_saved = True
        self._set_doctor()

        case_key = self._insert_medical_record()
        self.update_diagnosis_data(case_key)
        self.tab_registration.case_key = case_key
        self.tab_registration.data_changed = True
        self.tab_registration.save_record()
        self.update_cash_fees_data(case_key)
        self._set_doctor_done(case_key)
        self._set_charge_done(case_key)

        self._insert_wait_record(case_key)
        self._set_wait_done(case_key)

        for medicine_set, tab_prescript in zip(range(1, self.max_tab+1), self.tab_list):
            if tab_prescript is not None:
                try:
                    tab_prescript.case_key = case_key
                except RuntimeError:  # 關閉處方頁, 刪除整個處方
                    self.remove_prescript(medicine_set)
            else:
                self.remove_prescript(medicine_set)

        self.save_prescript()

        if self.sender().text() == '存檔列印':
            self._print(case_key)
        elif self.sender().text() == '存檔後選擇列印處方':
            self._print_prescript(case_key, '選擇列印')
        elif self.sender().text() == '存檔後選擇列印費用收據':
            self._print_receipt(case_key, '選擇列印')
        elif self.sender().text() == '存檔後選擇列印其他收據':
            self._print_misc(case_key, '選擇列印')

        socket_client = udp_socket_client.UDPSocketClient()
        socket_client.send_data('醫師看診作業完成')

        self.close_all()
        self.close_tab()

    # 新增自費病歷
    def _insert_medical_record(self):
        fields = [
            'PatientKey', 'CaseDate',
        ]

        data = [
            self.patient_key,
            self.tab_registration.lineEdit_case_date.text(),
        ]
        case_key = self.database.insert_record('cases', fields, data)

        return case_key

    # 新增自費病歷候診名單
    def _insert_wait_record(self, case_key):
        fields = ['CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Period',
                  'Room', 'RegistNo', 'Doctor', 'Massager']
        data = [
            case_key,
            self.tab_registration.lineEdit_case_date.text(),
            self.patient_key,
            self.tab_registration.lineEdit_name.text(),
            self.tab_registration.comboBox_visit.currentText(),
            self.tab_registration.comboBox_reg_type.currentText(),
            self.tab_registration.comboBox_treat_type.currentText(),
            self.tab_registration.comboBox_share_type.currentText(),
            self.tab_registration.comboBox_ins_type.currentText(),
            self.tab_registration.comboBox_period.currentText(),
            self.tab_registration.comboBox_room.currentText(),
            self.tab_registration.lineEdit_regist_no.text(),
            self.tab_registration.comboBox_doctor.currentText(),
            self.tab_registration.comboBox_massager.currentText(),
        ]
        self.database.insert_record('wait', fields, data)

    # 病歷存檔
    def save_medical_record(self):
        if self.call_from == '新增自費病歷':
            self.save_new_self_medical_record()
            return

        if (self.ins_type == '健保' and
                self.tab_registration.comboBox_ins_type.currentText() == '健保'):
            treat_type = self.tab_registration.ui.comboBox_treat_type.currentText()
            special_code = self.tab_registration.ui.lineEdit_special_code.text()
            disease_code1 = string_utils.xstr(self.ui.lineEdit_disease_code1.text())
            disease_code2 = string_utils.xstr(self.ui.lineEdit_disease_code2.text())
            disease_code3 = string_utils.xstr(self.ui.lineEdit_disease_code3.text())
            treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())
            pres_days = number_utils.get_integer(self.tab_list[0].ui.comboBox_pres_days.currentText())
            packages = number_utils.get_integer(self.tab_list[0].ui.comboBox_package.currentText())
            instruction = self.tab_list[0].ui.comboBox_instruction.currentText()

            table_widget_prescript = self.tab_list[0].ui.tableWidget_prescript
            table_widget_treat = self.tab_list[0].ui.tableWidget_treat

            if self.tab_list[11] is not None:
                table_widget_ins_care = self.tab_list[11].ui.tableWidget_prescript
            else:
                table_widget_ins_care = None

            record_check = medical_record_check.MedicalRecordCheck(
                self, self.database, self.system_settings, self.call_from,
                self.medical_record, self.patient_record,
                treat_type,
                disease_code1, disease_code2, disease_code3,
                special_code,
                treatment, pres_days, packages, instruction,
                table_widget_prescript,
                table_widget_treat,
                table_widget_ins_care,
            )

            check_ok = record_check.check_medical_record()
            record_check.deleteLater()

            if not check_ok:
                return

        if not self._check_self_pres_days():
            return

        if not self._check_self_dosage():
            return

        if not self._check_fees():  # 檢查批價
            return

        self.record_saved = True
        self._set_necessary_fields()

        set_doctor_done = False
        if self.call_from == '醫師看診作業':
            set_doctor_done = True

        self.update_medical_record(set_doctor_done)

        if self.sender().text() == '存檔列印':
            self._print(self.case_key)
        elif self.sender().text() == '存檔後選擇列印處方':
            self._print_prescript(self.case_key, '選擇列印')
        elif self.sender().text() == '存檔後選擇列印費用收據':
            self._print_receipt(self.case_key, '選擇列印')
        elif self.sender().text() == '存檔後選擇列印其他收據':
            self._print_misc(self.case_key, '選擇列印')

        card = string_utils.xstr(self.medical_record['Card'])
        xcard = string_utils.xstr(self.medical_record['XCard'])
        if ((self.ins_type == '健保') and
                (self.call_from == '醫師看診作業') and
                (self.system_settings.field('產生醫令簽章位置') == '診療') and
                (self.system_settings.field('使用讀卡機') == 'Y') and
                (card not in nhi_utils.ABNORMAL_CARD) and
                (xcard not in nhi_utils.ABNORMAL_CARD) and
                (card != '欠卡')):
            ic_card = cshis.CSHIS(self.database, self.system_settings)
            ic_card.write_ic_medical_record(self.case_key, cshis_utils.NORMAL_CARD)

        self.close_all()
        self.close_tab()

    def _check_self_pres_days(self):
        ins_pres_days = 0
        for tab_index in range(self.ui.tabWidget_prescript.count()):
            current_tab = self.ui.tabWidget_prescript.widget(tab_index)
            tab_name = self.ui.tabWidget_prescript.tabText(tab_index)
            if tab_name == '健保':
                ins_pres_days = number_utils.get_integer(current_tab.comboBox_pres_days.currentText())
                break

        for tab_index in range(self.ui.tabWidget_prescript.count()):
            current_tab = self.ui.tabWidget_prescript.widget(tab_index)
            tab_name = self.ui.tabWidget_prescript.tabText(tab_index)
            if tab_name in ['健保', '加強照護']:
                continue

            self_pres_days = number_utils.get_integer(current_tab.comboBox_pres_days.currentText())
            table_widget_prescript = current_tab.tableWidget_prescript
            for row_no in range(table_widget_prescript.rowCount()):
                medicine_name = table_widget_prescript.item(
                    row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']
                )
                if medicine_name is None:
                    continue

                medicine_name = medicine_name.text()
                if '混合(科藥+自費藥' in medicine_name and self_pres_days != ins_pres_days:
                    system_utils.show_message_box(
                        QMessageBox.Critical,
                        '給藥天數錯誤',
                        '''
                            <font size="4" color="red">
                              <b>
                               {tab_name}(混合科藥+自費藥)給藥天數與健保不符! 請更正.
                               </b>
                            </font>
                        '''.format(tab_name=tab_name),

                        '健保給藥天數為{ins_pres_days}天, {tab_name}給藥天數為{self_pres_days}天.'.format(
                            tab_name=tab_name,
                            ins_pres_days=ins_pres_days,
                            self_pres_days=self_pres_days,
                        )
                    )
                    return False

        return True

    # 檢查自費劑量空白 (無單價不檢查) 2019.12.10
    def _check_self_dosage(self):
        for tab_index in range(self.ui.tabWidget_prescript.count()):
            current_tab = self.ui.tabWidget_prescript.widget(tab_index)
            tab_name = self.ui.tabWidget_prescript.tabText(tab_index)
            if tab_name in ['健保', '加強照護']:
                continue

            table_widget_prescript = current_tab.tableWidget_prescript
            for row_no in range(table_widget_prescript.rowCount()):
                dosage = table_widget_prescript.item(
                    row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Dosage']
                )
                price = table_widget_prescript.item(
                    row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['Price']
                )
                if dosage is not None and dosage.text() != '':
                    continue

                if price is None or price.text() in ['', '0.0']:
                    continue

                medicine_name = table_widget_prescript.item(
                    row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineName']
                )
                if medicine_name is not None:
                    medicine_name = medicine_name.text()
                else:
                    medicine_name = '(處方空白)'

                system_utils.show_message_box(
                    QMessageBox.Critical,
                    '劑量空白',
                    '''
                        <font size="4" color="red">
                          <b>
                           {tab_name}: {medicine_name} 劑量空白! 請更正.
                           </b>
                        </font>
                    '''.format(
                        tab_name=tab_name,
                        medicine_name=medicine_name,
                    ),

                    '請輸入劑量.'
                )
                return False

        return True

    def _check_fees(self):
        if self.call_from == '醫師看診作業':
            return True

        old_total_fee = number_utils.get_integer(
            charge_utils.get_table_widget_item_fee(self.tab_medical_record_fees.ui.tableWidget_cash_fees, 14, 0)
        )
        new_total_fee = self.tab_medical_record_fees.get_total_fee()
        if new_total_fee != old_total_fee:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('批價有變更')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                       本次病歷有變更, 原現金應收為${old_total_fee}, <br>
                       經本系統檢查, 病歷異動批價金額為${new_total_fee}, 請更正.
                       </b>
                    </font>
                '''.format(
                    old_total_fee=old_total_fee,
                    new_total_fee=new_total_fee,
                )
            )
            msg_box.setInformativeText("請選擇以下的選項.")
            msg_box.addButton(QPushButton("不理會, 繼續存檔"), QMessageBox.NoRole)
            msg_box.addButton(QPushButton("重新批價後存檔"), QMessageBox.YesRole)
            calculate_fee = msg_box.exec_()
            if calculate_fee:
                self.tab_medical_record_fees.ui.checkBox_disable_calculate.setChecked(False)
                self.tab_medical_record_fees.calculate_fees()

        return True

    def _print(self, case_key=None):
        if case_key is None:
            case_key = self.case_key

        print_mode = '系統設定'
        self._print_prescript(case_key, print_mode)
        self._print_receipt(case_key, print_mode)
        self._print_misc(case_key, print_mode)

    # 列印處方
    def _print_prescript(self, case_key, print_mode):
        print_prescript = print_prescription.PrintPrescription(
            self, self.database, self.system_settings, case_key, print_mode)
        print_prescript.print()

        del print_prescript

    # 列印收據
    def _print_receipt(self, case_key, print_mode):
        print_charge = print_receipt.PrintReceipt(
            self, self.database, self.system_settings, case_key, print_mode)
        print_charge.print()

        del print_charge

    # 列印其他收據
    def _print_misc(self, case_key, print_mode):
        print_other = print_misc.PrintMisc(
            self, self.database, self.system_settings, case_key, print_mode)
        print_other.print()
        del print_other

    # 設定必要欄位
    def _set_necessary_fields(self):
        if self.call_from == '醫師看診作業':  # 所有病歷都要設定
            self._set_doctor()

        if self.ins_type == '健保':
            self._set_treatment_and_course()

    # 設定主治醫師姓名
    def _set_doctor(self):
        self.tab_registration.ui.comboBox_doctor.setCurrentText(self.system_settings.field('使用者'))

    # 設定就醫類別及療程
    def _set_treatment_and_course(self):
        if self.tab_registration.ui.comboBox_treat_type.currentText() in nhi_utils.CARE_TREAT:
            self.tab_registration.ui.comboBox_course.setCurrentText('')
            return

        treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())
        course = number_utils.get_integer(self.tab_registration.ui.comboBox_course.currentText())
        if treatment in nhi_utils.INS_TREAT:
            self.tab_registration.ui.comboBox_treat_type.setCurrentText(treatment)
            if course <= 0:
                self.tab_registration.ui.comboBox_course.setCurrentText('1')
        elif treatment == '':
            self.tab_registration.ui.comboBox_treat_type.setCurrentText('內科')
            if course >= 1:
                self.tab_registration.ui.comboBox_course.setCurrentText(None)

    # 病歷存檔
    def update_medical_record(self, set_doctor_done=False):
        self.update_diagnosis_data()
        self.update_treat_data()
        self.update_ins_fees_data()
        self.update_cash_fees_data()
        self.tab_registration.save_record()
        self.save_prescript()

        if set_doctor_done:
            self._set_doctor_done()
            self._set_charge_done()
            self._set_wait_done()
            socket_client = udp_socket_client.UDPSocketClient()
            socket_client.send_data('醫師看診作業完成')

    def _set_doctor_done(self, case_key=None):
        if case_key is None:
            case_key = self.case_key

        self.database.exec_sql(
            'UPDATE cases SET DoctorDone = "True", DoctorDate = "{0}" WHERE CaseKey = {1}'.format(
                date_utils.now_to_str(), case_key))

    def _set_charge_done(self, case_key=None):
        if self.system_settings.field('自動完成批價作業') != 'Y':
            return

        if case_key is None:
            case_key = self.case_key

        sql = '''
            UPDATE cases 
            SET 
                ChargeDone = "True", 
                ChargeDate = "{charge_date}", 
                ChargePeriod = "{charge_period}",
                Cashier = "{cashier}"
            WHERE 
                CaseKey = {case_key}
        '''.format(
            charge_date=date_utils.now_to_str(),
            charge_period=registration_utils.get_current_period(self.system_settings),
            cashier=self.system_settings.field('使用者'),
            case_key=case_key,
        )

        self.database.exec_sql(sql)

    def _set_wait_done(self, case_key=None):
        if case_key is None:
            case_key = self.case_key

        if self.system_settings.field('自動完成批價作業') == 'Y':
            sql = '''
                UPDATE wait 
                SET 
                    DoctorDone = "True", ChargeDone = "True" 
                WHERE CaseKey = {case_key}
            '''.format(
                case_key=case_key
            )
        else:
            sql = 'UPDATE wait SET DoctorDone = "True" WHERE CaseKey = {0}'.format(case_key)

        self.database.exec_sql(sql)

    # 診斷資料存檔
    def update_diagnosis_data(self, case_key=None):
        if case_key is None:
            case_key = self.case_key

        fields = [
            'Symptom', 'Tongue', 'Pulse', 'Remark',
            'DiseaseCode1', 'DiseaseCode2', 'DiseaseCode3',
            'DiseaseName1', 'DiseaseName2', 'DiseaseName3',
            'Distincts', 'Cure',
            'Treatment', 'Reference',
        ]

        treatment = None
        if self.ins_type == '健保':
            treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())

        if self.ui.checkBox_reference.isChecked():
            reference = 'True'
        else:
            reference = 'False'

        symptom = self.ui.textEdit_symptom.toPlainText()
        symptom = string_utils.remove_bom(symptom)
        data = [
            symptom,
            self.ui.textEdit_tongue.toPlainText(),
            self.ui.textEdit_pulse.toPlainText(),
            self.ui.textEdit_remark.toPlainText(),
            self.ui.lineEdit_disease_code1.text(),
            self.ui.lineEdit_disease_code2.text(),
            self.ui.lineEdit_disease_code3.text(),
            self.ui.lineEdit_disease_name1.text(),
            self.ui.lineEdit_disease_name2.text(),
            self.ui.lineEdit_disease_name3.text(),
            self.ui.lineEdit_distinguish.text(),
            self.ui.lineEdit_cure.text(),
            treatment, reference,
        ]

        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

    # 處置資料存檔
    def update_treat_data(self):
        fields = [
            'Package1', 'PresDays1', 'Instruction1',
            'Treatment',
        ]

        package1, pres_days1, instruction1 = None, None, None
        treatment = None
        if self.ins_type == '健保':
            package1 = string_utils.xstr(self.tab_list[0].ui.comboBox_package.currentText())
            pres_days1 = string_utils.xstr(self.tab_list[0].ui.comboBox_pres_days.currentText())
            instruction1 = string_utils.xstr(self.tab_list[0].ui.comboBox_instruction.currentText())
            treatment = string_utils.xstr(self.tab_list[0].combo_box_treatment.currentText())

        data = [
            package1, pres_days1, instruction1,
            treatment,
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    # 健保批價資料存檔
    def update_ins_fees_data(self):
        fields = [
            'DiagFee', 'InterDrugFee', 'PharmacyFee',
            'AcupunctureFee', 'MassageFee', 'DislocateFee',
            'InsTotalFee', 'DiagShareFee', 'DrugShareFee', 'InsApplyFee', 'AgentFee',
        ]

        self.calculate_ins_fees()
        data = [
            self.tab_medical_record_fees.ui.tableWidget_ins_fees.item(i, 0).text()
            for i in range(len(fields))
        ]

        self.database.update_record('cases', fields, 'CaseKey', self.case_key, data)

    # 自費批價資料存檔
    def update_cash_fees_data(self, case_key=None):
        if case_key is None:
            case_key = self.case_key

        fields = [
            'RegistFee', 'SDiagShareFee', 'SDrugShareFee', 'DepositFee', 'RefundFee',
            'SDiagFee', 'SDrugFee', 'SHerbFee', 'SExpensiveFee',
            'SAcupunctureFee', 'SMassageFee', 'SMaterialFee',
            'SelfTotalFee', 'DiscountFee', 'TotalFee', 'ReceiptFee',
        ]

        data = [
            self.tab_medical_record_fees.ui.tableWidget_cash_fees.item(i, 0).text()
            for i in range(len(fields))
        ]
        fields.append('DiscountRate')
        data.append(self.tab_medical_record_fees.ui.spinBox_discount.value())

        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

        if self.system_settings.field('自動完成批價作業') != 'Y':
            return

        receipt_fee = (
                number_utils.get_integer(self.tab_medical_record_fees.ui.tableWidget_cash_fees.item(2, 0).text()) +
                number_utils.get_integer(self.tab_medical_record_fees.ui.tableWidget_cash_fees.item(15, 0).text())
        )

        total_fee = (
                number_utils.get_integer(self.tab_medical_record_fees.ui.tableWidget_ins_fees.item(8, 0).text()) +
                number_utils.get_integer(self.tab_medical_record_fees.ui.tableWidget_cash_fees.item(14, 0).text())
        )

        if receipt_fee < total_fee:
            self._write_debt(case_key, receipt_fee, total_fee)

    def _write_debt(self, case_key, receipt_fee, total_fee):
        debt_fee = total_fee - receipt_fee
        message = '<h3><font color="red">此人應收金額為{total_fee}, 實收金額為 {receipt_fee}, 是否欠款 {debt_fee} 元?</font></h3>'.format(
            total_fee=total_fee,
            receipt_fee=receipt_fee,
            debt_fee=debt_fee,
        )

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('批價存檔')
        msg_box.setText(message)
        msg_box.setInformativeText("注意！存檔後, 將產生一筆欠款資料!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        save_debt = msg_box.exec_()
        if not save_debt:
            return

        fields = [
            'CaseKey', 'PatientKey', 'DebtType', 'Name', 'CaseDate', 'Period', 'Doctor', 'Fee'
        ]

        data = [
            case_key,
            self.patient_key,
            '批價欠款',
            string_utils.xstr(self.medical_record['Name']),
            self.tab_registration.lineEdit_case_date.text(),
            self.tab_registration.comboBox_period.currentText(),
            self.tab_registration.comboBox_doctor.currentText(),
            debt_fee,
        ]
        self.database.insert_record('debt', fields, data)

        fields = ['DebtFee']
        data = [debt_fee]
        self.database.update_record('cases', fields, 'CaseKey', case_key, data)

    def save_prescript(self):
        for medicine_set, tab_prescript in zip(range(1, self.max_tab+1), self.tab_list):
            if tab_prescript is not None:
                try:
                    tab_prescript.save_prescript()
                except RuntimeError:  # 關閉處方頁, 刪除整個處方
                    self.remove_prescript(medicine_set)
            else:
                self.remove_prescript(medicine_set)

    def remove_prescript(self, medicine_set):
        sql = '''
            DELETE FROM prescript WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1})
        '''.format(self.case_key, medicine_set)
        self.database.exec_sql(sql)
        sql = '''
            DELETE FROM dosage WHERE 
            (CaseKey = {0}) AND (MedicineSet = {1})
        '''.format(self.case_key, medicine_set)
        self.database.exec_sql(sql)

    # 健保重新批價
    def calculate_ins_fees(self):
        try:
            self.tab_medical_record_fees.calculate_ins_fees()
        except AttributeError:
            pass

    # 健保重新批價
    def calculate_self_fees(self):
        try:
            self.tab_medical_record_fees.calculate_self_fees(
                self.tab_list,
                self.tab_medical_record_fees.ui.checkBox_disable_calculate,
            )
        except AttributeError:
            pass

    # 顯示拷貝過去病歷視窗
    def _open_past_history(self):
        dialog = dialog_medical_record_past_history.DialogMedicalRecordPastHistory(
            self, self.database, self.system_settings, self.case_key,
            self.patient_key, '病歷登錄'
        )

        dialog.exec_()
        dialog.deleteLater()

    # 顯示參考病歷
    def _open_medical_record_reference(self):
        dialog = dialog_medical_record_reference.DialogMedicalRecordReference(
            self, self.database, self.system_settings, self.case_key,
        )

        dialog.exec_()
        dialog.deleteLater()

    def _text_edit_key_press(self, event):
        if self.ui.textEdit_symptom.hasFocus():
            diagnostic_type = '主訴'
            sender = self.ui.textEdit_symptom
        elif self.ui.textEdit_tongue.hasFocus():
            diagnostic_type = '舌診'
            sender = self.ui.textEdit_tongue
        elif self.ui.textEdit_pulse.hasFocus():
            diagnostic_type = '脈象'
            sender = self.ui.textEdit_pulse
        elif self.ui.textEdit_remark.hasFocus():
            diagnostic_type = '備註'
            sender = self.ui.textEdit_remark
        else:
            diagnostic_type = '主訴'
            sender = self.ui.textEdit_symptom

        key = event.key()
        char = event.text()
        self.input_code += char

        if key in [
            Qt.Key_Enter, Qt.Key_Return,
            Qt.Key_Escape,
            Qt.Key_Space, Qt.Key_Comma,
            Qt.Key_Up, Qt.Key_Down, Qt.Key_Left, Qt.Key_Right,
        ]:
            if key in [Qt.Key_Enter, Qt.Key_Return]:
                self.input_code = self.input_code[:-1]
                if self.input_code != '':
                    self._query_diagnostic_dict(event, sender, self.input_code, diagnostic_type)
                else:
                    return QtWidgets.QTextEdit.keyPressEvent(sender, event)

            self.input_code = ''
        elif key in [Qt.Key_Backspace]:
            if len(self.input_code) > 1:
                self.input_code = self.input_code[:-2]
            else:
                self.input_code = ''

        if key not in [Qt.Key_Enter, Qt.Key_Return]:
            return QtWidgets.QTextEdit.keyPressEvent(sender, event)

    def _query_diagnostic_dict(self, event, sender, input_code, diagnostic_type):
        clean_input_code = string_utils.replace_ascii_char(['\\', '"', '\''], input_code)
        order_type = '''
            ORDER BY LENGTH(ClinicName), CAST(CONVERT(`ClinicName` using big5) AS BINARY)
        '''
        if self.system_settings.field('詞庫排序') == '點擊率':
            order_type = 'ORDER BY HitRate DESC'

        sql = '''
            SELECT * FROM clinic
            WHERE
                ClinicType = "{clinic_type}" AND
                InputCode LIKE "{input_code}%"
            GROUP BY ClinicName 
            {order_type}
        '''.format(
            clinic_type=diagnostic_type,
            input_code=clean_input_code,
            order_type=order_type,
        )

        rows = self.database.select_record(sql)
        row_count = len(rows)

        if row_count <= 0:
            return QtWidgets.QTextEdit.keyPressEvent(sender, event)
        elif row_count == 1:
            self.insert_text(sender, string_utils.xstr(rows[0]['ClinicName']), input_code)
            clinic_key = string_utils.xstr(rows[0]['ClinicKey'])
            db_utils.increment_hit_rate(self.database, 'clinic', 'ClinicKey', clinic_key)
        else:
            dialog = dialog_diagnostic_picker.DialogDiagnosticPicker(
                self, self.database, self.system_settings, sender, diagnostic_type, clean_input_code,
            )

            if dialog.exec_():
                clinic_name = dialog.clinic_name + ' '
                self.insert_text(sender, clinic_name, dialog.input_code)

            dialog.close_all()
            dialog.deleteLater()

    @staticmethod
    def insert_text(sender, text, input_code):
        cursor = sender.textCursor()
        cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.MoveAnchor, len(input_code))
        sender.setTextCursor(cursor)
        sender.insertPlainText(text)

        cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, len(input_code))
        cursor.removeSelectedText()

    def _medical_record_precheck(self):
        self._check_pres_days()

    # 檢查上次健保給藥是否服藥完畢
    def _check_pres_days(self):
        message = registration_utils.check_prescription_finished(
            self.database, self.case_key, self.patient_key
        )
        if message is not None:
            system_utils.show_message_box(
                QMessageBox.Warning,
                '檢查結果提醒',
                '<h3><font color="red">{0}</font></h3>'.format(message),
                '請注意用藥重複.'
            )

    # 新增自費
    def _append_new_self_medical_record(self):
        self.parent.append_self_medical_record(
            self.case_key,
            self.patient_key,
            self.patient_record['Name'],
        )

    # 清除病歷
    def clear_medical_record(self):
        self.clear_medical_record_option = False

        msg_box = dialog_utils.get_message_box(
            '清除病歷', QMessageBox.Warning,
            '<font size="4" color="red"><b>確定清除此病歷? (包含望聞問切及處方資料)</b></font>',
            '注意！病歷清除後, 若不存檔, 還可復原!'
        )
        clear_medical_record = msg_box.exec_()
        if not clear_medical_record:
            return

        self.clear_medical_record_option = True
        self.ui.textEdit_symptom.setText(None)
        self.ui.textEdit_tongue.setText(None)
        self.ui.textEdit_pulse.setText(None)
        self.ui.textEdit_remark.setText(None)

        self.ui.lineEdit_disease_code1.setText(None)
        self.ui.lineEdit_disease_code2.setText(None)
        self.ui.lineEdit_disease_code2.setText(None)
        self.ui.lineEdit_distinguish.setText(None)
        self.ui.lineEdit_cure.setText(None)

    def _insert_today(self):
        cursor = self.ui.textEdit_symptom.textCursor()
        cursor.movePosition(
            QtGui.QTextCursor.Left,
            QtGui.QTextCursor.MoveAnchor,
            len(self.ui.textEdit_symptom.toPlainText())
        )
        self.ui.textEdit_symptom.setTextCursor(cursor)

        today = date_utils.west_date_to_nhi_date(datetime.date.today().strftime("%Y-%m-%d"), '.')
        self.insert_text(self.ui.textEdit_symptom, today + ' ', '')
        self.ui.textEdit_symptom.setFocus(True)

    def _symptom_selection_changed(self):
        selected_text = self.ui.textEdit_symptom.textCursor().selectedText().strip()

        if selected_text == '':
            enabled = False
        else:
            enabled = True

        self.ui.toolButton_add_symptom_dict.setEnabled(enabled)

    def _add_symptom_dict(self):
        selected_text = self.ui.textEdit_symptom.textCursor().selectedText().strip()
        dialog = dialog_add_diagnostic_dict.DialogAddDiagnosticDict(
            self, self.database, self.system_settings, '主訴', selected_text,
        )
        dialog.exec_()
        dialog.deleteLater()

    def _open_reservation(self):
        doctor = self.tab_registration.ui.comboBox_doctor.currentText()
        self.parent.open_reservation(None, self.patient_key, doctor)
