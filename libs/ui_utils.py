import os
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
from PyQt5 import uic
from libs import nhi_utils
from libs import string_utils

ICON_NO = QtGui.QIcon('./icons/gtk-no.svg')
ICON_OK = QtGui.QIcon('./icons/gtk-ok.svg')
ICON_STAR = QtGui.QIcon('./icons/gtk-about.svg')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))

UI_PATH = "ui"
CONFIG_FILE = "pymedical.conf"

UI_PY_MEDICAL = "pymedical.ui"
UI_LOGIN = "login.ui"
UI_LOGIN_STATISTICS = "login_statistics.ui"

UI_MEDICAL_RECORD = "medical_record.ui"
UI_MEDICAL_RECORD2 = "medical_record2.ui"
UI_INS_PRESCRIPT_RECORD = "ins_prescript_record.ui"
UI_SELF_PRESCRIPT_RECORD = "self_prescript_record.ui"
UI_INS_CARE_RECORD = "ins_care_record.ui"
UI_MEDICAL_RECORD_RECENTLY_HISTORY = "medical_record_recently_history.ui"
UI_MEDICAL_RECORD_REGISTRATION = "medical_record_registration.ui"
UI_MEDICAL_RECORD_IMAGE = "medical_record_image.ui"
UI_MEDICAL_RECORD_FEES = "medical_record_fees.ui"
UI_MEDICAL_RECORD_LIST = "medical_record_list.ui"
UI_MEDICAL_RECORD_FAMILY = "medical_record_family.ui"
UI_MEDICAL_RECORD_EXAMINATION = "medical_record_examination.ui"

UI_SYSTEM_UPDATE = "system_update.ui"

UI_PATIENT_LIST = "patient_list.ui"
UI_PATIENT = "patient.ui"

UI_CERTIFICATE_DIAGNOSIS = "certificate_diagnosis.ui"
UI_CERTIFICATE_PAYMENT = "certificate_payment.ui"

UI_RETURN_CARD = "return_card.ui"
UI_REGISTRATION = "registration.ui"
UI_RESERVATION = "reservation.ui"
UI_TEMPLATE = "template.ui"
UI_WAITING_LIST = "waiting_list.ui"
UI_CASHIER = "cashier.ui"
UI_INCOME = "income.ui"
UI_INCOME_CASH_FLOW = "income_cash_flow.ui"
UI_INCOME_LIST = "income_list.ui"
UI_INCOME_SELF_PRESCRIPT = "income_self_prescript.ui"
UI_DEBT = "debt.ui"
UI_PURCHASE = "purchase.ui"
UI_PURCHASE_LIST = "purchase_list.ui"
UI_EXAMINATION_LIST = "examination_list.ui"
UI_EXAMINATION = "examination.ui"

UI_EVENT_LOG = "event_log.ui"

UI_INS_CHECK = "ins_check.ui"
UI_INS_APPLY = "ins_apply.ui"
UI_INS_APPLY_LIST = "ins_apply_list.ui"
UI_INS_APPLY_TAB = "ins_apply_tab.ui"
UI_INS_JUDGE = "ins_judge.ui"
UI_INS_APPLY_CALCULATED_DATA = "ins_apply_calculated_data.ui"
UI_INS_APPLY_TOTAL_FEE = "ins_apply_total_fee.ui"
UI_INS_CHECK_APPLY_FEE = "ins_check_apply_fee.ui"
UI_INS_DOCTOR_APPLY_FEE = "ins_doctor_apply_fee.ui"
UI_INS_APPLY_FEE_PERFORMANCE = "ins_apply_fee_performance.ui"
UI_INS_APPLY_SCHEDULE_TABLE = "ins_apply_schedule_table.ui"
UI_INS_APPLY_TOUR = "ins_apply_tour.ui"

UI_STATISTICS_MEDICAL_RECORD = "statistics_medical_record.ui"
UI_STATISTICS_MEDICAL_RECORD_DIAG_TIME_LENGTH = "statistics_medical_record_diag_time_length.ui"
UI_STATISTICS_MEDICAL_RECORD_DISEASE_RANK = "statistics_medical_record_disease_rank.ui"

