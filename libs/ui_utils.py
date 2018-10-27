import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5 import uic
from libs import  nhi_utils

ICON_NO = QtGui.QIcon('./icons/gtk-no.svg')
ICON_OK = QtGui.QIcon('./icons/gtk-ok.svg')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))

UI_PATH = "ui"
CONFIG_FILE = "pymedical.conf"

UI_PY_MEDICAL = "pymedical.ui"
UI_LOGIN = "login.ui"
UI_LOGIN_STATISTICS = "login_statistics.ui"

UI_MEDICAL_RECORD = "medical_record.ui"
UI_INS_PRESCRIPT_RECORD = "ins_prescript_record.ui"
UI_SELF_PRESCRIPT_RECORD = "self_prescript_record.ui"
UI_MEDICAL_RECORD_RECENTLY_HISTORY = "medical_record_recently_history.ui"
UI_MEDICAL_RECORD_REGISTRATION = "medical_record_registration.ui"
UI_MEDICAL_RECORD_FEES = "medical_record_fees.ui"
UI_MEDICAL_RECORD_LIST = "medical_record_list.ui"

UI_PATIENT_LIST = "patient_list.ui"
UI_PATIENT = "patient.ui"

UI_RETURN_CARD = "return_card.ui"
UI_REGISTRATION = "registration.ui"
UI_RESERVATION = "reservation.ui"
UI_TEMPLATE = "template.ui"
UI_WAITING_LIST = "waiting_list.ui"
UI_CASHIER = "cashier.ui"
UI_INCOME = "income.ui"
UI_DEBT = "debt.ui"

UI_INS_CHECK = "ins_check.ui"
UI_INS_APPLY = "ins_apply.ui"
UI_INS_APPLY_LIST = "ins_apply_list.ui"
UI_INS_APPLY_TAB = "ins_apply_tab.ui"
UI_INS_JUDGE = "ins_judge.ui"
UI_INS_APPLY_CALCULATED_DATA = "ins_apply_calculated_data.ui"
UI_INS_APPLY_TOTAL_FEE = "ins_apply_total_fee.ui"
UI_INS_CHECK_APPLY_FEE = "ins_check_apply_fee.ui"

UI_DOCTOR_NURSE_TABLE = "doctor_nurse_table.ui"

UI_CHECK_ERRORS = "check_errors.ui"
UI_CHECK_COURSE = "check_course.ui"
UI_CHECK_MEDICAL_RECORD_COUNT = "check_medical_record_count.ui"
UI_CHECK_PRESCRIPT_DAYS = "check_prescript_days.ui"
UI_CHECK_INS_DRUG = "check_ins_drug.ui"
UI_CHECK_INS_TREAT = "check_ins_treat.ui"

UI_CHARGE_SETTINGS = "charge_settings.ui"
UI_CHARGE_SETTINGS_NHI = "charge_settings_nhi.ui"
UI_CHARGE_SETTINGS_REGIST = "charge_settings_regist.ui"
UI_CHARGE_SETTINGS_SHARE = "charge_settings_share.ui"

