# 字串 2018.01.29
#coding: utf-8


# 整數轉字串(零不顯示)
def int_to_str(number):
    if number is None:
        number = ''
    else:
        number = str(number)

    return number


# 更改欄位內容編碼 2015/01/22
def get_str(in_string, encoding):
    if not in_string:
        return ''

    try:
        out_string = str(in_string, encoding)
    except (UnicodeDecodeError, TypeError) as e:
        try:
            out_string = str(in_string, 'big5')
        except (UnicodeDecodeError, TypeError) as e:
            out_string = in_string

    return out_string


def xstr(string):
    if string is None:
        return ''

    return str(string)


def remove_bom(string):
    if string.startswith('\ufeff'):
        string = string[1:]

    return string