UI_STATISTICS_DOCTOR = "statistics_doctor.ui"
UI_STATISTICS_DOCTOR_COUNT = "statistics_doctor_count.ui"
UI_STATISTICS_DOCTOR_INCOME = "statistics_doctor_income.ui"
UI_STATISTICS_DOCTOR_SALE = "statistics_doctor_sale.ui"
UI_STATISTICS_DOCTOR_PERFORMANCE = "statistics_doctor_performance.ui"
UI_STATISTICS_DOCTOR_COMMISSION = "statistics_doctor_commission.ui"
UI_STATISTICS_DOCTOR_PROJECT_SALE = "statistics_doctor_project_sale.ui"
UI_STATISTICS_INS_DISCOUNT = "statistics_ins_discount.ui"
UI_STATISTICS_INS_DISCOUNT_REGIST_FEE = "statistics_ins_discount_regist_fee.ui"
UI_STATISTICS_INS_DISCOUNT_DIAG_SHARE_FEE = "statistics_ins_discount_diag_share_fee.ui"
UI_STATISTICS_INS_DISCOUNT_DRUG_SHARE_FEE = "statistics_ins_discount_drug_share_fee.ui"
UI_STATISTICS_MULTIPLE_PERFORMANCE = "statistics_multiple_performance.ui"
UI_STATISTICS_MULTIPLE_PERFORMANCE_WEEK_PERSON = "statistics_multiple_performance_week_person.ui"
UI_STATISTICS_MULTIPLE_PERFORMANCE_WEEK_INCOME = "statistics_multiple_performance_week_income.ui"
UI_STATISTICS_MULTIPLE_PERFORMANCE_WEEK_PROJECT = "statistics_multiple_performance_week_project.ui"
UI_STATISTICS_MULTIPLE_PERFORMANCE_WEEK_DOCTOR = "statistics_multiple_performance_week_doctor.ui"

UI_STATISTICS_INS_PERFORMANCE = "statistics_ins_performance.ui"
UI_STATISTICS_INS_PERFORMANCE_MEDICAL_RECORD = "statistics_ins_performance_medical_record.ui"

UI_STATISTICS_RETURN_RATE = "statistics_return_rate.ui"
UI_STATISTICS_RETURN_RATE_DOCTOR = "statistics_return_rate_doctor.ui"
UI_STATISTICS_RETURN_RATE_MASSAGER = "statistics_return_rate_massager.ui"

UI_STATISTICS_MEDICINE = "statistics_medicine.ui"
UI_STATISTICS_MEDICINE_SALES = "statistics_medicine_sales.ui"

UI_DOCTOR_SCHEDULE = "doctor_schedule.ui"
UI_DOCTOR_NURSE_TABLE = "doctor_nurse_table.ui"

UI_CHECK_ERRORS = "check_errors.ui"
UI_CHECK_COURSE = "check_course.ui"
UI_CHECK_CARD = "check_card.ui"
UI_CHECK_MEDICAL_RECORD_COUNT = "check_medical_record_count.ui"
UI_CHECK_PRESCRIPT_DAYS = "check_prescript_days.ui"
UI_CHECK_INS_DRUG = "check_ins_drug.ui"
UI_CHECK_INS_TREAT = "check_ins_treat.ui"

UI_CHARGE_SETTINGS = "charge_settings.ui"
UI_CHARGE_SETTINGS_NHI = "charge_settings_nhi.ui"
UI_CHARGE_SETTINGS_REGIST = "charge_settings_regist.ui"
UI_CHARGE_SETTINGS_SHARE = "charge_settings_share.ui"

UI_DIALOG_DIAGNOSIS = "dialog_diagnosis.ui"
UI_DIALOG_DIAGNOSTIC_PICKER = "dialog_diagnostic_picker.ui"
UI_DIALOG_DISEASE = "dialog_disease.ui"
UI_DIALOG_DISEASE_PICKER = "dialog_disease_picker.ui"
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
UI_DIALOG_INPUT_HOST = "dialog_input_host.ui"
UI_DIALOG_EDIT_DISEASE = "dialog_edit_disease.ui"
UI_DIALOG_RICH_TEXT = "dialog_rich_text.ui"
UI_DIALOG_COMMISSION = "dialog_commission.ui"
UI_DIALOG_INS_LIST_EDIT = "dialog_ins_list_edit.ui"
UI_DIALOG_MEDICAL_RECORD_IMAGE = "dialog_medical_record_image.ui"

UI_DIALOG_MEDICAL_RECORD_LIST = "dialog_medical_record_list.ui"
UI_DIALOG_MEDICAL_RECORD_PAST_HISTORY = "dialog_medical_record_past_history.ui"
UI_DIALOG_MEDICAL_RECORD_HOSTS = "dialog_medical_record_hosts.ui"
UI_DIALOG_MEDICAL_RECORD_COLLECTION = "dialog_medical_record_collection.ui"
UI_DIALOG_MEDICAL_RECORD_PICKER = "dialog_medical_record_picker.ui"
UI_DIALOG_MEDICAL_RECORD_DONE = "dialog_medical_record_done.ui"
UI_DIALOG_MEDICAL_RECORD_REFERENCE = "dialog_medical_record_reference.ui"
UI_DIALOG_MEDICINE = "dialog_medicine.ui"

