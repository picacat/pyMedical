# 日誌檔 2019.12.25
#coding: utf-8
import datetime
from libs import system_utils


def write_event_log(database, user_name, log_type, program_name, log):
    ip_address = system_utils.get_ip()

    fields = ['UserName', 'IP', 'LogType', 'ProgramName', 'Log']
    data = [user_name, ip_address, log_type, program_name, log]

    try:
        database.insert_record('event_log', fields, data)
    except:
        pass


def write_system_log(database, log_type, log_name, log):
    fields = ['LogType', 'LogName', 'Log']
    data = [log_type, log_name, log]

    database.insert_record('system_log', fields, data)