UI_DIALOG_DIAGNOSIS = "dialog_diagnosis.ui"
UI_DIALOG_DISEASE = "dialog_disease.ui"
UI_DIALOG_INQUIRY = "dialog_inquiry.ui"
UI_DIALOG_IC_CARD = "dialog_ic_card.ui"
UI_DIALOG_INPUT_REGIST = "dialog_input_regist.ui"
UI_DIALOG_INPUT_DISCOUNT = "dialog_input_discount.ui"
UI_DIALOG_INPUT_SHARE = "dialog_input_share.ui"
UI_DIALOG_INPUT_NHI = "dialog_input_nhi.ui"
UI_DIALOG_INPUT_DIAGNOSTIC = "dialog_input_diagnostic.ui"
UI_DIALOG_INPUT_DISEASE = "dialog_input_disease.ui"
UI_DIALOG_INPUT_MEDICINE = "dialog_input_medicine.ui"
UI_DIALOG_INPUT_DRUG = "dialog_input_drug.ui"
UI_DIALOG_INPUT_USER = "dialog_input_user.ui"
UI_DIALOG_EDIT_DISEASE = "dialog_edit_disease.ui"
UI_DIALOG_MEDICAL_RECORD_LIST = "dialog_medical_record_list.ui"
UI_DIALOG_MEDICAL_RECORD_PAST_HISTORY = "dialog_medical_record_past_history.ui"
UI_DIALOG_MEDICINE = "dialog_medicine.ui"
UI_DIALOG_PAST_HISTORY = "dialog_past_history.ui"
UI_DIALOG_PATIENT = "dialog_patient.ui"
UI_DIALOG_PATIENT_LIST = "dialog_patient_list.ui"
UI_DIALOG_SETTINGS = "dialog_settings.ui"
UI_DIALOG_SYMPTOM = "dialog_symptom.ui"
UI_DIALOG_TONGUE = "dialog_tongue.ui"
UI_DIALOG_PULSE = "dialog_pulse.ui"
UI_DIALOG_REMARK = "dialog_remark.ui"
UI_DIALOG_DISTINGUISH = "dialog_distinguish.ui"
UI_DIALOG_CURE = "dialog_cure.ui"
UI_DIALOG_RETURN_CARD = "dialog_return_card.ui"
UI_DIALOG_IC_RECORD_UPLOAD = "dialog_ic_record_upload.ui"
UI_DIALOG_INCOME = "dialog_income.ui"
UI_DIALOG_DEBT = "dialog_debt.ui"
UI_DIALOG_RESERVATION_BOOKING = "dialog_reservation_booking.ui"

UI_DIALOG_INS_CHECK = "dialog_ins_check.ui"
UI_DIALOG_INS_APPLY = "dialog_ins_apply.ui"
UI_DIALOG_NURSE_SCHEDULE = "dialog_nurse_schedule.ui"
UI_DIALOG_COURSE_LIST = "dialog_course_list.ui"

UI_DICT_DIAGNOSTIC = "dict_diagnostic.ui"
UI_DICT_SYMPTOM = "dict_symptom.ui"
UI_DICT_TONGUE = "dict_tongue.ui"
UI_DICT_PULSE = "dict_pulse.ui"
UI_DICT_REMARK = "dict_remark.ui"
UI_DICT_DISEASE = "dict_disease.ui"
UI_DICT_DISTINGUISH = "dict_distinguish.ui"
UI_DICT_CURE = "dict_cure.ui"
UI_DICT_MEDICINE = "dict_medicine.ui"
UI_DICT_DRUG = "dict_drug.ui"
UI_DICT_TREAT = "dict_treat.ui"
UI_DICT_COMPOUND = "dict_compound.ui"

UI_USERS = "users.ui"
UI_CONVERT = "convert.ui"
UI_IC_RECORD_UPLOAD = 'ic_record_upload.ui'

THEME = ['Fusion', 'Windows', 'Cleanlooks', 'gtk2', 'motif', 'plastic', 'cde', 'qt5-ct-style']
WIN32_THEME = ['Fusion', 'Windows', 'WindowsXP', 'WindowsVista']


# 載入 ui 檔
def load_ui_file(ui_file, self):
    try:
        return uic.loadUi(os.path.join(BASE_DIR, UI_PATH, ui_file), self)
    except:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('找不到ui檔')
        msg_box.setText("<font size='4' color='red'><b>找不到 {0}, 請檢查檔案是否存在.</b></font>".format(ui_file))
        msg_box.setInformativeText("請與本公司聯繫, 並告知上面的訊息.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()

        return None


def get_discount_type(database):
    discount_type = []
    sql = 'SELECT * from charge_settings where ChargeType = "掛號費優待"'
    rows = database.select_record(sql)
    for row in rows:
        discount_type.append(row['ItemName'])

    return [None] + nhi_utils.DISCOUNT + discount_type


# 設定 comboBox item
def set_combo_box(combobox, items, *args):
    combobox.setMaxVisibleItems(30)
    if items == '掛號優待':
        items = get_discount_type(args[0])
        args = []

    for arg in args:
        combobox.addItem(arg)

    for item in items:
        combobox.addItem(item)


# 設定輸入文字補全
def set_completer(database, sql, field, widget):
    rows = database.select_record(sql)
    completer_list = []
    for row in rows:
        completer_list.append(row[field])

    model = QtCore.QStringListModel()
    model.setStringList(completer_list)
    completer = QtWidgets.QCompleter()
    completer.setModel(model)
    widget.setCompleter(completer)