UI_DIALOG_EXAMINATION_LIST = "dialog_examination_list.ui"

UI_DIALOG_STATISTICS_THERAPIST = "dialog_statistics_therapist.ui"
UI_DIALOG_STATISTICS_RETURN_RATE = "dialog_statistics_return_rate.ui"
UI_DIALOG_INS_DATE_DOCTOR = "dialog_ins_date_doctor.ui"

UI_DIALOG_CERTIFICATE_DIAGNOSIS = "dialog_certificate_diagnosis.ui"
UI_DIALOG_CERTIFICATE_PAYMENT = "dialog_certificate_payment.ui"
UI_DIALOG_CERTIFICATE_QUERY = "dialog_certificate_query.ui"

UI_DIALOG_PAST_HISTORY = "dialog_past_history.ui"
UI_DIALOG_PATIENT = "dialog_patient.ui"
UI_DIALOG_PATIENT_LIST = "dialog_patient_list.ui"
UI_DIALOG_SELECT_PATIENT = "dialog_select_patient.ui"
UI_DIALOG_SELECT_REMOTE_PATIENT = "dialog_select_remote_patient.ui"

UI_DIALOG_RESERVATION_BOOKING = "dialog_reservation_booking.ui"
UI_DIALOG_RESERVATION_MODIFY = "dialog_reservation_modify.ui"
UI_DIALOG_RESERVATION_QUERY = "dialog_reservation_query.ui"

UI_DIALOG_ADDRESS = "dialog_address.ui"
UI_DIALOG_SETTINGS = "dialog_settings.ui"
UI_DIALOG_SYMPTOM = "dialog_symptom.ui"
UI_DIALOG_TONGUE = "dialog_tongue.ui"
UI_DIALOG_PULSE = "dialog_pulse.ui"
UI_DIALOG_PULSE_PICKER = "dialog_pulse_picker.ui"
UI_DIALOG_REMARK = "dialog_remark.ui"
UI_DIALOG_DISTINGUISH = "dialog_distinguish.ui"
UI_DIALOG_CURE = "dialog_cure.ui"
UI_DIALOG_RETURN_CARD = "dialog_return_card.ui"
UI_DIALOG_IC_RECORD_UPLOAD = "dialog_ic_record_upload.ui"
UI_DIALOG_INCOME = "dialog_income.ui"
UI_DIALOG_DEBT = "dialog_debt.ui"
UI_DIALOG_ELECTRIC_ACUPUNCTURE = "dialog_electric_acupuncture.ui"
UI_DIALOG_PURCHASE_LIST = "dialog_purchase_list.ui"
UI_DIALOG_EXPORT_EMR_XML = "dialog_export_emr_xml.ui"
UI_DIALOG_DATE_PICKER = "dialog_date_picker.ui"
UI_DIALOG_ACUPUNCTURE_POINT = "dialog_acupuncture_point.ui"
UI_DIALOG_PERMISSION = "dialog_permission.ui"
UI_DIALOG_HOSTS = "dialog_hosts.ui"
UI_DIALOG_ADD_DIAGNOSTIC_DICT = "dialog_add_diagnostic_dict.ui"
UI_DIALOG_ADD_DEPOSIT = "dialog_add_deposit.ui"
UI_DIALOG_IMPORT_MEDICAL_RECORD = "dialog_import_medical_record.ui"
UI_DIALOG_OFF_DAY_SETTING = "dialog_off_day_setting.ui"

UI_DIALOG_INS_CHECK = "dialog_ins_check.ui"
UI_DIALOG_INS_APPLY = "dialog_ins_apply.ui"
UI_DIALOG_INS_JUDGE = "dialog_ins_judge.ui"
UI_DIALOG_INS_CARE = "dialog_ins_care.ui"
UI_DIALOG_DOCTOR_SCHEDULE = "dialog_doctor_schedule.ui"
UI_DIALOG_NURSE_SCHEDULE = "dialog_nurse_schedule.ui"
UI_DIALOG_COURSE_LIST = "dialog_course_list.ui"
UI_DIALOG_CERTIFICATE_ITEMS = "dialog_certificate_items.ui"

UI_DIALOG_DATABASE_REPAIR = "dialog_database_repair.ui"

