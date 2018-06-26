import datetime


# 取得年齡
def get_age(birth_date, current_date=datetime.datetime.now()):
    if birth_date is None:
        return None, None

    year = current_date.year - birth_date.year - \
           ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
    month = current_date.month - birth_date.month if current_date.month >= birth_date.month \
            else 12 - (birth_date.month - current_date.month)

    return year, month


# 取得日期分隔符號
def _get_date_separator(in_date):
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
    separator = _get_date_separator(in_date)
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


# 健保民國年轉為西元年
def nhi_datetime_to_west_datetime(nhi_datetime):
    if nhi_datetime is None or nhi_datetime == '':
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
