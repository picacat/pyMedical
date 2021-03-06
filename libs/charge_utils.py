# 取得各項費用金額

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton

import datetime

from libs import number_utils
from libs import string_utils
from libs import nhi_utils
from libs import case_utils
from libs import prescript_utils
from libs import date_utils

DISCOUNT_TYPE = ['掛號費優待', '門診負擔優待', '藥品負擔優待']


# 基本掛號費
def _get_basic_regist_fee(database, ins_type):
    regist_fee = 0
    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "掛號費" AND 
            ItemName = "基本掛號費" AND InsType = "{0}"
          '''.format(ins_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('找不到基本掛號費')
        msg_box.setText("<font size='4' color='red'><b>找不到基本掛號費，請至收費資料->掛號費設定</b></font>")
        msg_box.setInformativeText("請新增「基本掛號費」")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
        return regist_fee

    if len(row) > 0:
        regist_fee = number_utils.get_float(row['Amount'])

    return regist_fee


# 基本掛號費
def _get_basic_discount_fee(database):
    discount_fee = 0
    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "掛號費優待" AND 
            ItemName = "其他優待"
          '''
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('找不到其他優待')
        msg_box.setText("<font size='4' color='red'><b>找不到其他優待，請至收費資料->掛號費優待設定</b></font>")
        msg_box.setInformativeText("請新增「其他優待")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
        return discount_fee

    if len(row) > 0:
        discount_fee = number_utils.get_integer(row['Amount'])

    return discount_fee