UI_DIALOG_MASSAGE_RESERVATION = "dialog_massage_reservation.ui"
UI_DIALOG_CUSTOMER = "dialog_customer.ui"
UI_DIALOG_MASSAGE_CASE_LIST = "dialog_massage_case_list.ui"
UI_MASSAGE_PURCHASE_LIST = "massage_purchase_list.ui"
UI_MASSAGE_PURCHASE = "massage_purchase.ui"
UI_MASSAGE_INCOME = "massage_income.ui"
UI_DIALOG_MASSAGE_PURCHASE_LIST = "dialog_massage_purchase_list.ui"
UI_MASSAGE_INCOME_CASH_FLOW = "massage_income_cash_flow.ui"
UI_MASSAGE_INCOME_LIST = "massage_income_list.ui"
UI_MASSAGE_CUSTOMER_LIST = "massage_customer_list.ui"
UI_MASSAGE_CASE_LIST = "massage_case_list.ui"
UI_STATISTICS_MASSAGE = "statistics_massage.ui"
UI_STATISTICS_MASSAGE_COUNT = "statistics_massage_count.ui"
UI_STATISTICS_MASSAGE_INCOME = "statistics_massage_income.ui"
UI_STATISTICS_MASSAGE_PAYMENT = "statistics_massage_payment.ui"
UI_STATISTICS_MASSAGE_SALE = "statistics_massage_sale.ui"

UI_DICT_DIAGNOSTIC = "dict_diagnostic.ui"
UI_DICT_SYMPTOM = "dict_symptom.ui"
UI_DICT_TONGUE = "dict_tongue.ui"
UI_DICT_PULSE = "dict_pulse.ui"
UI_DICT_REMARK = "dict_remark.ui"
UI_DICT_DISEASE = "dict_disease.ui"
UI_DICT_DISTINGUISH = "dict_distinguish.ui"
UI_DICT_CURE = "dict_cure.ui"
UI_DICT_MEDICINE = "dict_medicine.ui"
UI_DICT_MISC = "dict_misc.ui"
UI_DICT_DRUG = "dict_drug.ui"
UI_DICT_TREAT = "dict_treat.ui"
UI_DICT_INSTRUCTION = "dict_instruction.ui"
UI_DICT_HOSP = "dict_hosp.ui"
UI_DICT_COMPOUND = "dict_compound.ui"

UI_DICT_INS_DRUG = "dict_ins_drug.ui"

UI_USERS = "users.ui"
UI_CONVERT = "convert.ui"
UI_IC_RECORD_UPLOAD = 'ic_record_upload.ui'

UI_RESTORE_RECORDS = "restore_records.ui"
UI_RESTORE_MEDICAL_RECORDS = "restore_medical_records.ui"

UI_MASSAGE_REGISTRATION = "massage_registration.ui"

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
    combobox.clear()

    combobox.setMaxVisibleItems(30)
    if items == '掛號優待':
        items = get_discount_type(args[0])
        args = []

    for arg in args:
        combobox.addItem(arg)

    for item in items:
        combobox.addItem(item)


def set_combo_box_item_color(combobox, colors):
    for item_no in range(len(colors)):
        combobox.setItemData(
            item_no, colors[item_no], QtCore.Qt.TextColorRole)


# 設定輸入文字補全
def set_completer(database, sql, field, widget):
    rows = database.select_record(sql)
    completer_list = []
    for row in rows:
        if type(field) is list:
            field_name = ''
            for f in field:
                field_name += row[f]
        else:
            field_name = row[field]

        completer_list.append(field_name)

    model = QtCore.QStringListModel()
    model.setStringList(completer_list)
    completer = QtWidgets.QCompleter()
    completer.setModel(model)
    completer.setCompletionColumn(2)

    if type(widget) is list:
        for w in widget:
            w.setCompleter(completer)
    else:
        widget.setCompleter(completer)


def set_table_widget_field_icon(table_widget, row_no, col_no, icon_file_name,
                                property_name, property_value, function_call):
    icon = QtGui.QIcon(icon_file_name)

    button = QtWidgets.QPushButton(table_widget)
    button.setProperty(property_name, property_value)
    button.setIcon(icon)
    button.setFlat(True)
    button.clicked.connect(function_call)
    table_widget.setCellWidget(row_no, col_no, button)


# 設定 instruction comboBox
def set_instruction_combo_box(database, combobox):
    set_combo_box(combobox, nhi_utils.INSTRUCTION, None)

    sql = '''
        SELECT * FROM clinic 
        WHERE 
            ClinicType = "指示" 
        ORDER BY LENGTH(ClinicName), CAST(CONVERT(`ClinicName` using big5) AS BINARY)
    '''
    rows = database.select_record(sql)

    for row in rows:
        instruction = string_utils.xstr(row['ClinicName'])
        if instruction in nhi_utils.INSTRUCTION:
            continue

        combobox.addItem(instruction)


def get_medical_record_ui_file(system_settings):
    if system_settings.field('病歷版面') == '版面1':
        ui_file = UI_MEDICAL_RECORD
    elif system_settings.field('病歷版面') == '版面2':
        ui_file = UI_MEDICAL_RECORD2
    else:
        ui_file = UI_MEDICAL_RECORD

    return ui_file

