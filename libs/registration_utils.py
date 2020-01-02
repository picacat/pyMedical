# 2018-03-27 掛號作業用

from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
from libs import nhi_utils
from libs import number_utils
from libs import string_utils


# 取得班別
def get_current_period(system_settings):
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


# 取得今日最後的診號
def get_last_reg_no(database, system_settings, start_date, end_date, period, room):
    sql = '''
        SELECT RegistNo FROM cases 
        WHERE 
            CaseDate BETWEEN "{0}" AND "{1}" AND
            RegistNo >= 0
    '''.format(
        start_date, end_date
    )

    if system_settings.field('分診') == 'Y':
        sql += ' AND Room = {0}'.format(room)

    if system_settings.field('分班') == 'Y':
        sql += ' AND Period = "{0}"'.format(period)

    if system_settings.field('現場掛號給號模式') == '預約班表':
        sql += ' AND RegistType = "一般門診"'  # 一定要讀現場號，否則預約報到後，現場號會變成預約號之後, 早成中間許多現場號空號

    sql += ' ORDER BY RegistNo DESC LIMIT 1'
    rows = database.select_record(sql)

    if len(rows) > 0:
        last_reg_no = rows[0]['RegistNo']
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
            return 0

    return last_reg_no


# 取得診號
def get_reg_no(database, system_settings, room, doctor, period=None, reserve_key=None):
    if reserve_key is not None:
        sql = '''
            SELECT * FROM reserve
            WHERE
                ReserveKey = {0}
        '''.format(reserve_key)
        rows = database.select_record(sql)
        if len(rows) > 0:
            return number_utils.get_integer(rows[0]['ReserveNo'])

    start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
    end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')
    if period is None:
        period = get_current_period(system_settings)

    last_reg_no = get_last_reg_no(
        database, system_settings, start_date, end_date,
        period, room
    )

    reg_no = get_reg_no_by_mode(database, system_settings, period, room, doctor, last_reg_no)

    return int(reg_no)


# 診號模式
def get_reg_no_by_mode(database, system_settings, period, room, doctor, reg_no):
    if system_settings.field('現場掛號給號模式') == '雙號':
        if reg_no % 2 == 1:
            reg_no += 1
        else:
            reg_no += 2
    elif system_settings.field('現場掛號給號模式') == '單號':
        if number_utils.get_integer(reg_no) % 2 == 0:
            reg_no += 1
        else:
            reg_no += 2
    elif system_settings.field('現場掛號給號模式') == '預約班表':
        period_condition = ''
        doctor_condition = ''
        if period is not None:
            period_condition = 'AND Period = "{0}"'.format(period)
        if doctor is not None:
            doctor_condition = 'AND Doctor = "{0}"'.format(doctor)

        reg_no += 1
        sql = '''
            SELECT * FROM reservation_table
            WHERE
                ReserveNo >= {reg_no} 
                {period_condition}
                {doctor_condition}
            ORDER BY ReserveNo 
        '''.format(
            reg_no=reg_no,
            room=room,
            period_condition=period_condition,
            doctor_condition=doctor_condition,
        )
        rows = database.select_record(sql)
        for row in rows:
            if reg_no != row['ReserveNo']:
                break

            if system_settings.field('釋出預約號') == 'Y':
                if check_release_reserve_no(database, room, period, doctor, reg_no):  # 可以釋出預約號, 不再繼續往下檢查
                    break

            reg_no += 1
    else:
        reg_no += 1

    return reg_no


# 2019.03.12 檢查是否可以釋出預約號碼 (只檢查今日，其他日期不可佔用)
def check_release_reserve_no(database, room, period, doctor, reg_no):
    release_reserve_no = False

    start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
    end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

    sql = '''
        SELECT * FROM reserve 
        WHERE
            ReserveDate BETWEEN "{start_date}" AND "{end_date}" AND
            Period = "{period}" AND
            Doctor = "{doctor}" AND
            ReserveNo = {reg_no}
    '''.format(
        start_date=start_date,
        end_date=end_date,
        room=room,
        period=period,
        doctor=doctor,
        reg_no=reg_no,
    )

    rows = database.select_record(sql)

    if len(rows) <= 0:  # 無人佔用, 可以釋出
        release_reserve_no = True

    return release_reserve_no


# 檢查健保重複就診
def check_record_duplicated(database, patient_key, case_date):
    start_date = case_date.strftime('%Y-%m-%d 00:00:00')
    end_date = case_date.strftime('%Y-%m-%d 23:59:59')
    sql = '''
        SELECT * FROM cases 
        WHERE 
            PatientKey = {patient_key} AND 
            CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
            InsType = "健保"
    '''.format(
        patient_key=patient_key,
        start_date=start_date,
        end_date=end_date,
    )
    rows = database.select_record(sql)
    if len(rows) > 0:
        return True
    else:
        return False


