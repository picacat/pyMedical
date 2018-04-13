#coding: utf-8

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
