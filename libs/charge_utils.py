# 取得各項費用金額

from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import number


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


# 取得掛號費
def get_regist_fee(database, ins_type, share_type, treat_type, card=None, course=None):
    regist_fee = _get_basic_regist_fee(database, ins_type)

    if card == '欠卡':
        sql = '''
                SELECT * FROM charge_settings WHERE ChargeType = "掛號費" AND ItemName = "欠卡費"
              '''
    else:
        if 2 <= number.get_integer(course) <= 6:
            course = '療程'
        else:
            course = '首次'

        sql = '''
                SELECT * FROM charge_settings WHERE ChargeType = "掛號費" AND 
                InsType = "{0}" AND ShareType = "{1}" AND 
                TreatType = "{2}" AND Course = "{3}" 
              '''.format(ins_type, share_type, treat_type, course)
    try:
        row = database.select_record(sql)[0]
    except IndexError:
        return regist_fee

    if len(row) > 0:
        regist_fee = number.get_integer(row['Amount'])

    return regist_fee