# 取得當月健保針傷門診就診次數
def get_treat_times(database, patient_key):
    start_date = datetime.datetime.now().strftime("%Y-%m-01 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")

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
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")

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
    diag_fee_times = get_diag_fee_times(database, patient_key)
    diag_fee_times_limit = number_utils.get_integer(system_settings.field('首次警告次數'))
    if diag_fee_times >= diag_fee_times_limit:
        message = '* 診察次數警告: 本月診察次數共{0}次, 已達系統設定{1}次的限制.<br>'.format(
            diag_fee_times, diag_fee_times_limit)

    return message


# 檢查欠卡
def check_deposit(database, system_settings, patient_key):
    message = None
    present = datetime.datetime.now()
    if system_settings.field('欠卡日期檢查範圍') == '10天前':
        start_date = (present - datetime.timedelta(days=9)).strftime("%Y-%m-%d 00:00:00")  # 10天內未還卡
    elif system_settings.field('欠卡日期檢查範圍') == '本月1日':
        start_date = datetime.date(present.year, present.month, 1).strftime("%Y-%m-%d 00:00:00")  # 本月1日
    elif system_settings.field('欠卡日期檢查範圍') == '上個月20日':
        start_date = datetime.date(present.year, present.month, 1) - datetime.timedelta(10)  # 至上個月20日
        start_date = start_date.strftime("%Y-%m-%d 00:00:00")
    else:
        start_date = datetime.date(present.year, present.month, 1) - datetime.timedelta(1)  # 至上個月1日
        start_date = start_date.strftime("%Y-%m-01 00:00:00")

    end_date = (present - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
    sql = '''
        SELECT CaseDate FROM cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        (Card = "欠卡") 
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    if len(rows) > 0:
        row = rows[0]
        message = '* 欠卡提醒: {year}年{month}月{day}日門診尚有欠卡未還.'.format(
            year=row['CaseDate'].year,
            month=row['CaseDate'].month,
            day=row['CaseDate'].day,
        )

    return message


# 檢查欠款
def check_debt(database, patient_key):
    message = None

    sql = '''
        SELECT * FROM debt 
        WHERE
            PatientKey = {patient_key} AND
            Fee > 0 AND
            ReturnDate1 IS NULL 
    '''.format(
        patient_key=patient_key,
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        message = ''
        for row in rows:
            message += '* 欠款提醒: {case_date} 門診尚有{debt_type} {debt} 未還.<br>'.format(
                case_date=row['CaseDate'].strftime('%Y-%m-%d'),
                debt_type=string_utils.xstr(row['DebtType']),
                debt=row['Fee']
            )

    return message


# 檢查昨日內科或新療程刷卡
def check_card_yesterday(database, patient_key, course=None):
    message = None

    if number_utils.get_integer(course) >= 2:  # 療程無隔日過卡問題, 不檢查
        return message

    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
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
def check_prescription_finished(database, case_key, patient_key, in_date=None):
    message = None
    if in_date is None:
        in_date = datetime.date.today()
    else:
        in_date = in_date.date()

    if case_key is None:
        case_condition = ''
    else:
        case_condition = '(cases.CaseKey != {case_key}) AND '.format(case_key=case_key)

    end_date = (in_date - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
    sql = '''
        SELECT cases.CaseDate, cases.Name, dosage.Days FROM cases
        LEFT JOIN dosage on dosage.CaseKey = cases.CaseKey
        WHERE
            {case_condition}
            (cases.PatientKey = {patient_key}) AND
            (cases.CaseDate <= "{end_date}") AND
            (cases.InsType = "健保") AND
            (dosage.MedicineSet = 1) AND (dosage.Days > 0)
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(
        case_condition=case_condition,
        case_key=case_key,
        patient_key=patient_key,
        end_date=end_date,
    )
    rows = database.select_record(sql)

    if len(rows) > 0:
        row = rows[0]
        prescription_days = number_utils.get_integer(row['Days'])
        last_prescription_date = row['CaseDate'].date()
        days = (in_date - last_prescription_date).days  # 已服用天數 (給藥當日也算一日)
        remain_days = prescription_days - days  # 剩餘藥日
        if remain_days > 0:  # 藥還有剩
            message = '* 用藥檢查: {name}在{case_date}開了{pres_days}日藥, 到目前尚有{remain_days}日藥未服用完畢.'.format(
                name=string_utils.xstr(row['Name']),
                case_date=rows[0]['CaseDate'].strftime('%Y-%m-%d'),
                pres_days=prescription_days,
                remain_days=remain_days,
            )

    return message


# 療程未完成
def check_course_complete(database, patient_key, course):
    message = None

    if number_utils.get_integer(course) >= 2:  # 療程無問題, 不檢查
        return message

    start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
    sql = '''
        SELECT CaseDate, Card, Continuance FROM cases 
        WHERE
            (PatientKey = {0}) AND
            (CaseDate BETWEEN "{1}" AND "{2}") AND
            (InsType = "健保") AND
            (Continuance >= 1)
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(patient_key, start_date, end_date, tuple(nhi_utils.INS_TREAT))
    rows = database.select_record(sql)

    if len(rows) <= 0:
        return message

    row = rows[0]
    card = string_utils.xstr(row['Card'])
    course = number_utils.get_integer(row['Continuance'])

    if course >= 6:  # 療程已經完成
        return message

    if check_course_complete_in_days(database, patient_key, card, course, 30) is not None:  # 療程還沒有超過30天
        return message

    message = '* 療程提醒: {0}只到療程{1}, 尚未完成全部療程.<br>'.format(
        row['CaseDate'].date(), course,
    )

    return message


# 同療程days日未完成
def check_course_complete_in_days(database, patient_key, card, course, days):
    message = None

    course = number_utils.get_integer(course)
    if course <= 1:  # 療程首次或內科不檢查
        return message

    start_date = (datetime.datetime.now() - datetime.timedelta(days=days-1)).strftime("%Y-%m-%d 00:00:00")
    end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
    sql = '''
        SELECT Continuance FROM cases WHERE
        (PatientKey = {0}) AND
        (CaseDate BETWEEN "{1}" AND "{2}") AND
        (InsType = "健保") AND
        (Card = "{3}") AND
        (Continuance = 1)
        ORDER BY CaseDate DESC LIMIT 1
    '''.format(patient_key, start_date, end_date, card)
    rows = database.select_record(sql)

    if len(rows) <= 0:  # 找不到代表療程已經不在天數內，已過期 例如: 30天內有找到第一次, 代表療程第一次到現在還沒超過30天
        message = '* 療程提醒: 療程已超過{0}日, 尚未完成全部療程.<br>'.format(days)

    return message


# 取得診別
def get_room(database, period, doctor):
    room = 1

    week_day_list = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ]

    today = datetime.datetime.now().weekday()
    weekday = week_day_list[today]

    sql = '''
        SELECT * FROM doctor_schedule
        WHERE
            Period = "{period}" AND
            {weekday} = "{doctor}"
    '''.format(
        period=period,
        weekday=weekday,
        doctor=doctor,
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return room

    room = rows[0]['Room']

    return room

# 取得醫師
def get_doctor(database, period, room):
    week_day_list = [
        'Monday',
        'Tuesday',
        'Wednesday',
        'Thursday',
        'Friday',
        'Saturday',
        'Sunday',
    ]

    today = datetime.datetime.now().weekday()
    weekday = week_day_list[today]

    sql = '''
        SELECT * FROM doctor_schedule
        WHERE
            Period = "{period}" AND
            room = "{room}"
    '''.format(
        period=period,
        room=room,
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return room

    try:
        doctor = string_utils.xstr(rows[0][weekday])
    except:
        doctor = ''

    return doctor


# 檢查預約是否已滿
def is_reservation_full(database, reservation_date, period, reserve_no, doctor):
    is_full = False

    reservation_date = reservation_date.split(' ')[0]
    start_date = '{reservation_date} 00:00:00'.format(reservation_date=reservation_date)
    end_date = '{reservation_date} 23:59:59'.format(reservation_date=reservation_date)

    sql = '''
        SELECT ReserveKey FROM reserve
        WHERE
            ReserveDate BETWEEN "{start_date}" AND "{end_date}" AND
            Period = "{period}" AND
            ReserveNo = {reserve_no} AND
            Doctor = "{doctor}"
    '''.format(
        start_date=start_date,
        end_date=end_date,
        period=period,
        reserve_no=reserve_no,
        doctor=doctor,
    )

    rows = database.select_record(sql)

    if len(rows) > 0:
        is_full = True

    return is_full


# Monday=0, Tuesday=1...Sunday=6
def get_doctor_schedule(database, room, period):
    if room is None:
        room = 1

    sql = '''
        SELECT * FROM doctor_schedule
        WHERE
            Room = {room} AND
            Period = "{period}" 
    '''.format(
        room=room,
        period=period,
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return None

    row = rows[0]
    doctor_list = [
        string_utils.xstr(row['Monday']),
        string_utils.xstr(row['Tuesday']),
        string_utils.xstr(row['Wednesday']),
        string_utils.xstr(row['Thursday']),
        string_utils.xstr(row['Friday']),
        string_utils.xstr(row['Saturday']),
        string_utils.xstr(row['Sunday']),
    ]

    today = datetime.datetime.now().weekday()

    return doctor_list[today]

