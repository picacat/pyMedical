import mysql.connector as mysql
from PyQt5 import QtWidgets
from libs import ui_utils
from libs import system_utils
from libs import string_utils


VENDOR_LIST = {
    '友杏': ['Medical', 'Med2000'],
    '國泰': ['kthis'],
}


# 輸入分院資料
class DialogInputHost(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogInputHost, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.hosts_key = args[2]
        self.ui = None

        self._set_ui()
        self._set_signal()
        if self.hosts_key is not None:
            self._edit_host()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_INPUT_HOST, self)
        self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('存檔')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self._set_combo_box()
        self.ui.lineEdit_clinic_name.setFocus()

    def _set_combo_box(self):
        ui_utils.set_combo_box(self.ui.comboBox_charset, ['utf8', 'big5'])
        ui_utils.set_combo_box(self.ui.comboBox_vendor, list(VENDOR_LIST.keys()), None)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.lineEdit_host_name.textChanged.connect(self._set_database_name)
        self.ui.lineEdit_user_name.textChanged.connect(self._set_database_name)
        self.ui.lineEdit_password.textChanged.connect(self._set_database_name)
        self.ui.comboBox_vendor.currentTextChanged.connect(self._set_HIS_version)

    def _set_database_name(self):
        host_name = self.ui.lineEdit_host_name.text()
        user_name = self.ui.lineEdit_user_name.text()
        password = self.ui.lineEdit_password.text()
        charset = self.ui.comboBox_charset.currentText()

        if host_name == '' or user_name == '' or password == '' or charset in ['', None]:
            self.ui.comboBox_database_name.clear()
            return

        try:
            cnx = mysql.connect(
                user=user_name,
                host=host_name,
                password=password,
                charset=charset,
                buffered=True,
            )
        except mysql.errors.ProgrammingError:
            return

        cursor = cnx.cursor(dictionary=True)
        cursor.execute('SHOW DATABASES')
        rows = cursor.fetchall()
        database_list = []
        for row in rows:
            database_list.append(row['Database'])

        ui_utils.set_combo_box(self.ui.comboBox_database_name, database_list, None)

    def _set_HIS_version(self):
        self.ui.comboBox_HIS_version.clear()
        ui_utils.set_combo_box(
            self.ui.comboBox_HIS_version,
            VENDOR_LIST[self.ui.comboBox_vendor.currentText()],
            None
        )

    def _edit_host(self):
        sql = 'SELECT * FROM hosts where HostsKey = {0}'.format(self.hosts_key)
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return

        row = rows[0]
        self.ui.lineEdit_clinic_name.setText(row['ClinicName'])
        self.ui.lineEdit_host_name.setText(row['Host'])
        self.ui.lineEdit_user_name.setText(row['UserName'])
        self.ui.lineEdit_password.setText(row['Password'])
        self.ui.comboBox_database_name.setCurrentText(string_utils.xstr(row['DatabaseName']))
        self.ui.comboBox_vendor.setCurrentText(string_utils.xstr(row['Vendor']))
        self.ui.comboBox_HIS_version.setCurrentText(string_utils.xstr(row['HISVersion']))

    def accepted_button_clicked(self):
        if self.hosts_key is None:
            self._insert_host()
        else:
            self._update_host()

    def _insert_host(self):
        fields = [
            'ClinicName', 'Host', 'DatabaseName', 'UserName', 'Password', 'Charset', 'Vendor', 'HISVersion',
        ]
        data = [
            self.ui.lineEdit_clinic_name.text(),
            self.ui.lineEdit_host_name.text(),
            self.ui.comboBox_database_name.currentText(),
            self.ui.lineEdit_user_name.text(),
            self.ui.lineEdit_password.text(),
            self.ui.comboBox_charset.currentText(),
            self.ui.comboBox_vendor.currentText(),
            self.ui.comboBox_HIS_version.currentText(),
        ]
        
        self.database.insert_record('hosts', fields, data)

    def _update_host(self):
        fields = [
            'ClinicName', 'Host', 'DatabaseName', 'UserName', 'Password', 'Charset', 'Vendor', 'HISVersion',
        ]
        data = [
            self.ui.lineEdit_clinic_name.text(),
            self.ui.lineEdit_host_name.text(),
            self.ui.comboBox_database_name.currentText(),
            self.ui.lineEdit_user_name.text(),
            self.ui.lineEdit_password.text(),
            self.ui.comboBox_charset.currentText(),
            self.ui.comboBox_vendor.currentText(),
            self.ui.comboBox_HIS_version.currentText(),
        ]

        self.database.update_record(
            'hosts', fields, 'HostsKey', self.hosts_key, data
        )
