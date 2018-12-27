
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


