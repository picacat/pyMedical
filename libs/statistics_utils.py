
import datetime

from libs import nhi_utils


def get_count_by_treat_type(database, table_name, calc_type, treat_type):
    if calc_type == '當月':
        start_date = datetime.datetime.now().strftime('%Y-%m-01 00:00:00')
        end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
    else:
        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

    if table_name == 'cases':
        sql = '''
            SELECT COUNT(CaseKey) AS Count FROM {table_name}
            WHERE
                InsType = "健保" AND
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                TreatType IN {treat_type}
        '''.format(
            table_name=table_name,
            start_date=start_date,
            end_date=end_date,
            treat_type=tuple(treat_type),
        )
    else:
        sql = '''
            SELECT COUNT(cases.CaseKey) AS Count FROM {0}
                LEFT JOIN cases ON cases.CaseKey = wait.CaseKey
            WHERE
                cases.InsType = "健保" AND
                cases.CaseDate BETWEEN "{1}" AND "{2}" AND
                cases.TreatType IN {3}
        '''.format(table_name, start_date, end_date, tuple(treat_type))

    rows = database.select_record(sql)

    return rows[0]['Count']


def get_first_course(database, table_name, calc_type):
    if calc_type == '當月':
        start_date = datetime.datetime.now().strftime('%Y-%m-01 00:00:00')
        end_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d 23:59:59")
    else:
        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

    sql = '''
            SELECT Count(CaseKey) as Count FROM {0} 
            WHERE
                InsType = "健保" AND
                CaseDate BETWEEN "{1}" AND "{2}" AND
                (Continuance IS NULL OR Continuance <= 1)
        '''.format(table_name, start_date, end_date)
    rows = database.select_record(sql)

    return rows[0]['Count']


def get_diag_days(database):
    start_date = datetime.datetime.now().strftime('%Y-%m-01 00:00:00')
    end_date = datetime.datetime.now().strftime("%Y-%m-%d 23:59:59")

    sql = '''
            SELECT CaseDate FROM cases 
            WHERE
                InsType = "健保" AND
                CaseDate BETWEEN "{0}" AND "{1}" 
                GROUP BY DayOfMonth(CaseDate)
        '''.format(start_date, end_date)
    rows = database.select_record(sql)

    return len(rows)


def get_max_treat(database):
    return get_diag_days(database) * nhi_utils.TREAT_SECTION2

