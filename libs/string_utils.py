# 字串 2018.01.29
#coding: utf-8

import re


phonetic_table = {
    'ㄅ': '1', 'ㄆ': 'q', 'ㄇ': 'a', 'ㄈ': 'z',
    'ㄉ': '2', 'ㄊ': 'w', 'ㄋ': 's', 'ㄌ': 'x',
    'ㄍ': 'e', 'ㄎ': 'd', 'ㄏ': 'c',
    'ㄐ': 'r', 'ㄑ': 'f', 'ㄒ': 'v',
    'ㄓ': '5', 'ㄔ': 't', 'ㄕ': 'g', 'ㄖ': 'b',
    'ㄗ': 'y', 'ㄘ': 'h', 'ㄙ': 'n',
    'ㄧ': 'u', 'ㄨ': 'j', 'ㄩ': 'm',
    'ㄚ': '8', 'ㄛ': 'i', 'ㄜ': 'k', 'ㄝ': ',',
    'ㄞ': '9', 'ㄟ': 'o', 'ㄠ': 'l', 'ㄡ': '.',
    'ㄢ': '0', 'ㄣ': 'p', 'ㄤ': ';', 'ㄥ': '/',
    'ㄦ': '-',
}


# 清除不必要的字元
def strip_string(in_string):
    try:
        in_string = re.sub(r'\([^)]*\)', '', in_string)  # 把 in_string(xxx) 中的 (xxx) 去除
    except TypeError:
        return

    remap = [chr(i) for i in range(32, 127)]  # 去除非中文字元
    for char in remap:
        in_string = in_string.replace(char, '')

    return in_string


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


def str_to_none(in_list):
    for i in range(len(in_list)):
        if str(in_list[i]) == '':
            in_list[i] = None


# 轉換注音字母為英數字母
def phonetic_to_str(in_str):
    ansi_str = ''
    for char in in_str:
        try:
            phn_str = phonetic_table[char]
        except KeyError:
            phn_str = char

        ansi_str += phn_str

    return ansi_str


def get_formatted_str(field_type, raw_value):
    value  = xstr(raw_value)

    if value == '':
        return value

    try:
        if field_type in ['日劑量', '總量']:
            value = '{0:.1f}'.format(raw_value)
        elif field_type == '次劑量':
            value = '{0:.2f}'.format(raw_value)
        elif field_type == '單價':
            value = '{0:.1f}'.format(raw_value)
        else:
            value = '{0:.1f}'.format(raw_value)
    except ValueError:
        pass

    return value
