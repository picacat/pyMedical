# 2018-03-27 掛號作業用

from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
from libs import nhi_utils
from libs import number_utils


# 取得班別
def get_period(system_settings):
    current_time = datetime.datetime.now().strftime('%H:%M')
    try:
        if current_time >= system_settings.field('晚班時間'):
            period = '晚班'
        elif current_time >= system_settings.field('午班時間'):
            period = '午班'
        else:
            period = '早班'
    except TypeError:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('讀取班別資料失敗')
        msg_box.setText("無法取得系統班別時間, 無法產生班別資料.")
        msg_box.setInformativeText("請檢查[系統設定]->[院所設定]->[班別時間設定]的早午晚班別時間設定.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
        return

    return period


# 診號模式
def get_reg_no_by_mode(system_settings, reg_no):
    if system_settings.field('現場掛號給號模式') == '雙號':
        if reg_no % 2 == 1:
            reg_no += 1
        else:
            reg_no += 2
    elif system_settings.field('現場掛號給號模式') == '單號':
        if reg_no % 2 == 0:
            reg_no += 1
        else:
            reg_no += 2
    else:
        reg_no += 1

    return reg_no


# 取得診號
def get_reg_no(database, system_settings, room, period=None):
    start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
    end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')
    if period is None:
        period = get_period(system_settings)

    script = 'select RegistNo from cases where CaseDate between "{0}" and "{1}"'.format(
        start_date, end_date)

    if system_settings.field('分診') == 'Y':
        script += ' and Room = {0}'.format(room)

    if system_settings.field('分班') == 'Y':
        script += ' and Period = "{0}"'.format(period)

    script += ' order by RegistNo desc limit 1'
    row = database.select_record(script)
    row_count = len(list(row))

    if row_count > 0:
        last_reg_no = row[0]['RegistNo']
    else:
        if system_settings.field('分班') == 'Y':
            reg_no = system_settings.field('{0}起始號'.format(period))
        else:
            reg_no = system_settings.field('早班起始號'.format(period))

        try:
            last_reg_no = int(reg_no) - 1
        except TypeError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('讀取診號起始號資料失敗')
            msg_box.setText("無法取得班別起始號資料, 無法產生診號.")
            msg_box.setInformativeText("請檢查[系統設定]->[診號控制]->[給號方式]的早午晚班起始號設定.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

    reg_no = get_reg_no_by_mode(system_settings, last_reg_no)

    return int(reg_no)


# 檢查重複就診
def check_record_duplicated(database, patient_key, case_date):
    start_date = case_date.strftime('%Y-%m-%d 00:00:00')
    end_date = case_date.strftime('%Y-%m-%d 23:59:59')
    sql = '''
        SELECT * FROM cases WHERE PatientKey = {0} and 
        CaseDate BETWEEN "{1}" and "{2}" 
    '''.format(patient_key, start_date, end_date)
    rows = database.select_record(sql)
    if len(rows) > 0:
        return True
    else:
        return False


# 取得當月健保針傷門診就診次數
def get_treat_times(database, patient_key):
    start_date = datetime.datetime.now().strftime("%Y-%m-01 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")

    sql = '''
        SELECT CaseKey from cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        (Continuance between 1 AND 6) AND
        (TreatType in {3})
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    return len(rows)


# 檢查當月健保針傷門診就診次數
def check_treat_times(database, system_settings, patient_key):
    message = None
    treat_times = get_treat_times(database, patient_key)
    treat_times_limit = number_utils.get_integer(system_settings.field('針傷警告次數'))
    if treat_times >= treat_times_limit:
        message = '* 針傷次數警告: 本月針傷次數共{0}次, 已達系統設定{1}次的限制.<br>'.format(
            treat_times, treat_times_limit)

    return message


# 取得當月健保有診察費就診次數
def get_diag_fee_times(database, patient_key):
    start_date = datetime.datetime.now().strftime("%Y-%m-01 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")

    sql = '''
        SELECT CaseKey from cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        ((Continuance IS NULL) OR (Continuance <= 1)) AND
        (DiagFee > 0)
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    return len(rows)


# 檢查當月健保有診察費就診次數
def check_diag_fee_times(database, system_settings, patient_key):
    message = None
    diag_fee_times = get_treat_times(database, patient_key)
    diag_fee_times_limit = number_utils.get_integer(system_settings.field('首次警告次數'))
    if diag_fee_times >= diag_fee_times_limit:
        message = '* 診察次數警告: 本月診察次數共{0}次, 已達系統設定{1}次的限制.<br>'.format(
            diag_fee_times, diag_fee_times_limit)

    return message


# 檢查欠卡
def check_deposit(database, patient_key):
    message = None
    start_date = datetime.datetime.now().strftime("%Y-%m-01 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")
    sql = '''
        SELECT CaseDate FROM cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        (Card = "欠卡") 
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    if len(rows) > 0:
        message = '* 欠卡提醒: 本月{0}門診尚有欠卡未還.<br>'.format(rows[0]['CaseDate'].strftime('%m月%d日'))

    return message


# 檢查欠款
def check_debt(database, patient_key):
    message = None
    sql = '''
        SELECT CaseDate, DebtFee FROM cases WHERE
        (PatientKey = {0}) AND
        (DebtFee > 0)
    '''.format(patient_key)
    rows = database.select_record(sql)

    if len(rows) > 0:
        message = '* 欠款提醒: {0}門診尚有欠款{1}未還.<br>'.format(
            rows[0]['CaseDate'].strftime('%Y-%m-%d'),
            rows[0]['DebtFee'])

    return message


# 檢查昨日內科或新療程刷卡
def check_card_yesterday(database, patient_key, course=None):
    message = None

    if number_utils.get_integer(course) >= 2:  # 療程無隔日過卡問題, 不檢查
        return message

    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")
    sql = '''
        SELECT CaseKey FROM cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        ((Continuance IS NULL) OR (Continuance <= 1))
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    if len(rows) > 0:
        message = '* 隔日過卡提醒: 昨日門診有內科或新開療程.<br>'

    return message


# 檢查上次給藥是否用完
def check_prescription_finished(database, patient_key):
    message = None
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")
    sql = '''
        SELECT cases.CaseDate, dosage.Days FROM cases
        LEFT JOIN dosage on dosage.CaseKey = cases.CaseKey
        WHERE
        (cases.PatientKey = {0}) AND
        (cases.CaseDate <= "{1}") AND
        (cases.InsType = "健保") AND
        (dosage.Days > 0)
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(patient_key, end_date)
    rows = database.select_record(sql)

    if len(rows) > 0:
        prescription_days = number_utils.get_integer(rows[0]['Days'])
        today = datetime.date.today()
        last_prescription_date = (rows[0]['CaseDate']).date()
        days = (today - last_prescription_date).days + 1  # 給藥當日也算一日
        if prescription_days > days:
            message = '* 用藥檢查: {0}給藥尚有{1}日藥未服用完畢.'.format(
                rows[0]['CaseDate'].strftime('%Y-%m-%d'),
                (prescription_days-days))

    return message


# 療程未完成
def check_course_complete(database, patient_key, course):
    message = None

    if number_utils.get_integer(course) >= 2:  # 療程無問題, 不檢查
        return message

    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")
    sql = '''
        SELECT CaseDate, Continuance FROM cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        (Continuance >= 1)
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    if len(rows) > 0:
        if number_utils.get_integer(rows[0]['Continuance']) <= 5:
            message = '* 療程提醒: {0}只到療程{1}, 尚未完成全部療程.<br>'.format(
                rows[0]['CaseDate'].date(),
                rows[0]['Continuance']
            )

    return message


# 療程14日未完成
def check_course_complete_in_two_weeks(database, patient_key, card, course):
    message = None

    if number_utils.get_integer(course) <= 1:  # 療程首次或內科不檢查
        return message

    start_date = (datetime.datetime.now() - datetime.timedelta(days=14)).strftime("%Y-%m-%d 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:49:59")
    sql = '''
        SELECT Continuance FROM cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        (Card = "{3}") AND
        (Continuance = 1)
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(patient_key, start_date, end_date, card)
    print(sql)
    rows = database.select_record(sql)

    if len(rows) <= 0:
        message = '* 療程提醒: 療程已超過14日, 尚未完成全部療程.<br>'

    return message
