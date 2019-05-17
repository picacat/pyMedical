
from libs import string_utils


PERMISSION_LIST = [
    ['門診掛號', '執行門診掛號'],
    ['門診掛號', '修正候診名單'],
    ['門診掛號', '刪除候診名單'],
    ['門診掛號', '病患資料修正'],
    ['門診掛號', '初診掛號'],
    ['門診掛號', '清除非本日候診名單'],
    ['門診掛號', '開啟雲端藥歷'],
    ['門診掛號', '健保卡掛號'],
    ['門診掛號', '健保卡退掛'],
    ['門診掛號', '健保卡寫卡'],
    ['門診掛號', '補印收據'],

    ['預約掛號', '執行預約掛號'],
    ['批價作業', '執行批價作業'],
    ['健保卡欠還卡', '執行健保卡欠還卡'],
    ['欠還款作業', '執行欠還款作業'],
    ['櫃台購藥', '執行櫃台購藥'],
    ['掛號櫃台結帳', '執行掛號櫃台結帳'],
    ['病患查詢', '執行病患查詢'],
    ['健保IC卡資料上傳', '執行健保IC卡資料上傳'],
    ['醫師看診作業', '執行醫師看診作業'],
    ['病歷查詢', '執行病歷查詢'],
    ['病歷統計', '執行病歷統計'],
    ['系統設定', '執行系統設定'],
    ['收費設定', '執行收費設定'],
    ['診察資料', '執行診察資料'],
    ['處方資料', '執行處方資料'],
    ['健保卡讀卡機', '執行健保卡讀卡機'],

    ['醫師班表', '執行醫師班表'],
    ['護士跟診表', '執行護士跟診表'],
    ['使用者管理', '執行使用者管理'],
    ['健保藥品', '執行健保藥品'],

    ['匯出電子病歷交換檔', '執行匯出電子病歷交換檔'],
    ['醫療軟體更新', '執行醫療軟體更新'],

    ['診斷證明書', '執行診斷證明書'],
    ['醫療費用證明書', '執行醫療費用證明書'],

    ['申報檢查', '執行申報檢查'],
    ['健保申報', '執行健保申報'],
    ['健保抽審', '執行健保抽審'],

    ['醫師統計', '執行醫師統計'],
    ['回診率統計', '執行回診率統計'],
]


# 取得醫事人員名單
def get_personnel(database, personnel_type):
    if personnel_type == '全部':
        position = ''
    elif personnel_type == '醫師':
        position = 'WHERE (Position IN("醫師", "支援醫師"))'
    else:
        position = 'WHERE Position = "{0}"'.format(personnel_type)
    sql = '''
        SELECT * FROM person {0}
        ORDER BY PersonKey
    '''.format(position)
    rows = database.select_record(sql)

    personnel_list = []
    for row in rows:
        personnel_list.append(string_utils.xstr(row['Name']))

    return personnel_list


def get_personnel_field_value(database, name, field):
    if string_utils.xstr(name) == '':
        return ''

    sql = '''
        SELECT * FROM person WHERE
        Name = "{0}"
    '''.format(name)
    rows = database.select_record(sql)

    if len(rows) <= 0:
        return ''
    else:
        return string_utils.xstr(rows[0][field])


def get_doctor_nurse(database, schedule_date, period, doctor):
    nurse_name = ''
    sql = '''
        SELECT * FROM nurse_schedule
        WHERE
            ScheduleDate = "{0}" AND
            Doctor = "{1}"
    '''.format(schedule_date, doctor)
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return nurse_name

    row = rows[0]

    nurse_list = {
        '早班': string_utils.xstr(row['Nurse1']),
        '午班': string_utils.xstr(row['Nurse2']),
        '晚班': string_utils.xstr(row['Nurse3']),
    }

    return nurse_list[period]


def get_nurse_doctor(database, schedule_date, period, nurse):
    nurse_fields = ['Nurse1', 'Nurse2', 'Nurse3']
    doctor_fields = ['', '', '']

    for i in range(len(nurse_fields)):
        sql = '''
            SELECT * FROM nurse_schedule
            WHERE
                ScheduleDate = "{0}" AND
                {1} = "{2}"
        '''.format(schedule_date, nurse_fields[i], nurse)
        rows = database.select_record(sql)
        if len(rows) > 0:
            doctor_fields[i] = rows[0]['Doctor']

    doctor_list = {
        '早班': string_utils.xstr(doctor_fields[0]),
        '午班': string_utils.xstr(doctor_fields[1]),
        '晚班': string_utils.xstr(doctor_fields[2]),
    }

    return doctor_list[period]


def get_permission(database, program_name, permission_item, user_name):
    sql = '''
        SELECT * FROM person
        WHERE
            Name = "{name}"
    '''.format(
        name=user_name,
    )
    rows = database.select_record(sql)

    if len(rows) <= 0:
        return None

    person_key = rows[0]['PersonKey']
    sql = '''
        SELECT * FROM permission
        WHERE
            PersonKey = {person_key} AND
            ProgramName = "{program_name}" AND
            PermissionItem = "{permission_item}"
    '''.format(
        person_key=person_key,
        program_name=program_name,
        permission_item=permission_item,
    )
    rows = database.select_record(sql)
    if len(rows) <= 0:
        return None

    return string_utils.xstr(rows[0]['Permission'])



