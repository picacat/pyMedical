# 2018-03-27 掛號作業用

from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
from classes import db


def get_period(system_settings):
    current_time = datetime.datetime.now().strftime('%H:%M')
    try:
        if current_time >= system_settings.field('晚班時間'):
            period = '晚班'
        elif current_time >= system_settings.field('午班時間'):
            period = '午班'
        else:
            period = '早班'
    except TypeError:
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle('讀取班別資料失敗')
        msg_box.setText("無法取得系統班別時間, 無法產生班別資料.")
        msg_box.setInformativeText("請檢查[系統設定]->[院所設定]->[班別時間設定]的早午晚班別時間設定.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()
        return

    return period


def get_reg_no_by_mode(system_settings, reg_no):
    if system_settings.field('現場掛號給號模式') == '雙號':
        if reg_no % 2 == 1:
            reg_no += 1
        else:
            reg_no += 2
    elif system_settings.field('現場掛號給號模式') == '單號':
        if reg_no % 2 == 0:
            reg_no += 1
        else:
            reg_no += 2
    else:
        reg_no += 1

    return reg_no


# 取得診號
def get_reg_no(database, system_settings, room, period=None):
    start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
    end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')
    if period is None:
        period = get_period(system_settings)

    script = 'select RegistNo from cases where CaseDate between "{0}" and "{1}"'.format(
        start_date, end_date)

    if system_settings.field('分診') == 'Y':
        script += ' and Room = {0}'.format(room)

    if system_settings.field('分班') == 'Y':
        script += ' and Period = "{0}"'.format(period)

    script += ' order by RegistNo desc limit 1'
    row = database.select_record(script)
    row_count = len(list(row))

    if row_count > 0:
        last_reg_no = row[0]['RegistNo']
    else:
        if system_settings.field('分班') == 'Y':
            reg_no = system_settings.field('{0}起始號'.format(period))
        else:
            reg_no = system_settings.field('早班起始號'.format(period))

        try:
            last_reg_no = int(reg_no) - 1
        except TypeError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('讀取診號起始號資料失敗')
            msg_box.setText("無法取得班別起始號資料, 無法產生診號.")
            msg_box.setInformativeText("請檢查[系統設定]->[診號控制]->[給號方式]的早午晚班起始號設定.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

    reg_no = get_reg_no_by_mode(system_settings, last_reg_no)

    return int(reg_no)
