#!/usr/bin/env python3
#coding: utf-8

import configparser

from libs import ui_settings


# 系統設定
class SystemSettings:
    # 初始化
    def __init__(self, database, station_no=None):
        self.database = database
        self.config_file = ui_settings.CONFIG_FILE
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

        if station_no is None:
            self.station_no = self.config['settings']['station_no']
        else:
            self.station_no = station_no

    # 解構
    def __del__(self):
        pass

    # 讀取設定檔
    def field(self, field_name):
        station_no = self.get_station_no(field_name)
        if field_name == '工作站編號':
            return station_no

        script = 'select * from system_settings where StationNo = {0} and Field = "{1}"'.format(station_no, field_name)

        try:
            setting_rec = self.database.select_record(script)[0]
            return setting_rec['Value']
        except IndexError:
            return None

    # 寫入設定檔
    def post(self, field_name, value):
        if field_name == '工作站編號':
            self.config.set('settings', 'station_no', value)
            self.config.write(open(self.config_file, 'w'))
            return

        station_no = self.get_station_no(field_name)

        script = 'select * from system_settings where StationNo = {0} and Field = "{1}" limit 1'.format(station_no, field_name)

        try:
            setting_rec = self.database.select_record(script)[0]
            if value == setting_rec['Value']:
                return

            self.database.update_record('system_settings', ['Value'], 'SystemSettingsKey', setting_rec['SystemSettingsKey'], [value])
        except IndexError:
            fields = ['StationNo', 'Field', 'Value']
            data = (station_no, field_name, value)
            self.database.insert_record('system_settings', fields, data)

    # 取得工作站編號
    def get_station_no(self, field_name):
        if field_name in ['院所名稱', '院所代號', '統一編號', '健保業務', '負責醫師', '醫師證號', '開業證號',
                          '院所電話', '院所地址', '電子郵件', '早班時間', '午班時間', '晚班時間',
                          '護士人數', '藥師人數', '申報藥事服務費', '申報初診照護', '針灸認證合格', '針灸認證合格日期',
                          '分班', '分診', '早班起始號', '午班起始號', '晚班起始號', '現場掛號給號模式', '預設門診類別',
                          '首次警告次數', '針傷警告次數', '外觀主題',
                          ]:
            station_no = 0
        else:
            station_no = self.station_no

        return station_no

