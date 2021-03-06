import datetime
import calendar


# 取得年齡
def get_age(birth_date, current_date=datetime.datetime.now()):
    if birth_date is None or current_date is None:
        return None, None

    year = current_date.year - birth_date.year - \
           ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
    month = current_date.month - birth_date.month if current_date.month >= birth_date.month \
            else 12 - (birth_date.month - current_date.month)

    return year, month


# 取得日期分隔符號
def get_date_separator(in_date):
    separator = ''

    if in_date.find('-') > 0:
        separator = '-'
    elif in_date.find('/') > 0:
        separator = '/'
    elif in_date.find('.') > 0:
        separator = '.'

    return separator


# 轉換為西元年
def date_to_west_date(in_date):
    separator = get_date_separator(in_date)
    new_date = in_date.split(separator)

    try:
        year = int(new_date[0])
    except ValueError:
        return in_date

    if year < 1900:  # 非西元曆
        year += 1911

    try:
        west_date = '{0}-{1:0>2}-{2:0>2}'.format(str(year), new_date[1], new_date[2])
    except IndexError:
        return in_date

    return west_date


# 健保民國年轉為西元年
def nhi_date_to_west_date(nhi_date):
    if nhi_date is None or nhi_date == '':
        return nhi_date

    year, month, day = int(nhi_date[:3]), int(nhi_date[3:5]), int(nhi_date[5:7])
    year += 1911

    try:
        west_date = '{0}-{1:0>2}-{2:0>2}'.format(str(year), str(month), str(day))
    except IndexError:
        return nhi_date

    return west_date


# 健保民國日期時間轉為西元日期時間
def nhi_datetime_to_west_datetime(nhi_datetime):
    if nhi_datetime in [None, '']:
        return nhi_datetime

    year, month, day = int(nhi_datetime[:3]), int(nhi_datetime[3:5]), int(nhi_datetime[5:7])
    hour, minute, second = int(nhi_datetime[7:9]), int(nhi_datetime[9:11]), int(nhi_datetime[11:13])
    year += 1911

    try:
        west_datetime = '{0}-{1:0>2}-{2:0>2} {3:0>2}:{4:0>2}:{5:0>2}'.format(
            str(year), str(month), str(day), str(hour), str(minute), str(second))
    except IndexError:
        return nhi_datetime

    return west_datetime


# 西元日期時間轉健保日期時間
def west_datetime_to_nhi_datetime(in_datetime):
    if in_datetime in [None, '']:
        return in_datetime

    if type(in_datetime) is str:
        in_datetime = datetime.datetime.strptime(in_datetime, '%Y-%m-%d %H:%M:%S')

    year = in_datetime.year - 1911
    nhi_datetime = '{0:0>3}{1:0>2}{2:0>2}{3:0>2}{4:0>2}{5:0>2}'.format(
        str(year), str(in_datetime.month), str(in_datetime.day),
        str(in_datetime.hour), str(in_datetime.minute), str(in_datetime.second))

    return nhi_datetime


# 西元日期轉健保日期
def west_date_to_nhi_date(in_date, separator=''):
    if type(in_date) is str:
        in_date = datetime.datetime.strptime(in_date, '%Y-%m-%d')

    year = in_date.year - 1911
    nhi_date = '{year:0>3}{separator}{month:0>2}{separator}{day:0>2}'.format(
        year=str(year),
        month=str(in_date.month),
        day=str(in_date.day),
        separator=separator,
    )

    return nhi_date


def get_weekday_name(weekday):
    weekday_name = [
        '星期一',
        '星期二',
        '星期三',
        '星期四',
        '星期五',
        '星期六',
        '星期日',
    ]

    return weekday_name[weekday]


# 取得現在時間
def now_to_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def str_to_date(in_date):
    try:
        date = datetime.datetime.strptime(in_date, "%Y-%m-%d").date()
    except ValueError:
        date = datetime.datetime.strptime(in_date, "%Y-%m-%d %H:%M:%S").date()

    return date


# 取得現在日期
def date_to_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_start_date_by_year_month(year, month):
    start_date = '{0}-{1}-01 00:00:00'.format(
        year, month
    )

    return start_date


def get_end_date_by_year_month(year, month):
    last_day = calendar.monthrange(year, month)[1]
    end_date = '{0}-{1}-{2} 23:59:59'.format(
        year, month, last_day
    )

    return end_date


def get_two_month_date(database, patient_key, apply_year, apply_month):
    month = int(apply_month)
    if month > 1:
        year = apply_year
        month -= 1
    else:
        year = apply_year - 1
        month = 12

    start_date = get_start_date_by_year_month(year, month)  # 上月
    start_date2 = get_end_date_by_year_month(year, month)  # 上月最後一日

    sql = '''
            SELECT CaseKey FROM cases
            WHERE
                InsType = "健保" AND
                CaseDate BETWEEN "{0}" AND "{1}" AND
                PatientKey = {2}
        '''.format(
        start_date,
        start_date2,
        patient_key,
    )

    rows = database.select_record(sql)  # 檢查兩個月前是否有病歷
    if len(rows) <= 0:  # 如果沒病歷, 找出最後一次的病歷
        sql = '''
                SELECT CaseDate FROM cases
                WHERE
                    InsType = "健保" AND
                    CaseDate < "{0}" AND
                    PatientKey = {1}
                ORDER BY CaseDate DESC LIMIT 1
            '''.format(start_date, patient_key)
        rows = database.select_record(sql)
        if len(rows) > 0:
            start_date = get_start_date_by_year_month(
                rows[0]['CaseDate'].year, rows[0]['CaseDate'].month)  # 雙月檢查

    end_date = get_end_date_by_year_month(apply_year, apply_month)

    return start_date, end_date


def add_months(in_date, months):
    month = in_date.month - 1 + months
    year = in_date.year + month // 12
    month = month % 12 + 1
    day = min(in_date.day, calendar.monthrange(year, month)[1])

    return datetime.date(year, month, day)
