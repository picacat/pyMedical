# 取得各項費用金額

from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import number
from libs import strings
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
        regist_fee = number.get_integer(row['Amount'])

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
        discount_fee = number.get_integer(row['Amount'])

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
        discount_fee = number.get_integer(row['Amount'])

    return discount_fee


# 取得掛號費
def get_regist_fee(database, discount_type, ins_type, share_type, treat_type, course=None):
    if strings.xstr(discount_type) != '':  # 掛號費優待優先取得
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
        regist_fee = number.get_integer(row['Amount'])

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
        deposit_fee = number.get_integer(row['Amount'])

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
        diag_share_fee = number.get_integer(row['Amount'])

    return diag_share_fee


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
        traditional_health_care_fee = number.get_integer(row['Amount'])

    return traditional_health_care_fee
