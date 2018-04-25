from PyQt5 import QtCore, QtGui


# 取得日期驗證器
def get_date_validator():
    regexp = QtCore.QRegExp('^(0|1|19|20)?[0-9]{2}[-/.](0?[1-9]|1[012])[-/.](0?[1-9]|[12][0-9]|3[01])$')
    validator = QtGui.QRegExpValidator(regexp)

    return validator
