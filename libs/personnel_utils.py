
from libs import string_utils


# 取得醫事人員名單
def get_personnel(database, personnel_type):
    if personnel_type == '全部':
        position = ''
    elif personnel_type == '醫師':
        position = 'WHERE (Position = "醫師" OR Position = "支援醫師")'
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

