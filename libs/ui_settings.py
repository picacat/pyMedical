import os
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5 import uic

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))

UI_PATH = "ui"
CONFIG_FILE = "pymedical.conf"

UI_PY_MEDICAL = "pymedical.ui"

UI_INS_PRESCRIPT_RECORD = "ins_prescript_record.ui"
UI_MEDICAL_RECORD = "medical_record.ui"
UI_MEDICAL_RECORD_RECENTLY_HISTORY = "medical_record_recently_history.ui"
UI_MEDICAL_RECORD_LIST = "medical_record_list.ui"
UI_PATIENT_LIST = "patient_list.ui"
UI_PATIENT = "patient.ui"
UI_RETURN_CARD = "return_card.ui"
UI_REGISTRATION = "registration.ui"
UI_TEMPLATE = "template.ui"
UI_WAITING_LIST = "waiting_list.ui"

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
UI_DIALOG_EDIT_DISEASE = "dialog_edit_disease.ui"
UI_DIALOG_MEDICAL_RECORD_LIST = "dialog_medical_record_list.ui"
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

UI_DICT_DIAGNOSTIC = "dict_diagnostic.ui"
UI_DICT_SYMPTOM = "dict_symptom.ui"
UI_DICT_TONGUE = "dict_tongue.ui"
UI_DICT_PULSE = "dict_pulse.ui"
UI_DICT_REMARK = "dict_remark.ui"
UI_DICT_DISEASE = "dict_disease.ui"
UI_DICT_DISTINGUISH = "dict_distinguish.ui"
UI_DICT_CURE = "dict_cure.ui"
UI_DICT_MEDICINE = "dict_medicine.ui"

UI_CONVERT = "convert.ui"

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


def _get_discount_type(database):
    discount_type = [None]
    sql = 'SELECT * from charge_settings where ChargeType = "掛號費優待"'
    rows = database.select_record(sql)
    for row in rows:
        discount_type.append(row['ItemName'])

    return discount_type


# 設定 comboBox item
def set_combo_box(combobox, items, *args):
    if items == '掛號優待':
        items = _get_discount_type(args[0])
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

