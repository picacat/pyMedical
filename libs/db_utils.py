

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
