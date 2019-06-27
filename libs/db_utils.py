

# 增加點擊率
def increment_hit_rate(database, table_name, primary_key_field, primary_key):
    if primary_key in [None, '']:
        return

    sql = '''
        UPDATE {table_name}
        SET
            HitRate = HitRate + 1
        WHERE
            {primary_key_field} = {primary_key}
    '''.format(
        table_name=table_name,
        primary_key_field=primary_key_field,
        primary_key=primary_key
    )

    database.exec_sql(sql)


def str_converter(field_value):
    import datetime

    if isinstance(field_value, datetime.datetime):
        field_value = field_value.__str__()
    elif isinstance(field_value, bytes):
        field_value = field_value.decode('utf8')
    else:
        field_value = field_value.__str__()

    return field_value


def mysql_to_json(rows):
    import json

    json_rows = []
    for row in rows:
        json_rows.append(json.dumps(row, default=str_converter))

    return json_rows
