from PyQt5 import QtCore, QtGui


DATE_REGEXP = '^(0|1|19|20)?[0-9]{2}[-/.](0?[1-9]|1[012])[-/.](0?[1-9]|[12][0-9]|3[01])$'
ID_REGEXP = '([A-Z])(1|2|A|B|C|D|Y|X)\d{8}'


# 設定資料驗證
def set_validator(validator_type):
    regexp_str = None
    if validator_type == '日期格式':
        regexp_str = DATE_REGEXP
    elif validator_type == '身分證格式':
        regexp_str = ID_REGEXP

    regexp = QtCore.QRegExp(regexp_str)
    validator = QtGui.QRegExpValidator(regexp)

    return validator


# 檢查身分證
def verify_id(in_id):
    area_code = {
        'A': '10', 'B': '11', 'C': '12', 'D': '13', 'E': '14', 'F': '15', 'G': '16', 'H': '17',
        'I': '34',
        'J': '18', 'K': '19', 'L': '20', 'M': '21', 'N': '22',
        'O': '35',
        'P': '23', 'Q': '24', 'R': '25', 'S': '26', 'T': '27', 'U': '28', 'V': '29',
        'W': '32',
        'X': '30', 'Y': '31',
        'Z': '33'
    }

    try:
        code1 = area_code[in_id[0]]
    except IndexError:
        return False

    code2 = in_id[1]
    if code2 in ['A', 'B', 'C', 'D', 'Y', 'X']:
        code2 = area_code[in_id[1]][-1]

    id_digits = code1 + code2 + in_id[2] + in_id[3] + in_id[4] + in_id[5] + in_id[6] + in_id[7] + in_id[8]
    id_check_code = '1987654321'

    converted_id = ''
    for i in range(0, 10):
        converted_id += str(int(id_digits[i]) * int(id_check_code[i]))[-1]

    final_code = 0
    for i in range(0, 10):
        final_code += int(converted_id[i])

    last_digit = str(final_code)[-1]
    if last_digit == '0':
        checksum = last_digit
    else:
        checksum = str(10 - int(last_digit))

    if in_id[9] != checksum:
        return False
    else:
        return True