# 取得掛號費優待
def _get_regist_discount_fee(database, discount_type):
    discount_fee = _get_basic_discount_fee(database)

    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "掛號費優待" AND 
            ItemName = "{0}"
          '''.format(discount_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return discount_fee

    if len(row) > 0:
        discount_fee = number_utils.get_integer(row['Amount'])

    return discount_fee


# 取得掛號費
def get_regist_fee(database, system_settings,
                   birthday, discount_type, ins_type, share_type, treat_type, course=None):
    regist_fee = _get_basic_regist_fee(database, ins_type)
    course_type = nhi_utils.get_course_type(course)
    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "掛號費" AND 
            InsType = "{0}" AND ShareType = "{1}" AND 
            TreatType = "{2}" AND Course = "{3}" 
          '''.format(ins_type, share_type, treat_type, course_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return regist_fee

    if len(row) > 0:
        regist_fee = number_utils.get_integer(row['Amount'])

    if string_utils.xstr(discount_type) != '':  # 掛號費優待優先取得
        discount_fee = _get_regist_discount_fee(database, discount_type)
        if discount_fee >= 0:
            regist_fee = discount_fee
        else:
            regist_fee += discount_fee
    else:  # 最後檢查是否符合老人優待, 已經優待者就不檢查
        old_man_regist_fee = get_old_man_regist_fee(database, system_settings, birthday)
        if old_man_regist_fee is not None:
            if old_man_regist_fee >= 0:
                regist_fee = old_man_regist_fee
            else:
                regist_fee += old_man_regist_fee

    return regist_fee


def get_old_man_regist_fee(database, system_settings, birthday):
    old_man_regist_fee = None
    if system_settings.field('老人優待') != 'Y':
        return old_man_regist_fee

    if birthday == '':
        return old_man_regist_fee

    try:
        birthday = date_utils.str_to_date(birthday)
    except:
        return old_man_regist_fee

    age_year, _ = date_utils.get_age(birthday, datetime.datetime.now())

    old_man_age = number_utils.get_integer(system_settings.field('老人優待年齡'))
    if age_year >= old_man_age:
        sql = '''
            SELECT * FROM charge_settings
            WHERE
                ChargeType = "掛號費優待" AND
                ItemName = "年長病患"
        '''
        rows = database.select_record(sql)
        if len(rows) <= 0:
            old_man_regist_fee = None
        else:
            old_man_regist_fee = number_utils.get_integer(rows[0]['Amount'])

    return old_man_regist_fee


# 取得欠卡費
def get_deposit_fee(database, card):
    deposit_fee = 0

    if card != '欠卡':
        return deposit_fee

    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "掛號費" AND ItemName = "欠卡費"
          '''
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return deposit_fee

    if len(row) > 0:
        deposit_fee = number_utils.get_integer(row['Amount'])

    return deposit_fee


# 取得門診負擔 (treat_type 取代 treatment的原因: 掛號時須取得門診負擔, 以treat_type代表)
def get_diag_share_fee(database, share_type, treatment, course, reg_type=None):
    diag_share_fee = 0
    course_type = nhi_utils.get_course_type(course)
    if treatment in nhi_utils.ACUPUNCTURE_TREAT:
        treatment = '針灸治療'
    elif treatment in nhi_utils.MASSAGE_TREAT:
        treatment = '傷科治療'
    else:
        treatment = '內科'

    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" AND 
            ShareType = "{0}" AND TreatType = "{1}" AND Course = "{2}"
    '''.format(share_type, treatment, course_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return diag_share_fee

    if len(row) > 0:
        diag_share_fee = number_utils.get_integer(row['Amount'])

    if reg_type in nhi_utils.TOUR_FAR:
        diag_share_fee *= 0.8  # 偏遠地區減免20%

    return int(diag_share_fee)


# 取得門診負擔優待
def get_diag_share_discount_fee(database, discount_type):
    diag_share_discount_fee = None

    sql = '''
        SELECT * FROM charge_settings
        WHERE
            ChargeType = "門診負擔優待" AND
            ItemName = "{discount_type}"
    '''.format(
        discount_type=discount_type,
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return diag_share_discount_fee

    row = rows[0]
    diag_share_discount_fee = number_utils.get_integer(row['Amount'])

    return diag_share_discount_fee


# 取得藥品負擔
def get_drug_share_fee(database, share_type, ins_drug_fee, reg_type=None):
    drug_share_fee = 0
    if share_type == '基層醫療':
        remark = None
        if ins_drug_fee <= 100:
            remark = '<=100'
        elif ins_drug_fee <= 200:
            remark = '<=200'
        elif ins_drug_fee <= 300:
            remark = '<=300'
        elif ins_drug_fee <= 400:
            remark = '<=400'
        elif ins_drug_fee <= 500:
            remark = '<=500'
        elif ins_drug_fee <= 600:
            remark = '<=600'
        elif ins_drug_fee <= 700:
            remark = '<=700'
        elif ins_drug_fee <= 800:
            remark = '<=800'
        elif ins_drug_fee <= 900:
            remark = '<=900'
        elif ins_drug_fee <= 1000:
            remark = '<=1000'
        elif ins_drug_fee > 1000:
            remark = '>1000'

        sql = '''
                SELECT * FROM charge_settings WHERE 
                (ChargeType = "藥品負擔") AND (ShareType = "{0}") AND (Remark = "{1}")
              '''.format(share_type, remark)
    else:
        sql = '''
                SELECT * FROM charge_settings WHERE (ChargeType = "藥品負擔") AND (ShareType = "{0}")
              '''.format(share_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return drug_share_fee

    if len(row) > 0:
        drug_share_fee = number_utils.get_integer(row['Amount'])

    if reg_type in nhi_utils.TOUR_FAR:
        drug_share_fee *= 0.8  # 偏遠地區減免20%

    return int(drug_share_fee)


# 取得藥品負擔優待
def get_drug_share_discount_fee(database, discount_type):
    drug_share_discount_fee = None

    sql = '''
        SELECT * FROM charge_settings
        WHERE
            ChargeType = "藥品負擔優待" AND
            ItemName = "{discount_type}"
    '''.format(
        discount_type=discount_type,
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return drug_share_discount_fee

    row = rows[0]
    drug_share_discount_fee = number_utils.get_integer(row['Amount'])

    return drug_share_discount_fee


# 取得門診負擔
def get_traditional_health_care_fee(database, ins_type, massager):
    traditional_health_care_fee = 0

    if massager is None or massager == '':
        return traditional_health_care_fee

    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" AND 
            ItemName = "傷科調理費" AND InsType = "{0}"
          '''.format(ins_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return traditional_health_care_fee

    if len(row) > 0:
        traditional_health_care_fee = number_utils.get_integer(row['Amount'])

    return traditional_health_care_fee


# 取得醫療費用金額
def get_ins_fee_from_ins_code(database, ins_code):
    ins_fee = 0

    if ins_code is None:
        return ins_fee

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(ins_code)

    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_fee

    ins_fee = number_utils.get_integer(row[0]['Amount'])

    return ins_fee


# 取得醫療費用名稱
def get_item_name_from_ins_code(database, ins_code):
    ins_fee = 0

    if ins_code is None:
        return ins_fee

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(ins_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_fee

    item_name = string_utils.xstr(row[0]['ItemName'])

    return item_name


# 取得健保門診診察費
# 取第一段診察費, 分有無護理人員, 支援醫師等到申報才調整
def get_ins_diag_fee(database, system_settings, course=1, diag_code=None):
    ins_diag_fee = 0

    if course >= 2:  # 療程無診察費
        return ins_diag_fee

    if diag_code is None:
        nurse = system_settings.field('護士人數')
        if number_utils.get_integer(nurse) > 0:
            diag_code = 'A01'
        else:
            diag_code = 'A02'

    ins_diag_fee = get_ins_fee_from_ins_code(database, diag_code)

    return ins_diag_fee


# 取得健保藥費
# 藥費 = 每日藥費 * 給藥天數
def get_ins_drug_fee(database, pres_days):
    ins_drug_fee = 0

    if pres_days == 0:
        return ins_drug_fee

    drug_code = 'A21'
    ins_drug_fee = get_ins_fee_from_ins_code(database, drug_code) * pres_days

    return ins_drug_fee


# 取得健保調劑費
# 調劑費 = 0: 不申報調劑費, 沒有申報藥費
# 調劑費 > 0: 藥師調劑, 醫師調劑
def get_ins_pharmacy_fee(database, system_settings, ins_drug_fee, pharmacy_type='申報'):
    ins_pharmacy_fee = 0

    if ins_drug_fee == 0:
        return ins_pharmacy_fee

    if pharmacy_type == '不申報':
        return ins_pharmacy_fee

    pharmacist = system_settings.field('藥師人數')

    if int(pharmacist) > 0:
        item_name = '藥師調劑'
    else:
        item_name = '醫師調劑'

    pharmacy_code = get_ins_code_from_charge_settings(database, '調劑費', item_name)
    ins_pharmacy_fee = get_ins_fee_from_ins_code(database, pharmacy_code)

    return ins_pharmacy_fee


def get_ins_code_from_charge_settings(database, charge_type, item_name):
    ins_code = ''
    sql = '''
        SELECT * FROM charge_settings 
        WHERE
            ChargeType = "{0}" AND
            ItemName = "{1}"
    '''.format(charge_type, item_name)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ins_code

    return string_utils.xstr(rows[0]['InsCode'])


# 取得健保針灸費
def get_ins_acupuncture_fee(database, treatment, ins_drug_fee):
    ins_acupuncture_fee = 0

    if treatment not in nhi_utils.ACUPUNCTURE_DRUG_DICT:
        return ins_acupuncture_fee

    if ins_drug_fee > 0:
        acupuncture_code = nhi_utils.ACUPUNCTURE_DRUG_DICT[treatment]
    else:
        acupuncture_code = nhi_utils.ACUPUNCTURE_DICT[treatment]

    ins_acupuncture_fee = get_ins_fee_from_ins_code(database, acupuncture_code)

    return ins_acupuncture_fee


# 取得健保傷科治療費
def get_ins_massage_fee(database, treatment, ins_drug_fee):
    ins_massage_fee = 0

    if treatment not in nhi_utils.MASSAGE_TREAT:
        return ins_massage_fee

    if ins_drug_fee > 0:
        massage_code = nhi_utils.MASSAGE_DRUG_DICT[treatment]
    else:
        massage_code = nhi_utils.MASSAGE_DICT[treatment]

    ins_massage_fee = get_ins_fee_from_ins_code(database, massage_code)

    return ins_massage_fee


# 取得健保脫臼治療費
def get_ins_dislocate_fee(database, treatment, ins_drug_fee):
    ins_dislocate_fee = 0

    if treatment not in nhi_utils.DISLOCATE_TREAT:
        return ins_dislocate_fee

    if ins_drug_fee > 0:
        dislocate_code = nhi_utils.DISLOCATE_DRUG_DICT[treatment]
    else:
        dislocate_code = nhi_utils.DISLOCATE_DICT[treatment]

    ins_dislocate_fee = get_ins_fee_from_ins_code(database, dislocate_code)

    return ins_dislocate_fee


# 取得健保加強照護費
def get_ins_care_fee_from_case_key(database, case_key):
    ins_care_fee = 0

    sql = '''
        SELECT * FROM prescript
        WHERE
            CaseKey = {0} AND
            MedicineSet = 11
    '''.format(case_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return ins_care_fee

    for row in rows:
        ins_care_fee += get_ins_fee_from_ins_code(database, string_utils.xstr(row['InsCode']))

    return ins_care_fee


# 取得健保加強照護費
def get_ins_care_fee_from_table_widget(table_widget):
    ins_care_fee = 0
    for row_no in range(table_widget.rowCount()):
        amount = table_widget.item(row_no, 12)
        if amount is not None:
            ins_care_fee += number_utils.get_integer(amount.text())

    return ins_care_fee


# 取得健保代辦費
def get_ins_agent_fee(database, share_type, treatment, course, ins_drug_fee, reg_type=None):
    ins_agent_fee = 0

    if share_type in ['重大傷病', '山地離島']:  # 重大傷病, 山地離島: 無代辦費
        return ins_agent_fee

    if share_type in nhi_utils.AGENT_SHARE:
        diag_share_fee = get_diag_share_fee(  # 以基層醫療為代辦基礎
            database,
            '基層醫療',
            nhi_utils.get_treat_type(treatment),
            course,
            reg_type
        )
        drug_share_fee = get_drug_share_fee(
            database,
            '基層醫療',
            ins_drug_fee,
            reg_type,
        )
        ins_agent_fee = diag_share_fee + drug_share_fee

    return ins_agent_fee


# 取得各項照護申報費用
def get_ins_special_care_fee(database, system_settings, case_key, treat_type,
                             share, course, pres_days, pharmacy_type, treatment,
                             table_widget_ins_care=None):
    ins_fee = {}

    diag_fee = 0
    drug_fee = 0
    pharmacy_fee = 0
    acupuncture_fee = 0
    massage_fee = 0
    if table_widget_ins_care is None:
        care_fee = get_ins_care_fee_from_case_key(database, case_key)  # 小兒氣喘, 小兒腦麻為包套, 照護費已包含藥費, 調劑費與針傷處置費
    else:
        care_fee = get_ins_care_fee_from_table_widget(table_widget_ins_care)  # 小兒氣喘, 小兒腦麻為包套, 照護費已包含藥費, 調劑費與針傷處置費

    if treat_type in ['腦血管疾病', '兒童鼻炎']:  # 腦血管疾病, 兒童鼻炎可申報藥費及調劑費
        drug_fee = get_ins_drug_fee(database, pres_days)
        pharmacy_fee = get_ins_pharmacy_fee(
            database, system_settings, drug_fee,
            pharmacy_type
        )

    if treat_type in ['腦血管疾病']:  # 腦血管疾病可申報藥費及調劑費
        care_fee = get_ins_fee_from_ins_code(database, 'C05')  # 預設為C05 <= 3次

    if treat_type in ['兒童鼻炎']:  # 兒童鼻炎可申報診察費, 針灸費, 傷科費
        diag_fee = get_ins_diag_fee(
            database, system_settings, course
        )
        acupuncture_fee = get_ins_acupuncture_fee(
            database, treatment, drug_fee,
        )
        massage_fee = get_ins_massage_fee(
            database, treatment, drug_fee,
        )

    ins_fee['diag_fee'] = diag_fee
    ins_fee['drug_fee'] = drug_fee
    ins_fee['pharmacy_fee'] = pharmacy_fee
    ins_fee['acupuncture_fee'] = acupuncture_fee
    ins_fee['massage_fee'] = massage_fee
    ins_fee['dislocate_fee'] = care_fee

    ins_fee['ins_total_fee'] = (
            ins_fee['diag_fee'] +
            ins_fee['drug_fee'] +
            ins_fee['pharmacy_fee'] +
            ins_fee['acupuncture_fee'] +
            ins_fee['massage_fee'] +
            ins_fee['dislocate_fee']
    )

    ins_fee['diag_share_fee'] = get_diag_share_fee(
        database, share, treatment, course,
    )
    if treat_type in ['乳癌照護', '肝癌照護', '助孕照護', '保胎照護']:  # 照護要申報藥品負擔
        virtual_drug_fee = get_ins_drug_fee(database, pres_days)
        ins_fee['drug_share_fee'] = get_drug_share_fee(
            database, share, virtual_drug_fee,
        )
    else:
        ins_fee['drug_share_fee'] = get_drug_share_fee(
            database, share, drug_fee,
        )

    ins_fee['ins_apply_fee'] = (
            ins_fee['ins_total_fee'] -
            ins_fee['diag_share_fee'] -
            ins_fee['drug_share_fee']
    )
    ins_fee['agent_fee'] = get_ins_agent_fee(
        database, share, treatment, course, drug_fee,
    )

    return ins_fee


def get_ins_fee(database, system_settings, case_key, reg_type, treat_type,
                share, course, pres_days, pharmacy_type, treatment, table_widget_ins_care=None):
    if treat_type in nhi_utils.CARE_TREAT:
        ins_fee = get_ins_special_care_fee(
            database, system_settings, case_key, treat_type,
            share, course, pres_days, pharmacy_type, treatment,
            table_widget_ins_care
        )
        return ins_fee

    ins_fee = {}

    ins_fee['diag_fee'] = get_ins_diag_fee(
        database, system_settings, course)
    ins_fee['drug_fee'] = get_ins_drug_fee(database, pres_days)
    ins_fee['pharmacy_fee'] = get_ins_pharmacy_fee(
        database, system_settings, ins_fee['drug_fee'],
        pharmacy_type
    )
    ins_fee['acupuncture_fee'] = get_ins_acupuncture_fee(
        database, treatment, ins_fee['drug_fee'])
    ins_fee['massage_fee'] = get_ins_massage_fee(
        database, treatment, ins_fee['drug_fee'])
    ins_fee['dislocate_fee'] = get_ins_dislocate_fee(
        database, treatment, ins_fee['drug_fee'])

    ins_fee['ins_total_fee'] = (
            ins_fee['diag_fee'] +
            ins_fee['drug_fee'] +
            ins_fee['pharmacy_fee'] +
            ins_fee['acupuncture_fee'] +
            ins_fee['massage_fee'] +
            ins_fee['dislocate_fee']
    )

    ins_fee['diag_share_fee'] = get_diag_share_fee(
        database, share, treatment, course, reg_type,
    )
    ins_fee['drug_share_fee'] = get_drug_share_fee(
        database, share, ins_fee['drug_fee'], reg_type,
    )

    ins_fee['ins_apply_fee'] = (
            ins_fee['ins_total_fee'] -
            ins_fee['diag_share_fee'] -
            ins_fee['drug_share_fee']
    )
    ins_fee['agent_fee'] = get_ins_agent_fee(
        database, share, treatment, course, ins_fee['drug_fee'],
    )

    return ins_fee


# 重新批價
def calculate_ins_fee(database, system_settings, case_key):
    sql = '''
        SELECT 
            CaseKey, RegistType, Share, Continuance, TreatType, PharmacyType, Treatment 
        FROM cases 
        WHERE 
            CaseKey = {0}
    '''.format(case_key)
    rows = database.select_record(sql)
    if len(rows) > 0:
        row = rows[0]
    else:
        return

    pres_days = case_utils.get_pres_days(database, case_key)
    reg_type = string_utils.xstr(row['RegistType'])
    treat_type = string_utils.xstr(row['TreatType'])
    share = string_utils.xstr(row['Share'])
    course = number_utils.get_integer(row['Continuance'])
    pharmacy_type = string_utils.xstr(row['PharmacyType'])
    treatment = string_utils.xstr(row['Treatment'])

    ins_fee = get_ins_fee(
        database, system_settings, case_key,
        reg_type, treat_type, share, course, pres_days, pharmacy_type, treatment)

    fields = [
        'DiagFee', 'InterDrugFee', 'PharmacyFee',
        'AcupunctureFee', 'MassageFee', 'DislocateFee',
        'InsTotalFee', 'DiagShareFee', 'DrugShareFee', 'InsApplyFee', 'AgentFee',
    ]

    data = [
        ins_fee['diag_fee'],
        ins_fee['drug_fee'],
        ins_fee['pharmacy_fee'],
        ins_fee['acupuncture_fee'],
        ins_fee['massage_fee'],
        ins_fee['dislocate_fee'],
        ins_fee['ins_total_fee'],
        ins_fee['diag_share_fee'],
        ins_fee['drug_share_fee'],
        ins_fee['ins_apply_fee'],
        ins_fee['agent_fee']
    ]

    database.update_record('cases', fields, 'CaseKey', case_key, data)


# 自費批價
def get_self_fee(database, tab_list):
    self_fee = {}
    self_fee['diag_fee'] = 0.0
    self_fee['drug_fee'] = 0.0
    self_fee['herb_fee'] = 0.0
    self_fee['expensive_fee'] = 0.0
    self_fee['acupuncture_fee'] = 0.0
    self_fee['massage_fee'] = 0.0
    self_fee['material_fee'] = 0.0
    self_fee['discount_fee'] = 0.0

    for medicine_set, tab in zip(range(len(tab_list)), tab_list):
        medicine_set += 1
        if medicine_set in [1, 12]:  # 健保=1, 加強照護=12, 不批價
            continue

        if tab is None:
            continue

        try:
            pres_days = number_utils.get_integer(tab.ui.comboBox_pres_days.currentText())
            if pres_days <= 0:
                pres_days = 1
        except:
            pres_days = 1

        self_fee['discount_fee'] += number_utils.get_integer(tab.ui.lineEdit_discount_fee.text())
        calculate_self_fee(
            database,
            tab.ui.tableWidget_prescript,
            pres_days,
            self_fee,
        )

    return self_fee


# 計算自費批價
def calculate_self_fee(database, table_widget_prescript, pres_days, self_fee):
    try:
        row_count = table_widget_prescript.rowCount()
    except RuntimeError:
        return

    for row_no in range(row_count):
        item = table_widget_prescript.item(row_no, prescript_utils.SELF_PRESCRIPT_COL_NO['MedicineType'])
        if item is None:
            continue

        medicine_type = item.text()
        amount = get_table_widget_item_fee(
            table_widget_prescript, row_no,
            prescript_utils.SELF_PRESCRIPT_COL_NO['Amount'])

        subtotal = get_subtotal_fee(amount, pres_days)

        field = get_medicine_type_charge_field(database, medicine_type)
        if field in [None, '']:
            if medicine_type == '水藥':
                charge_field = 'herb_fee'
            elif medicine_type == '高貴':
                charge_field = 'expensive_fee'
            elif medicine_type == '穴道':
                charge_field = 'acupuncture_fee'
            elif medicine_type == '處置':
                charge_field = 'massage_fee'
            elif medicine_type == '器材':
                charge_field = 'material_fee'
            else:
                charge_field = 'drug_fee'
        else:
            if field == '自費藥費':
                charge_field = 'drug_fee'
            elif field == '水藥費':
                charge_field = 'herb_fee'
            elif field == '高貴藥費':
                charge_field = 'expensive_fee'
            elif field == '自費針灸費':
                charge_field = 'acupuncture_fee'
            elif field == '傷科調理費':
                charge_field = 'massage_fee'
            elif field == '自費材料費':
                charge_field = 'material_fee'
            elif field == '自費診察費':
                charge_field = 'diag_fee'
            else:
                charge_field = 'drug_fee'

        self_fee[charge_field] += subtotal


def get_medicine_type_charge_field(database, medicine_type):
    sql = '''
        SELECT * FROM dict_groups
        WHERE
            DictGroupsType = "藥品類別" AND
            DictGroupsName = "{medicine_type}"
    '''.format(
        medicine_type=medicine_type,
    )

    rows = database.select_record(sql)

    if len(rows) <= 0:
        return None

    row = rows[0]

    return string_utils.xstr(row['DictGroupsTopLevel'])


# 計算處方金額小計
def get_subtotal_fee(amount, pres_days):
    subtotal = number_utils.round_up(amount) * pres_days  # 小計四捨五入後再 * 天數

    return subtotal


def update_ins_apply_diag_fee(database, system_settings, ins_apply_key, diag_code):
    sql = 'SELECT * FROM insapply WHERE InsApplyKey = {0}'.format(ins_apply_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return

    row = rows[0]
    diag_fee = get_ins_diag_fee(
        database, system_settings, 0, diag_code
    )

    ins_total_fee = row['InsTotalFee'] - row['DiagFee'] + diag_fee
    ins_apply_fee = row['InsApplyFee'] - row['DiagFee'] + diag_fee

    fields = ['DiagCode', 'DiagFee', 'InsTotalFee', 'InsApplyFee']
    data = [
        diag_code,
        diag_fee,
        ins_total_fee,
        ins_apply_fee,
    ]

    database.update_record('insapply', fields, 'InsApplyKey', ins_apply_key, data)


def update_treat_fee(database, ins_apply_key, course, treat_percent):
    sql = 'SELECT * FROM insapply WHERE InsApplyKey = {0}'.format(ins_apply_key)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return

    row = rows[0]
    treat_fee = row['TreatFee{0}'.format(course)]
    adjusted_treat_fee = treat_fee / 100 * treat_percent

    total_treat_fee = row['TreatFee'] - treat_fee + adjusted_treat_fee
    ins_total_fee = row['InsTotalFee'] - treat_fee + adjusted_treat_fee
    ins_apply_fee = row['InsApplyFee'] - treat_fee + adjusted_treat_fee

    fields = [
        'TreatFee',
        'InsTotalFee',
        'InsApplyFee',
        'Percent{0}'.format(course),
        'TreatFee{0}'.format(course),
    ]

    data = [
        total_treat_fee,
        ins_total_fee,
        ins_apply_fee,
        treat_percent,
        adjusted_treat_fee,
    ]

    database.update_record('insapply', fields, 'InsApplyKey', ins_apply_key, data)


def set_nhi_basic_data(database):
    fields = ['ChargeType', 'ItemName', 'InsCode', 'Amount', 'Remark']
    rows = [
        ('診察費', '<=30人次門診診察費(有護理人員)', 'A01', 335, '支援醫師不適用'),
        ('診察費', '<=30人次門診診察費', 'A02', 325, None),
        ('診察費', '31-50人次門診診察費(有護理人員)', 'A03', 230, '支援醫師不適用'),
        ('診察費', '31-50人次門診診察費', 'A04', 220, None),
        ('診察費', '51-70人次門診診察費(有護理人員)', 'A05', 160, '支援醫師不適用'),
        ('診察費', '51-70人次門診診察費', 'A06', 150, None),
        ('診察費', '71-150人次門診診察費', 'A07', 90, None),
        ('診察費', '>150人次門診診察費', 'A08', 50, None),
        ('診察費', '山地離島門診診察費(有護理人員)', 'A09', 335, None),
        ('診察費', '山地離島門診診察費', 'A10', 325, None),
        ('診察費', '初診門診診察費加計', 'A90', 50, '2年以上新特約診所: 初診病患或2年內未就診病患'),
        ('藥費', '每日藥費', 'A21', 35, '一般案件給藥天數不得超過七日'),
        ('調劑費', '藥師調劑', 'A31', 23, '須先報備，經證明核可後申報'),
        ('調劑費', '醫師調劑', 'A32', 13, None),
        ('處置費', '針灸治療處置費-另開內服藥', 'B41', 227, None),
        ('處置費', '針灸治療處置費', 'B42', 227, None),
        ('處置費', '電針治療處置費-另開內服藥', 'B43', 227, None),
        ('處置費', '電針治療處置費', 'B44', 227, None),
        ('處置費', '複雜性針灸治療處置費-另開內服藥', 'B45', 307, None),
        ('處置費', '複雜性針灸治療處置費', 'B46', 307, None),
        ('處置費', '傷科治療處置費-另開內服藥', 'B53', 227, None),
        ('處置費', '傷科治療處置費', 'B54', 227, '標準作業程序: (1)四診八綱辨證(2)診斷(3)理筋手法'),
        ('處置費', '複雜性傷科治療處置費-另開內服藥', 'B55', 307, None),
        ('處置費', '複雜性傷科治療處置費', 'B56', 307, None),
        ('處置費', '骨折、脫臼整復第一線復位處置治療費', 'B57', 477,
         'B57「骨折、脫臼整復第一線復位處置治療」係指該患者受傷部位初次到醫療院所做接骨、復位之處理治療，且不得與B61併同申報'),
        ('處置費', '脫臼整復費-同療程第一次就醫', 'B61', 327, None),
        ('處置費', '脫臼整復費-同療程複診-另開內服藥', 'B62', 227, None),
        ('處置費', '脫臼整復費-同療程複診', 'B63', 227, None),
        ('照護費', '小兒氣喘照護處置費(含氣霧吸入處置費)', 'C01', 1500,
         '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、針灸治療處置費、穴位推拿按摩、穴位敷貼處置費、氣霧吸入處置費'),
        ('照護費', '小兒氣喘照護處置費', 'C02', 1400,
         '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、針灸治療處置費、穴位推拿按摩、穴位敷貼處置費'),
        ('照護費', '小兒腦性麻痺照護處置費(含藥浴處置費)', 'C03', 1500,
         '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、頭皮針及體針半刺治療處置費、穴位推拿按摩、督脈及神闕藥灸、藥浴處置費'),
        ('照護費', '小兒腦性麻痺照護處置費', 'C04', 1400,
         '照護處置費包括中醫四診診察費、口服藥(不得少於五天)、頭皮針及體針半刺治療處置費、穴位推拿按摩、督脈及神闕藥灸'),
        ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置1-3次)', 'C05', 2000,
         '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
        ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置4-6次)', 'C06', 3500,
         '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
        ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置7-9次)', 'C07', 5500,
         '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
        ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置10-12次)', 'C08', 7500,
         '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
        ('照護費', '腦血管疾病、顱腦損傷及脊髓損傷照護處置費(治療處置>=13次)', 'C09', 9500,
         '每月限申報一次，照護處置費包括中醫醫療診察費、同時執行針灸治療及傷科治療。首次收案即需進行衛教及巴氏量表，之後每三個月至少施行衛教及評估巴氏量表一次'),
        ('照護費', '中醫助孕照護處置費(含針灸處置)', 'P39001', 1200,
         '包括中醫四診診察費，估排卵期評估，女性須含基礎體溫(BBT)、體質證型、濾泡期、排卵期、黃體期之月經週期療法之診療、口服藥(至少七天)、針灸治療處置費、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
        ('照護費', '中醫助孕照護處置費(不含針灸處置)', 'P39002', 900,
         '包括中醫四診診察費，估排卵期評估，女性須含基礎體溫(BBT)、體質證型、濾泡期、排卵期、黃體期之月經週期療法之診療、口服藥(至少七天)、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
        ('照護費', '中醫保胎照護處置費(含針灸處置)', 'P39003', 1200,
         '中醫四診診察費口服藥(至少七天)、針灸治療處置費、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
        ('照護費', '中醫保胎照護處置費(不含針灸處置)', 'P39004', 900,
         '中醫四診診察費口服藥(至少七天)、衛教、營養飲食指導，單次門診須全部執行方能申請本項點數。'),
        ('照護費', '兒童過敏性鼻炎管理照護費', 'P58005', 200,
         '本項包含中醫護理衛教、營養飲食指導及經穴按摩指導，各項目皆須執行並於病歷詳細記載，方可申報費用。'),
        ('照護費', '特定癌症門診加強照護費(給藥日數7天以下)', 'P56001', 700,
         '包含中醫輔助醫療診察費、口服藥'),
        ('照護費', '特定癌症門診加強照護費(給藥日數8-14天)', 'P56002', 1050,
         '包含中醫輔助醫療診察費、口服藥'),
        ('照護費', '特定癌症門診加強照護費(給藥日數15-21天)', 'P56003', 1400,
         '包含中醫輔助醫療診察費、口服藥'),
        ('照護費', '特定癌症門診加強照護費(給藥日數22-28天)', 'P56004', 1750,
         '包含中醫輔助醫療診察費、口服藥'),
        ('照護費', '特定癌症針灸或傷科治療處置費', 'P56005', 400,
         '本項處置費每月申報上限為 12 次，超出部分支付點數以零計。'),
        ('照護費', '疾病管理照護費', 'P56006', 550,
         '1.包含中醫護理衛教及營養飲食指導。2.限三個月申報一次，申報此項目者，須參考衛教表單(如附件三)提供照護指導，並應併入病患之病歷紀錄備查。'),
        ('照護費', '生理評估費', 'P56007', 1000,
         '1.癌症治療功能性評估：一般性量表 2.生活品質評估。前測(收案三日內)及後測(收案三個月內)量表皆完成，方可申請給付。限三個月申報一次，並於病歷詳細載明評估結果。'),
    ]

    for row in rows:
        database.insert_record('charge_settings', fields, row)


def set_diag_share_basic_data(database):
    fields = ['ChargeType', 'ItemName', 'ShareType', 'TreatType', 'Course', 'InsCode', 'Amount', 'Remark']
    rows = [
        ('門診負擔', '一般內科', '基層醫療', '內科', '首次', 'S10', 50, None),
        ('門診負擔', '一般傷科首次', '基層醫療', '傷科治療', '首次', 'S10', 50, None),
        ('門診負擔', '一般傷科療程', '基層醫療', '傷科治療', '療程', 'S10', 50, None),
        ('門診負擔', '一般針灸首次', '基層醫療', '針灸治療', '首次', 'S10', 50, None),
        ('門診負擔', '一般針灸療程', '基層醫療', '針灸治療', '療程', '009', 0, None),

        ('門診負擔', '重大傷病內科', '重大傷病', '內科', '首次', '001', 0, None),
        ('門診負擔', '重大傷病傷科首次', '重大傷病', '傷科治療', '首次', '001', 0, None),
        ('門診負擔', '重大傷病傷科療程', '重大傷病', '傷科治療', '療程', '001', 0, None),
        ('門診負擔', '重大傷病針灸首次', '重大傷病', '針灸治療', '首次', '001', 0, None),
        ('門診負擔', '重大傷病針灸療程', '重大傷病', '針灸治療', '療程', '001', 0, None),

        ('門診負擔', '低收入戶內科', '低收入戶', '內科', '首次', '003', 0, None),
        ('門診負擔', '低收入戶傷科首次', '低收入戶', '傷科治療', '首次', '003', 0, None),
        ('門診負擔', '低收入戶傷科療程', '低收入戶', '傷科治療', '療程', '003', 0, None),
        ('門診負擔', '低收入戶針灸首次', '低收入戶', '針灸治療', '首次', '003', 0, None),
        ('門診負擔', '低收入戶針灸療程', '低收入戶', '針灸治療', '療程', '003', 0, None),

        ('門診負擔', '榮民內科', '榮民', '內科', '首次', '004', 0, None),
        ('門診負擔', '榮民傷科首次', '榮民', '傷科治療', '首次', '004', 0, None),
        ('門診負擔', '榮民傷科療程', '榮民', '傷科治療', '療程', '004', 0, None),
        ('門診負擔', '榮民針灸首次', '榮民', '針灸治療', '首次', '004', 0, None),
        ('門診負擔', '榮民針灸療程', '榮民', '針灸治療', '療程', '004', 0, None),

        ('門診負擔', '職業傷害內科', '職業傷害', '內科', '首次', '006', 0, None),
        ('門診負擔', '職業傷害傷科首次', '職業傷害', '傷科治療', '首次', '006', 0, None),
        ('門診負擔', '職業傷害傷科療程', '職業傷害', '傷科治療', '療程', '006', 0, None),
        ('門診負擔', '職業傷害針灸首次', '職業傷害', '針灸治療', '首次', '006', 0, None),
        ('門診負擔', '職業傷害針灸療程', '職業傷害', '針灸治療', '療程', '006', 0, None),

        ('門診負擔', '山地離島內科', '山地離島', '內科', '首次', '007', 0, None),
        ('門診負擔', '山地離島傷科首次', '山地離島', '傷科治療', '首次', '007', 0, None),
        ('門診負擔', '山地離島傷科療程', '山地離島', '傷科治療', '療程', '007', 0, None),
        ('門診負擔', '山地離島針灸首次', '山地離島', '針灸治療', '首次', '007', 0, None),
        ('門診負擔', '山地離島針灸療程', '山地離島', '針灸治療', '療程', '007', 0, None),

        ('門診負擔', '三歲兒童內科', '三歲兒童', '內科', '首次', '902', 0, None),
        ('門診負擔', '三歲兒童傷科首次', '三歲兒童', '傷科治療', '首次', '902', 0, None),
        ('門診負擔', '三歲兒童傷科療程', '三歲兒童', '傷科治療', '療程', '902', 0, None),
        ('門診負擔', '三歲兒童針灸首次', '三歲兒童', '針灸治療', '首次', '902', 0, None),
        ('門診負擔', '三歲兒童針灸療程', '三歲兒童', '針灸治療', '療程', '902', 0, None),

        ('門診負擔', '新生兒內科', '新生兒', '內科', '首次', '903', 0, None),
        ('門診負擔', '新生兒傷科首次', '新生兒', '傷科治療', '首次', '903', 0, None),
        ('門診負擔', '新生兒傷科療程', '新生兒', '傷科治療', '療程', '903', 0, None),
        ('門診負擔', '新生兒針灸首次', '新生兒', '針灸治療', '首次', '903', 0, None),
        ('門診負擔', '新生兒針灸療程', '新生兒', '針灸治療', '療程', '903', 0, None),

        ('門診負擔', '愛滋病內科', '愛滋病', '內科', '首次', '904', 0, None),
        ('門診負擔', '愛滋病傷科首次', '愛滋病', '傷科治療', '首次', '904', 0, None),
        ('門診負擔', '愛滋病傷科療程', '愛滋病', '傷科治療', '療程', '904', 0, None),
        ('門診負擔', '愛滋病針灸首次', '愛滋病', '針灸治療', '首次', '904', 0, None),
        ('門診負擔', '愛滋病針灸療程', '愛滋病', '針灸治療', '療程', '904', 0, None),

        ('門診負擔', '替代役男內科', '替代役男', '內科', '首次', '906', 0, None),
        ('門診負擔', '替代役男傷科首次', '替代役男', '傷科治療', '首次', '906', 0, None),
        ('門診負擔', '替代役男傷科療程', '替代役男', '傷科治療', '療程', '906', 0, None),
        ('門診負擔', '替代役男針灸首次', '替代役男', '針灸治療', '首次', '906', 0, None),
        ('門診負擔', '替代役男針灸療程', '替代役男', '針灸治療', '療程', '906', 0, None),
    ]
    for row in rows:
        database.insert_record('charge_settings', fields, row)


def set_drug_share_basic_data(database):
    fields = ['ChargeType', 'ItemName', 'ShareType', 'InsCode', 'Amount', 'Remark']
    rows = [
        ('藥品負擔', '藥費100點以下', '基層醫療', 'S10', 0, '<=100'),
        ('藥品負擔', '藥費101-200', '基層醫療', 'S20', 20, '<=200'),
        ('藥品負擔', '藥費201-300', '基層醫療', 'S20', 40, '<=300'),
        ('藥品負擔', '藥費301-400', '基層醫療', 'S20', 60, '<=400'),
        ('藥品負擔', '藥費401-500', '基層醫療', 'S20', 80, '<=500'),
        ('藥品負擔', '藥費501-600', '基層醫療', 'S20', 100, '<=600'),
        ('藥品負擔', '藥費601-700', '基層醫療', 'S20', 120, '<=700'),
        ('藥品負擔', '藥費701-800', '基層醫療', 'S20', 140, '<=800'),
        ('藥品負擔', '藥費801-900', '基層醫療', 'S20', 160, '<=900'),
        ('藥品負擔', '藥費901-1000', '基層醫療', 'S20', 180, '<=1000'),
        ('藥品負擔', '藥費1000以上', '基層醫療', 'S20', 200, '>1000'),
        ('藥品負擔', '重大傷病', '重大傷病', '001', 0, None),
        ('藥品負擔', '低收入戶', '低收入戶', '003', 0, None),
        ('藥品負擔', '榮民', '榮民', '004', 0, None),
        ('藥品負擔', '職業傷害', '職業傷害', '006', 0, None),
        ('藥品負擔', '山地離島', '山地離島', '007', 0, None),
        ('藥品負擔', '其他免部份負擔', '其他免部份負擔', '009', 0, '針灸療程2-6次, 百歲人瑞, 921震災'),
        ('藥品負擔', '三歲以下兒童', '三歲兒童', '902', 0, None),
        ('藥品負擔', '新生兒依附', '新生兒', '903', 0, None),
        ('藥品負擔', '愛滋病', '愛滋病', '904', 0, None),
        ('藥品負擔', '替代役男', '替代役男', '906', 0, None),
    ]
    for row in rows:
        database.insert_record('charge_settings', fields, row)


def set_regist_fee_basic_data(database):
    fields = ['ChargeType', 'ItemName', 'InsType', 'ShareType', 'TreatType', 'Course',
              'Amount', 'Remark']
    rows = [
        ('掛號費', '基本掛號費', '健保', '不分類', '不分類', '首次', 100, None),
        ('掛號費', '基本掛號費', '自費', '不分類', '不分類', '首次', 50, None),
        ('掛號費', '傷科調理費', '健保', '不分類', '不分類', '首次', 50, None),
        ('掛號費', '傷科調理費', '自費', '不分類', '不分類', '首次', 100, None),
        ('掛號費', '欠卡費', '健保', '不分類', '不分類', '首次', 500, None),
        ('掛號費', '內科掛號費', '健保', '基層醫療', '內科', '首次', 100, None),
        ('掛號費', '傷科首次掛號費', '健保', '基層醫療', '傷科治療', '首次', 100, None),
        ('掛號費', '傷科療程掛號費', '健保', '基層醫療', '傷科治療', '療程', 100, None),
        ('掛號費', '針灸首次掛號費', '健保', '基層醫療', '針灸治療', '首次', 100, None),
        ('掛號費', '針灸療程掛號費', '健保', '基層醫療', '針灸治療', '療程', 150, None),
        ('掛號費', '榮民內科掛號費', '健保', '榮民', '內科', '首次', 0, None),
        ('掛號費', '榮民傷科首次掛號費', '健保', '榮民', '傷科治療', '首次', 0, None),
        ('掛號費', '榮民傷科療程掛號費', '健保', '榮民', '傷科治療', '療程', 0, None),
        ('掛號費', '榮民針灸首次掛號費', '健保', '榮民', '針灸治療', '首次', 0, None),
        ('掛號費', '榮民針灸療程掛號費', '健保', '榮民', '針灸治療', '療程', 0, None),
        ('掛號費', '低收入戶內科掛號費', '健保', '低收入戶', '內科', '首次', 0, None),
        ('掛號費', '低收入戶傷科首次掛號費', '健保', '低收入戶', '傷科治療', '首次', 0, None),
        ('掛號費', '低收入戶傷科療程掛號費', '健保', '低收入戶', '傷科治療', '療程', 0, None),
        ('掛號費', '低收入戶針灸首次掛號費', '健保', '低收入戶', '針灸治療', '首次', 0, None),
        ('掛號費', '低收入戶針灸療程掛號費', '健保', '低收入戶', '針灸治療', '療程', 0, None),
    ]
    for row in rows:
        database.insert_record('charge_settings', fields, row)


def set_discount_basic_data(database):
    fields = ['ChargeType', 'ItemName', 'InsType', 'ShareType', 'TreatType',
              'Amount', 'Remark']
    rows = [
        ('掛號費優待', '年長病患', None, None, None, 0, None),
        ('掛號費優待', '殘障病患', None, None, None, 0, None),
        ('掛號費優待', '本院員工', None, None, None, 0, None),
        ('掛號費優待', '其他優待', None, None, None, 0, None),
    ]

    for row in rows:
        database.insert_record('charge_settings', fields, row)


def get_table_widget_item_fee(table_widget, row_no, col_no):
    fee = table_widget.item(row_no, col_no)
    try:
        if fee is not None:
            fee = number_utils.get_float(fee.text())
        else:
            fee = 0.0
    except ValueError:
        fee = 0.0
        item = QtWidgets.QTableWidgetItem()
        item.setData(QtCore.Qt.EditRole, fee)
        table_widget.setItem(row_no, col_no, item)

    return fee


# 取得抽成率 2019.05.28
def get_commission_rate(database, medicine_key, name):
    commission_rate = ''
    if medicine_key in [None, '']:
        return commission_rate

    sql = '''
        SELECT * FROM commission
        WHERE
            MedicineKey = {medicine_key} AND
            Name = "{name}"
    '''.format(
        medicine_key=medicine_key,
        name=name,
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        commission_rate = string_utils.xstr(rows[0]['Commission'])
        if commission_rate != '':
            return commission_rate

    sql = '''
        SELECT * FROM medicine
        WHERE
            MedicineKey = {medicine_key}
    '''.format(
        medicine_key=medicine_key,
    )
    rows = database.select_record(sql)
    medicine_type = None
    if len(rows) > 0:
        medicine_type = string_utils.xstr(rows[0]['MedicineType'])
        commission_rate = string_utils.xstr(rows[0]['Commission'])
        if commission_rate != '':
            return commission_rate

    if medicine_type is None:
        return commission_rate

    sql = '''
        SELECT * FROM dict_groups
        WHERE
            DictGroupsType = "藥品類別" AND
            DictGroupsName = "{dict_groups_name}"
    '''.format(
        dict_groups_name=medicine_type,
    )
    rows = database.select_record(sql)
    if len(rows) > 0:
        commission_rate = string_utils.xstr(rows[0]['DictGroupsLevel2'])
        if commission_rate != '':
            return '{0}%'.format(commission_rate)

    return commission_rate


# 計算抽成 2019.05.28
def calc_commission(quantity, amount, commission_rate):
    if '%' in commission_rate:
        commission_rate = number_utils.get_float(commission_rate.strip('%'))
        commission = amount * commission_rate / 100
    else:
        commission_rate = number_utils.get_float(commission_rate)
        commission = quantity * commission_rate

    commission = number_utils.round_up(commission)

    return commission


# 計算折扣
def get_discount_fee(system_settings, self_total_fee, discount_rate):
    if discount_rate == 100:
        return 0

    discount_fee = int(self_total_fee - (self_total_fee * discount_rate / 100))
    total_fee = self_total_fee - discount_fee
    remainder = total_fee % 10  # 個位數
    rounded_type = system_settings.field('自費折扣進位')
    remainder_type = system_settings.field('自費折扣尾數')
    rounded_total_fee = total_fee

    if rounded_type == '四捨五入':
        rounded_total_fee = round(total_fee, -1)
    elif rounded_type == '無條件進位':
        if remainder_type == '尾數為0':
            rounded_total_fee = total_fee + (10 - remainder)
        else:  # 尾數為0或5
            if remainder in [0, 5]:  # 尾數剛好, 不用調整
                rounded_total_fee = total_fee
            elif remainder < 5:
                rounded_total_fee = total_fee + (5 - remainder)
            elif remainder > 5:
                rounded_total_fee = total_fee + (10 - remainder)
    elif rounded_type == '無條件捨去':
        if remainder_type == '尾數為0':
            rounded_total_fee = total_fee - remainder
        else:
            if remainder in [0, 5]:  # 尾數剛好, 不用調整
                rounded_total_fee = total_fee
            elif remainder < 5:
                rounded_total_fee = total_fee - remainder
            elif remainder > 5:
                rounded_total_fee = total_fee - (remainder - 5)

    discount_fee += number_utils.get_integer(total_fee - rounded_total_fee)

    return discount_fee


# 計算折扣
def get_amount(system_settings, amount, discount_rate):
    if discount_rate == 100:
        return amount

    total_amount = amount - (amount * discount_rate / 100)
    remainder = total_amount % 10  # 個位數
    rounded_type = system_settings.field('自費折扣進位')
    remainder_type = system_settings.field('自費折扣尾數')
    rounded_total_fee = total_amount

    if rounded_type == '四捨五入':
        rounded_total_fee = round(total_amount, -1)
    elif rounded_type == '無條件進位':
        if remainder_type == '尾數為0':
            rounded_total_fee = total_amount + (10 - remainder)
        else:  # 尾數為0或5
            if remainder in [0, 5]:  # 尾數剛好, 不用調整
                rounded_total_fee = total_amount
            elif remainder < 5:
                rounded_total_fee = total_amount + (5 - remainder)
            elif remainder > 5:
                rounded_total_fee = total_amount + (10 - remainder)
    elif rounded_type == '無條件捨去':
        if remainder_type == '尾數為0':
            rounded_total_fee = total_amount - remainder
        else:
            if remainder in [0, 5]:  # 尾數剛好, 不用調整
                rounded_total_fee = total_amount
            elif remainder < 5:
                rounded_total_fee = total_amount - remainder
            elif remainder > 5:
                rounded_total_fee = total_amount - (remainder - 5)

    amount_fee = number_utils.get_integer(total_amount - rounded_total_fee)

    return amount_fee


# 取得自費金額
def get_self_total_fee(database, case_key):
    sql = '''
        SELECT * FROM prescript
        WHERE
            CaseKey = {case_key} AND
            MedicineSet >= 2
        ORDER BY MedicineSet, PrescriptKey
    '''.format(
        case_key=case_key,
    )

    rows = database.select_record(sql)

    self_total_fee = 0
    for row in rows:
        dosage = number_utils.get_float(row['Dosage'])
        price = number_utils.get_float(row['Price'])
        pres_days = case_utils.get_pres_days(database, case_key, row['MedicineSet'])
        if pres_days <= 0:
            pres_days = 1

        amount = dosage * price
        subtotal = get_subtotal_fee(amount, pres_days)
        self_total_fee += subtotal

    return self_total_fee
