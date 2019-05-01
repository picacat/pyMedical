
#coding: utf-8


from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import os
import configparser
import datetime

from libs import ui_utils


# 系統設定 2018.03.19
class Backup(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Backup, self).__init__(parent)
        self.database = args[0]
        self.system_settings = args[1]
        self.parent = parent
        self.BACKUP_PATH = './auto_backup'

        self._set_ui()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def _set_ui(self):
        self.center()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def start_backup(self):
        backup_date = datetime.datetime.today().strftime('%Y-%m-%d')
        backup_path = os.path.join(self.BACKUP_PATH, backup_date)

        start_date = datetime.datetime.now().strftime('%Y-%m-%d 00:00:00')
        end_date = datetime.datetime.now().strftime('%Y-%m-%d 23:59:59')

        self._check_backup_path(backup_path)

        backup_list = [
            ['patient.sql', '"PatientKey IN (SELECT PatientKey FROM cases WHERE CaseDate BETWEEN \'{0}\' AND \'{1}\')"'.format(start_date, end_date)],
            ['cases.sql', '"CaseDate BETWEEN \'{0}\' AND \'{1}\'"'.format(start_date, end_date)],
            ['prescript.sql', '"CaseKey IN (SELECT CaseKey FROM cases WHERE CaseDate BETWEEN \'{0}\' AND \'{1}\')"'.format(start_date, end_date)],
            ['dosage.sql', '"CaseKey IN (SELECT CaseKey FROM cases WHERE CaseDate BETWEEN \'{0}\' AND \'{1}\')"'.format(start_date, end_date)],
            ['deposit.sql', '"CaseKey IN (SELECT CaseKey FROM cases WHERE CaseDate BETWEEN \'{0}\' AND \'{1}\')"'.format(start_date, end_date)],
            ['debt.sql', '"CaseKey IN (SELECT CaseKey FROM cases WHERE CaseDate BETWEEN \'{0}\' AND \'{1}\')"'.format(start_date, end_date)],
            ['reserve.sql', '"ReserveDate BETWEEN \'{0}\' AND \'{1}\'"'.format(start_date, end_date)],
        ]
        max_progress = len(backup_list)

        progress_dialog = QtWidgets.QProgressDialog(
            '正在自動備份資料中, 請稍後...', '取消', 0, max_progress, self
        )

        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for i, filename in zip(range(1, len(backup_list)+1), backup_list):
            self._dump_file(backup_path, filename[0], filename[1])
            progress_dialog.setValue(i)

        progress_dialog.setValue(max_progress)

        if datetime.datetime.today().day in [5, 10, 15, 20, 25, 30]:  # 每個月5, 10, 15, 20, 25, 30日備份所有資料
            self._dump_database(backup_path)

    def _check_backup_path(self, backup_path):
        try:
            os.stat(self.BACKUP_PATH)
        except:
            os.mkdir(self.BACKUP_PATH)

        try:
            os.stat(backup_path)
        except:
            os.mkdir(backup_path)

    def _dump_file(self, backup_path, in_filename, where_script=None):
        config = configparser.ConfigParser()
        config.read(ui_utils.CONFIG_FILE)

        host_name =config['db']['host']
        user_name =config['db']['user']
        password=config['db']['password']
        database_name =config['db']['database']

        filename = os.path.join(backup_path, in_filename)
        table_name = in_filename.split('.')[0]

        if where_script is not None:
            where = '--where={0}'.format(where_script)
        else:
            where = ''

        dump_cmd = '''
            mysqldump --host={host} --user={user} --password={password} --lock-all-tables --complete-insert --no-create-info {where} {database} {table_name} > {dump_file}
        '''.format(
            host=host_name, user=user_name, password=password, where=where,
            database=database_name, table_name=table_name, dump_file=filename,
        )
        os.system(dump_cmd)

    def _dump_database(self, backup_path):
        config = configparser.ConfigParser()
        config.read(ui_utils.CONFIG_FILE)

        host_name =config['db']['host']
        user_name =config['db']['user']
        password=config['db']['password']
        database_name =config['db']['database']
        dump_file = os.path.join(backup_path, '{0}.sql'.format(database_name))

        dump_cmd = '''
            mysqldump --host={host} --user={user} --password={password} --complete-insert {database} > {dump_file}
        '''.format(
            host=host_name, user=user_name, password=password,
            database=database_name, dump_file=dump_file,
        )

        err_no = os.system(dump_cmd)
        if err_no != 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('備份失敗')
            msg_box.setText("<font size='4' color='red'><b>無法備份全部的資料庫, 資料庫檔案需要檢查.</b></font>")
            msg_box.setInformativeText("請與本公司聯繫, 並告知上面的訊息.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()

