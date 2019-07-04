import mysql.connector as mysql

from PyQt5.QtWidgets import QMessageBox, QPushButton
import configparser
import os
from libs import ui_utils
from libs import string_utils
from libs import charge_utils


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname("__file__")))
DB_PATH = "mysql"


# 資料庫元件 2018.03.28 重新撰寫 procedure -> class
class Database:
    # 初始化
    def __init__(self, **kwargs):
        self.cnx = None

        if kwargs == {}:
            self._connect_to_db()
        else:
            self._connect_to_db(**kwargs)

    # 結束
    def __del__(self):
        self.close_database()

    # 檢查資料庫是否連線
    def connected(self):
        return self.cnx

    # 關閉資料庫
    def close_database(self):
        if self.cnx:
            self.cnx.close()

    # 取得資料庫名稱
    def _get_database_name(self):
        sql = 'SELECT DATABASE()'
        row = self.select_record(sql)[0]

        return row['DATABASE()']

    # 連接MySQL
    def _connect_to_db(self, **kwargs):
        try:
            if kwargs == {}:
                config = configparser.ConfigParser()
                config.read(ui_utils.CONFIG_FILE)
                self.cnx = mysql.connect(
                    user=config['db']['user'],
                    host=config['db']['host'],
                    password=config['db']['password'],
                    charset=config['db']['charset'],
                    buffered=True,
                )
                cursor = self.cnx.cursor(dictionary=True)
                cursor.execute('CREATE DATABASE IF NOT EXISTS {0}'.format(config['db']['database']))
                cursor.execute('USE {0}'.format(config['db']['database']))
                cursor.close()
            else:
                self.cnx = mysql.connect(
                    host=kwargs['host'],
                    user=kwargs['user'],
                    password=kwargs['password'],
                    database=kwargs['database'],
                    charset=kwargs['charset'],
                    buffered=True,
                )
        except mysql.errors.ProgrammingError:
            if kwargs == {}:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle('連線失敗')
                msg_box.setText("<font size='4' color='red'><b>無法連線至資料庫主機, 請檢查網路設定.</b></font>")
                msg_box.setInformativeText("請檢查 pymedical.conf 內的設定, 確定資料庫連線設定是否正確.")
                msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
                msg_box.exec_()
            else:
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Critical)
                msg_box.setWindowTitle('連線失敗')
                msg_box.setText("<font size='4' color='red'><b>無法連線至資料庫主機, 請檢查傳遞的參數.</b></font>")
                msg_box.setInformativeText("請檢查傳遞的參數是否正確.")
                msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
                msg_box.exec_()

    # 取得 mysql insert values
    @staticmethod
    def _get_value_list(fields):
        value_format = len(fields) * '%s,'

        return value_format[:-1]

    # 取得 mysql field format
    @staticmethod
    def _get_assignment_list(fields):
        assignment_list = ''
        for field in fields:
            assignment_list += '{0} = %s,'.format(field)

        return assignment_list[:-1]

    # 讀取記錄
    def select_record(self, sql, dictionary=True):
        try:
            cursor = self.cnx.cursor(dictionary=dictionary)
        except:
            self.cnx.close()
            self._connect_to_db()
            cursor = self.cnx.cursor(dictionary=dictionary)

        cursor.execute(sql)
        rows = cursor.fetchall()
        cursor.close()

        return rows

    # 刪除記錄
    def delete_record(self, table_name, primary_key, key_value):
        cursor = self.cnx.cursor()
        sql = 'delete from {0} where {1} = {2}'.format(table_name, primary_key, key_value)
        cursor.execute(sql)
        self.cnx.commit()
        cursor.close()

    # 增加記錄
    def insert_record(self, table_name, fields, data):
        cursor = self.cnx.cursor()
        value_list = self._get_value_list(fields)
        sql = "INSERT INTO {0} ({1}) VALUES ({2})".format(table_name, ", ".join(fields), value_list)
        string_utils.str_to_none(data)
        cursor.execute(sql, data)
        self.cnx.commit()
        last_row_id = cursor.lastrowid
        cursor.close()

        return last_row_id

    # 更新記錄
    def update_record(self, table_name, fields, primary_key, key_value, data):
        cursor = self.cnx.cursor()
        assignment_list = self._get_assignment_list(fields)
        sql = "UPDATE {0} SET {1} WHERE {2} = {3}".format(table_name, assignment_list, primary_key, key_value)
        string_utils.str_to_none(data)
        cursor.execute(sql, data)
        self.cnx.commit()
        cursor.close()

    # 執行sql
    def exec_sql(self, sql):
        cursor = self.cnx.cursor()
        cursor.execute(sql)
        self.cnx.commit()
        cursor.close()

    # 檢查資料表是否存在
    def _is_table_exists(self, table_name):
        cursor = self.cnx.cursor()
        cursor.execute('show tables')
        rows = cursor.fetchall()
        if (table_name,) in rows:
            return True
        else:
            return False

    # 建立資料表格 from ./mysql/[table].sql
    def create_table(self, table_name):
        table_file = table_name + '.sql'
        try:
            with open(os.path.join(BASE_DIR, DB_PATH, table_file), 'r', encoding='utf-8') as db_table:
                sql = db_table.read()
        except FileNotFoundError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('資料庫檔案不存在')
            msg_box.setText("找不到資料庫表格定義檔，請檢查檔案是否存.")
            msg_box.setInformativeText("檔名: {0}/{1}/{2}".format(BASE_DIR, DB_PATH, table_file))
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return
        except UnicodeDecodeError:
            print('file encoding error')
            return

        sql = string_utils.remove_bom(sql)
        cursor = self.cnx.cursor(sql)
        try:
            cursor.execute(sql)
        except mysql.errors.ProgrammingError:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('資料表語法錯誤')
            msg_box.setText("資料庫表格定義檔{0}語法錯誤，請檢查定義檔內容是否有誤.".format(table_file))
            msg_box.setInformativeText("{0}".format(sql))
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()

        cursor.close()

    # 檢查資料庫狀態
    def check_table_exists(self, table_name):
        if self._is_table_exists(table_name):
            return

        self.create_table(table_name)
        if table_name == 'charge_settings':
            charge_utils.set_nhi_basic_data(self)
            charge_utils.set_diag_share_basic_data(self)
            charge_utils.set_drug_share_basic_data(self)
            charge_utils.set_discount_basic_data(self)
            charge_utils.set_regist_fee_basic_data(self)

    def get_last_auto_increment_key(self, table_name):
        sql = '''
        SELECT AUTO_INCREMENT
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND
        TABLE_NAME = "{0}"'''.format(table_name)
        row = self.select_record(sql)

        return row[0]['AUTO_INCREMENT']

    def check_field_exists(self, table_name, alter_type, column, data_type):
        if type(column) is list:
            search_column = column[0]
            new_column = column[1]
        else:
            search_column = column
            new_column = column

        sql = 'SHOW COLUMNS FROM {0} like "{1}"'.format(table_name, search_column)
        rows = self.select_record(sql)

        if alter_type == 'add' and len(rows) > 0:  # 新欄位已加入
            return
        elif alter_type == 'change' and len(rows) > 0:
            if (string_utils.xstr(rows[0]['Field']) == new_column and
                    string_utils.xstr(rows[0]['Type']).lower() == data_type.lower()):
                return

        if alter_type == 'add':
            sql = 'ALTER TABLE {0} ADD {1} {2}'.format(
                table_name, column, data_type
            )
        elif alter_type == 'change':
            sql = 'ALTER TABLE {0} CHANGE {1} {2} {3}'.format(
                table_name, column[0], column[1], data_type
            )

        self.exec_sql(sql)
