#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

import re
import datetime

from libs import system_utils
from libs import ui_utils
from libs import validator_utils
from libs import patient_utils
from libs import string_utils
from libs import date_utils
from libs import number_utils
from libs import registration_utils


# 主視窗
class DialogReservationBooking(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogReservationBooking, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.reservation_date = args[2]
        self.period = args[3]
        self.doctor = args[4]
        self.reserve_no = args[5]
        self.patient_key = args[6]
        self.ui = None

        self._set_ui()
        self._set_validator()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_RESERVATION_BOOKING, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('確定')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.lineEdit_reservation_date.setText(self.reservation_date)
        self.ui.lineEdit_period.setText(self.period)
        self.ui.lineEdit_doctor.setText(self.doctor)
        self.ui.lineEdit_reserve_no.setText(self.reserve_no)
        ui_utils.set_completer(
            self.database,
            'SELECT Name FROM patient GROUP BY Name ORDER BY Name',
            'Name',
            self.ui.lineEdit_query
        )
        ui_utils.set_combo_box(self.ui.comboBox_source, ['現場預約', '初診預約'])
        self._clear_patient_data()
        self._set_patient_read_only(True)

        if self.patient_key is not None:
            self.ui.lineEdit_query.setText(string_utils.xstr(self.patient_key))
            self._query_patient()
            self.ui.label_query.setVisible(False)
            self.ui.lineEdit_query.setVisible(False)
            self.ui.pushButton_query.setVisible(False)
            self.ui.comboBox_source.setEnabled(False)

    def keyPressEvent(self, event):
        if event.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            return

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.pushButton_query.clicked.connect(self._query_patient)
        self.ui.lineEdit_query.returnPressed.connect(self._query_patient)
        self.ui.comboBox_source.currentTextChanged.connect(self._source_changed)
        self.ui.lineEdit_name.textChanged.connect(self._name_changed)
        self.ui.lineEdit_birthday.editingFinished.connect(self._validate_birthday)

    def _validate_birthday(self):
        west_date = date_utils.date_to_west_date(self.ui.lineEdit_birthday.text())
        self.ui.lineEdit_birthday.setText(west_date)

    def _set_validator(self):
        self.ui.lineEdit_birthday.setValidator(validator_utils.set_validator('日期格式'))

    def _name_changed(self):
        if self.ui.lineEdit_name.text().strip() == '':
            button_enabled = False
        else:
            button_enabled = True

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(button_enabled)

    def _clear_patient_data(self):
        self.ui.lineEdit_patient_key.setText(None)
        self.ui.lineEdit_name.setText(None)
        self.ui.lineEdit_birthday.setText(None)
        self.ui.lineEdit_id.setText(None)
        self.ui.lineEdit_telephone.setText(None)

    def _set_patient_read_only(self, set_read_only):
        self.ui.lineEdit_query.setEnabled(set_read_only)
        self.ui.pushButton_query.setEnabled(set_read_only)

        self.ui.lineEdit_patient_key.setReadOnly(True)
        self.ui.lineEdit_name.setReadOnly(set_read_only)
        self.ui.lineEdit_birthday.setReadOnly(set_read_only)
        self.ui.lineEdit_id.setReadOnly(set_read_only)
        self.ui.lineEdit_telephone.setReadOnly(set_read_only)

        if set_read_only:
            self.ui.lineEdit_query.setFocus()
        else:
            self.ui.lineEdit_name.setFocus()

    def accepted_button_clicked(self):
        reservation_date = self.ui.lineEdit_reservation_date.text()
        period = self.ui.lineEdit_period.text()
        doctor = self.ui.lineEdit_doctor.text()
        room = registration_utils.get_room(self.database, period, doctor)
        reserve_no = self.ui.lineEdit_reserve_no.text()

        if registration_utils.is_reservation_full(self.database, reservation_date, period, reserve_no, doctor):
            system_utils.show_message_box(
                QMessageBox.Critical,
                '預約已滿',
                '<font size="4" color="red"><b>在剛剛此時段已被網路預約者預約, 請選擇其他時段.</b></font>',
                '很不巧, 有網路的預約者已搶先預約.'
            )
            return

        fields = [
            'PatientKey', 'Name', 'ReserveDate', 'Period',
            'Room', 'Doctor', 'ReserveNo', 'Source', 'Registrar',
        ]

        source = self.ui.comboBox_source.currentText()
        if source == '初診預約':
            self._write_temp_patient()

        patient_key = self.ui.lineEdit_patient_key.text()
        name = self.ui.lineEdit_name.text()
        registrar = self.system_settings.field('使用者')

        data = [
            patient_key, name, reservation_date, period,
            room, doctor, reserve_no, source, registrar,
        ]

        self.database.insert_record('reserve', fields, data)

    # 寫入初診病患暫存檔
    def _write_temp_patient(self):
        fields = [
            'Name', 'ID', 'Birthday', 'PhoneNo',
        ]

        data = [
            self.ui.lineEdit_name.text(),
            self.ui.lineEdit_id.text(),
            self.ui.lineEdit_birthday.text(),
            self.ui.lineEdit_telephone.text(),
        ]

        last_row_id = self.database.insert_record('temp_patient', fields, data)
        self.ui.lineEdit_patient_key.setText(string_utils.xstr(last_row_id))

    # 開始查詢病患資料
    def _query_patient(self):
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
            self._set_patient_data(row)

        self.ui.lineEdit_query.clear()

    def _set_patient_data(self, rows):
        row = rows[0]
        patient_key = row['PatientKey']
        name = string_utils.xstr(row['Name'])  # 病歷號可能會跟網路初診病歷號重複
        telephone = string_utils.xstr(row['Telephone'])
        if telephone == '':
            telephone = string_utils.xstr(row['Cellphone'])

        self.ui.lineEdit_patient_key.setText(string_utils.xstr(patient_key))
        self.ui.lineEdit_name.setText(name)
        self.ui.lineEdit_birthday.setText(string_utils.xstr(row['Birthday']))
        self.ui.lineEdit_id.setText(string_utils.xstr(row['ID']))
        self.ui.lineEdit_telephone.setText(telephone)

        if not self._check_reservation_status(patient_key, name):
            if self.patient_key is not None:
                self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).animateClick()

    def _check_reservation_status(self, patient_key, name):
        if not self._check_reservation_duplicated(patient_key, name):
            return False

        if not self._check_reservation_limit(patient_key, name):
            return False

        if not self._check_reservation_missing_appointment(patient_key, name):
            return False

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)

        return True

    # 檢查重複預約
    def _check_reservation_duplicated(self, patient_key, name):
        is_ok = True
        if name == '休診':
            return is_ok

        start_date = '{0} 00:00:00'.format(self.reservation_date[:10])
        end_date = '{0} 23:59:59'.format(self.reservation_date[:10])
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate BETWEEN "{start_date}" AND "{end_date}" AND
                PatientKey = {patient_key} AND
                Name = "{name}"
        '''.format(
            start_date=start_date,
            end_date=end_date,
            patient_key=patient_key,
            name=name,
        )

        rows = self.database.select_record(sql)
        if len(rows) > 0:
            is_ok = False

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('已有預約')
            msg_box.setText("此人該日已有預約, 無法再次預約掛號.")
            msg_box.setInformativeText("無法重複預約掛號.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            self.ui.lineEdit_patient_key.setText(None)
            self.ui.lineEdit_name.setText(None)
            self.ui.lineEdit_birthday.setText(None)
            self.ui.lineEdit_id.setText(None)

        return is_ok

    # 檢查預約次數限制
    def _check_reservation_limit(self, patient_key, name):
        is_ok = True
        if name == '休診':
            return is_ok

        reservation_limit = number_utils.get_integer(self.system_settings.field('預約次數限制'))
        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate >= "{start_date}" AND
                Arrival = "False" AND
                PatientKey = {patient_key} AND
                Name = "{name}" AND
                Source != "網路初診預約"
        '''.format(
            start_date=start_date,
            patient_key=patient_key,
            name=name,
        )
        rows = self.database.select_record(sql)
        if len(rows) >= reservation_limit:
            is_ok = False

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('已有預約')
            msg_box.setText("此人預約已超過系統設定內, 預約次數{0}次的限制, 無法再次預約掛號.".format(reservation_limit))
            msg_box.setInformativeText("超過次數, 無法預約掛號.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            self.ui.lineEdit_patient_key.setText(None)
            self.ui.lineEdit_name.setText(None)
            self.ui.lineEdit_birthday.setText(None)
            self.ui.lineEdit_id.setText(None)

        return is_ok

    # 檢查爽約次數
    def _check_reservation_missing_appointment(self, patient_key, name):
        is_ok = True
        if name == '休診':
            return is_ok

        reservation_period = number_utils.get_integer(self.system_settings.field('爽約期間'))
        reservation_missing_appointment = number_utils.get_integer(self.system_settings.field('爽約次數'))

        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate >= "{today}" AND
                Arrival = "False" AND
                PatientKey = {patient_key} AND
                Name = "{name}"
        '''.format(
            today=datetime.datetime.now().strftime('%Y-%m-%d 00:00:00'),
            patient_key=patient_key,
            name=name,
        )
        rows = self.database.select_record(sql)
        reservation_count = len(rows)

        reservation_date = date_utils.str_to_date(self.reservation_date[:10])
        start_date = reservation_date - datetime.timedelta(days=reservation_period)
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveDate >= "{start_date}" AND
                Arrival = "False" AND
                PatientKey = {patient_key} AND
                Name = "{name}"
        '''.format(
            start_date=start_date,
            patient_key=patient_key,
            name=name,
        )
        rows = self.database.select_record(sql)
        total_absent = len(rows)
        absent = total_absent - reservation_count

        if absent > reservation_missing_appointment:
            is_ok = False

            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('預約警告')
            msg_box.setText("此人預約已超過系統設定內, {0}天內預約超過{0}次的限制, 無法再次預約掛號.".format(
                reservation_period, reservation_missing_appointment))
            msg_box.setInformativeText("超過次數, 無法預約掛號.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            self._clear_patient_data()

        return is_ok

    def _source_changed(self):
        current_text = self.ui.comboBox_source.currentText()
        self._clear_patient_data()
        if current_text == '初診預約':
            set_read_only = False
            last_temp_patient_key = self.database.get_last_auto_increment_key('temp_patient')
            self.ui.lineEdit_patient_key.setText(string_utils.xstr(last_temp_patient_key))
        else:
            set_read_only = True

        self._set_patient_read_only(set_read_only)

