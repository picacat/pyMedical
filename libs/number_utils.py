# 數字 2014.10.05
#coding: utf-8


def get_integer(value):
    if value is None or value == '':
        return 0
    else:
        return int(float(value))


def get_integer_without_zero(value):
    if value is None or value == '':
        return None
    else:
        return int(float(value))


def get_float(value):
    if value is None or value == '':
        return 0.0
    else:
        return float(value)


# 傳統的四捨五入
def round_up(value):
    if value - int(value) > 0:
        value += 0.5

    return round(value)


def str_to_int(string):
    if string == '':
        return None
    else:
        return int(string)

