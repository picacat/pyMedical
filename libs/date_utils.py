import datetime


# 取得年齡
def get_age(birth_date, current_date = datetime.datetime.now()):
    if birth_date is None:
        return None, None

    year = current_date.year - birth_date.year \
           - ((current_date.month, current_date.day) < (birth_date.month, birth_date.day))
    month = current_date.month - birth_date.month if current_date.month >= birth_date.month \
            else 12 - (birth_date.month - current_date.month)

    return year, month


# 轉換為西元年
def date_to_west_date(in_date):
    separator = '-'
    if in_date.find('-') > 0:
        separator = '-'
    elif in_date.find('/') > 0:
        separator = '/'
    elif in_date.find('.') > 0:
        separator = '.'

    new_date = in_date.split(separator)
    year = int(new_date[0])
    if year < 1900:  # 非西元曆
        year += 1911

    west_date = '{0}-{1}-{2}'.format(str(year), new_date[1], new_date[2])

    return west_date
