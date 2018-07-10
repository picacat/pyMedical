# 取得各項費用金額

from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import number_utils
from libs import string_utils
from libs import nhi_utils


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
        regist_fee = number_utils.get_integer(row['Amount'])

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
def get_regist_fee(database, discount_type, ins_type, share_type, treat_type, course=None):
    if string_utils.xstr(discount_type) != '':  # 掛號費優待優先取得
        regist_fee = _get_regist_discount_fee(database, discount_type)
        return regist_fee

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

    return regist_fee


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


# 取得門診負擔
def get_diag_share_fee(database, share_type, treat_type, course):
    diag_share_fee = 0
    course_type = nhi_utils.get_course_type(course)
    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" AND 
            ShareType = "{0}" AND TreatType = "{1}" AND Course = "{2}"
          '''.format(share_type, treat_type, course_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return diag_share_fee

    if len(row) > 0:
        diag_share_fee = number_utils.get_integer(row['Amount'])

    return diag_share_fee


# 取得藥品負擔
def get_drug_share_fee(database, share_type, ins_drug_fee):
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

    return drug_share_fee


# 取得門診負擔
def get_traditional_health_care_fee(database, ins_type, massager):
    traditional_health_care_fee = 0

    if massager is None or massager == '':
        return traditional_health_care_fee

    sql = '''
            SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" AND 
            ItemName = "民俗調理費" AND InsType = "{0}"
          '''.format(ins_type)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return traditional_health_care_fee

    if len(row) > 0:
        traditional_health_care_fee = number_utils.get_integer(row['Amount'])

    return traditional_health_care_fee


# 取得健保門診診察費
# 取第一段診察費, 分有無護理人員, 支援醫師等到申報才調整
def get_ins_diag_fee(database, system_settings):
    ins_diag_fee = 0

    nurse = system_settings.field('護士人數')
    if int(nurse) > 0:
        diag_code = 'A01'
    else:
        diag_code = 'A02'

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(diag_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_diag_fee

    ins_diag_fee = row[0]['Amount']

    return ins_diag_fee


# 取得健保藥費
# 藥費 = 每日藥費 * 給藥天數
def get_ins_drug_fee(database, pres_days):
    ins_drug_fee = 0

    if pres_days == 0:
        return ins_drug_fee

    drug_code = 'A21'
    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(drug_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_drug_fee

    ins_drug_fee = row[0]['Amount'] * pres_days

    return ins_drug_fee


# 取得健保調劑費
# 調劑費 = 0: 不申報調劑費, 沒有申報藥費
# 調劑費 > 0: 藥師調劑, 醫師調劑
def get_ins_pharmacy_fee(database, system_settings, ins_drug_fee):
    ins_pharmacy_fee = 0

    if ins_drug_fee == 0:
        return ins_pharmacy_fee

    if system_settings.field('申報藥事服務費') == 'N':
        return ins_pharmacy_fee

    pharmacist = system_settings.field('藥師人數')
    if int(pharmacist) > 0:
        pharmacy_code = 'A31'
    else:
        pharmacy_code = 'A32'

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(pharmacy_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_pharmacy_fee

    ins_pharmacy_fee = row[0]['Amount']

    return ins_pharmacy_fee


# 取得健保針灸費
def get_ins_acupuncture_fee(database, treatment, ins_drug_fee):
    ins_acupuncture_fee = 0

    if treatment not in nhi_utils.ACUPUNCTURE_DRUG_DICT:
        return ins_acupuncture_fee

    if ins_drug_fee > 0:
        acupuncture_code = nhi_utils.ACUPUNCTURE_DRUG_DICT[treatment]
    else:
        acupuncture_code = nhi_utils.ACUPUNCTURE_DICT[treatment]

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(acupuncture_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_acupuncture_fee

    ins_acupuncture_fee = row[0]['Amount']

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

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(massage_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_massage_fee

    ins_massage_fee = row[0]['Amount']

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

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(dislocate_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_dislocate_fee

    ins_dislocate_fee = row[0]['Amount']

    return ins_dislocate_fee


# 取得健保加強照護費
def get_ins_care_fee(database, treatment):
    ins_care_fee = 0

    if treatment not in nhi_utils.CARE_TREAT:
        return ins_care_fee

    care_code = nhi_utils.CARE_DICT[treatment]

    sql = '''
        SELECT * FROM charge_settings WHERE
        InsCode = "{0}"
    '''.format(care_code)
    row = database.select_record(sql)
    if len(row) <= 0:
        return ins_care_fee

    ins_care_fee = row[0]['Amount']

    return ins_care_fee


# 取得健保代辦費
def get_ins_agent_fee(database, share_type, treatment, course, ins_drug_fee):
    ins_agent_fee = 0

    if share_type in ['重大傷病', '山地離島']:  # 重大傷病, 山地離島: 無代辦費
        return ins_agent_fee

    if share_type in nhi_utils.AGENT_SHARE:
        diag_share_fee = get_diag_share_fee(  # 以基層醫療為代辦基礎
            database,
            '基層醫療',
            nhi_utils.get_treat_type(treatment),
            course
        )
        drug_share_fee = get_drug_share_fee(
            database,
            '基層醫療',
            ins_drug_fee)
        ins_agent_fee = diag_share_fee + drug_share_fee

    return ins_agent_fee
