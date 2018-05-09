#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import ui_settings
from libs import strings
from classes import table_widget
from dialog import dialog_input_share


# 收費設定 2018.04.14
class ChargeSettingsShare(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(ChargeSettingsShare, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_charge()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_CHARGE_SETTINGS_SHARE, self)
        self.table_widget_diag_share = table_widget.TableWidget(self.ui.tableWidget_diag_share, self.database)
        self.table_widget_diag_share.set_column_hidden([0, 1])
        self.table_widget_drug_share = table_widget.TableWidget(self.ui.tableWidget_drug_share, self.database)
        self.table_widget_drug_share.set_column_hidden([0, 1])
        self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.toolButton_diag_share_add.clicked.connect(self._diag_share_add)
        self.ui.toolButton_diag_share_delete.clicked.connect(self._diag_share_delete)
        self.ui.toolButton_diag_share_edit.clicked.connect(self._diag_share_edit)
        self.ui.tableWidget_diag_share.doubleClicked.connect(self._diag_share_edit)
        self.ui.toolButton_drug_share_add.clicked.connect(self._drug_share_add)
        self.ui.toolButton_drug_share_delete.clicked.connect(self._drug_share_delete)
        self.ui.toolButton_drug_share_edit.clicked.connect(self._drug_share_edit)
        self.ui.tableWidget_drug_share.doubleClicked.connect(self._drug_share_edit)

    # 設定欄位寬度
    def _set_table_width(self):
        diag_share_width = [60, 60, 180, 120, 100, 60, 80, 80, 150]
        self.table_widget_diag_share.set_table_heading_width(diag_share_width)
        drug_share_width = [60, 60, 220, 150, 100, 100, 200]
        self.table_widget_drug_share.set_table_heading_width(drug_share_width)

    # 主程式控制關閉此分頁
    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    # 關閉分頁
    def close_charge_settings(self):
        self.close_all()
        self.close_tab()

    def _read_charge(self):
        self._read_diag_share()
        self._read_drug_share()

    # 門診負擔 **********************************************************************************************************
    def _read_diag_share(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" ORDER BY ChargeSettingsKey'
        self.table_widget_diag_share.set_db_data(sql, self._set_diag_share_data)
        row_count = self.table_widget_diag_share.row_count()
        if row_count <= 0:
            self._set_diag_share_basic_data()

    def _set_diag_share_basic_data(self):
        fields = ['ChargeType', 'ItemName', 'ShareType', 'TreatType', 'Course', 'InsCode', 'Amount', 'Remark']
        data = [
            ('門診負擔', '一般內科', '基層醫療', '內科', '首次', 'S10', 50, None),
            ('門診負擔', '一般傷科首次', '基層醫療', '傷科治療', '首次', 'S10', 50, None),
            ('門診負擔', '一般傷科療程', '基層醫療', '傷科治療', '療程', 'S10', 50, None),
            ('門診負擔', '一般針灸首次', '基層醫療', '針灸治療', '首次', 'S10', 50, None),
            ('門診負擔', '一般針灸療程', '基層醫療', '針灸治療', '療程', '009', 0, None),

            ('門診負擔', '重大傷病內科', '重大傷病', '內科', '首次', '001', 0, None),
            ('門診負擔', '重大傷病傷科首次', '重大傷病', '傷科治療', '首次', '001', 0, None),
            ('門診負擔', '重大傷病傷科療程', '重大傷病', '傷科治療', '療程', '001', 0, None),
            ('門診負擔', '重大傷病針灸首次', '重大傷病', '針灸治療', '首次', '001', 0, None),
            ('門診負擔', '重大傷病針灸療程', '重大傷病', '針灸治療', '療程', '001', 0, None),

            ('門診負擔', '低收入戶內科', '低收入戶', '內科', '首次', '003', 0, None),
            ('門診負擔', '低收入戶傷科首次', '低收入戶', '傷科治療', '首次', '003', 0, None),
            ('門診負擔', '低收入戶傷科療程', '低收入戶', '傷科治療', '療程', '003', 0, None),
            ('門診負擔', '低收入戶針灸首次', '低收入戶', '針灸治療', '首次', '003', 0, None),
            ('門診負擔', '低收入戶針灸療程', '低收入戶', '針灸治療', '療程', '003', 0, None),

            ('門診負擔', '榮民內科', '榮民', '內科', '首次', '004', 0, None),
            ('門診負擔', '榮民傷科首次', '榮民', '傷科治療', '首次', '004', 0, None),
            ('門診負擔', '榮民傷科療程', '榮民', '傷科治療', '療程', '004', 0, None),
            ('門診負擔', '榮民針灸首次', '榮民', '針灸治療', '首次', '004', 0, None),
            ('門診負擔', '榮民針灸療程', '榮民', '針灸治療', '療程', '004', 0, None),

            ('門診負擔', '職業傷害內科', '職業傷害', '內科', '首次', '006', 0, None),
            ('門診負擔', '職業傷害傷科首次', '職業傷害', '傷科治療', '首次', '006', 0, None),
            ('門診負擔', '職業傷害傷科療程', '職業傷害', '傷科治療', '療程', '006', 0, None),
            ('門診負擔', '職業傷害針灸首次', '職業傷害', '針灸治療', '首次', '006', 0, None),
            ('門診負擔', '職業傷害針灸療程', '職業傷害', '針灸治療', '療程', '006', 0, None),

            ('門診負擔', '山地離島內科', '山地離島', '內科', '首次', '007', 0, None),
            ('門診負擔', '山地離島傷科首次', '山地離島', '傷科治療', '首次', '007', 0, None),
            ('門診負擔', '山地離島傷科療程', '山地離島', '傷科治療', '療程', '007', 0, None),
            ('門診負擔', '山地離島針灸首次', '山地離島', '針灸治療', '首次', '007', 0, None),
            ('門診負擔', '山地離島針灸療程', '山地離島', '針灸治療', '療程', '007', 0, None),

            ('門診負擔', '三歲兒童內科', '三歲兒童', '內科', '首次', '902', 0, None),
            ('門診負擔', '三歲兒童傷科首次', '三歲兒童', '傷科治療', '首次', '902', 0, None),
            ('門診負擔', '三歲兒童傷科療程', '三歲兒童', '傷科治療', '療程', '902', 0, None),
            ('門診負擔', '三歲兒童針灸首次', '三歲兒童', '針灸治療', '首次', '902', 0, None),
            ('門診負擔', '三歲兒童針灸療程', '三歲兒童', '針灸治療', '療程', '902', 0, None),

            ('門診負擔', '新生兒內科', '新生兒', '內科', '首次', '903', 0, None),
            ('門診負擔', '新生兒傷科首次', '新生兒', '傷科治療', '首次', '903', 0, None),
            ('門診負擔', '新生兒傷科療程', '新生兒', '傷科治療', '療程', '903', 0, None),
            ('門診負擔', '新生兒針灸首次', '新生兒', '針灸治療', '首次', '903', 0, None),
            ('門診負擔', '新生兒針灸療程', '新生兒', '針灸治療', '療程', '903', 0, None),

            ('門診負擔', '愛滋病內科', '愛滋病', '內科', '首次', '904', 0, None),
            ('門診負擔', '愛滋病傷科首次', '愛滋病', '傷科治療', '首次', '904', 0, None),
            ('門診負擔', '愛滋病傷科療程', '愛滋病', '傷科治療', '療程', '904', 0, None),
            ('門診負擔', '愛滋病針灸首次', '愛滋病', '針灸治療', '首次', '904', 0, None),
            ('門診負擔', '愛滋病針灸療程', '愛滋病', '針灸治療', '療程', '904', 0, None),

            ('門診負擔', '替代役男內科', '替代役男', '內科', '首次', '906', 0, None),
            ('門診負擔', '替代役男傷科首次', '替代役男', '傷科治療', '首次', '906', 0, None),
            ('門診負擔', '替代役男傷科療程', '替代役男', '傷科治療', '療程', '906', 0, None),
            ('門診負擔', '替代役男針灸首次', '替代役男', '針灸治療', '首次', '906', 0, None),
            ('門診負擔', '替代役男針灸療程', '替代役男', '針灸治療', '療程', '906', 0, None),
        ]
        for rec in data:
            self.database.insert_record('charge_settings', fields, rec)

        self._read_diag_share()

    def _set_diag_share_data(self, rec_no, rec):
        diag_share_rec = [
            str(rec['ChargeSettingsKey']),
            strings.xstr(rec['ChargeType']),
            strings.xstr(rec['ItemName']),
            strings.xstr(rec['ShareType']),
            strings.xstr(rec['TreatType']),
            strings.xstr(rec['Course']),
            strings.xstr(rec['InsCode']),
            strings.xstr(rec['Amount']),
            strings.xstr(rec['Remark']),
        ]

        for column in range(0, self.ui.tableWidget_diag_share.columnCount()):
            self.ui.tableWidget_diag_share.setItem(rec_no, column, QtWidgets.QTableWidgetItem(diag_share_rec[column]))
            if column in [7]:
                self.ui.tableWidget_diag_share.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _diag_share_add(self):
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, None, '門診負擔')
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_diag_share.rowCount()
            self.ui.tableWidget_diag_share.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'ShareType', 'InsCode', 'Amount', 'Remark']
            data = (
                '門診負擔',
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.comboBox_share_type.currentText(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            )
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType = "門診負擔" ORDER BY ChargeSettingsKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            self._set_diag_share_data(current_row, row_data)
            self.ui.tableWidget_diag_share.setCurrentCell(current_row, 3)

        dialog.close_all()

    def _diag_share_edit(self):
        key = self.table_widget_diag_share.field_value(0)
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, key, '門診負擔')
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_diag_share_data(self.ui.tableWidget_diag_share.currentRow(), row_data)

    def _diag_share_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除門診負擔資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆門診負擔資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_diag_share.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_diag_share.removeRow(self.ui.tableWidget_diag_share.currentRow())

    # 藥品負擔 **********************************************************************************************************
    def _read_drug_share(self):
        sql = 'SELECT * FROM charge_settings WHERE ChargeType = "藥品負擔" ORDER BY ChargeSettingsKey'
        self.table_widget_drug_share.set_db_data(sql, self._set_drug_share_data)
        row_count = self.table_widget_drug_share.row_count()
        if row_count <= 0:
            self._set_drug_share_basic_data()

    def _set_drug_share_basic_data(self):
        fields = ['ChargeType', 'ItemName', 'ShareType', 'InsCode', 'Amount', 'Remark']
        data = [
            ('藥品負擔', '藥費100點以下', '基層醫療', 'S10', 0, '<=100'),
            ('藥品負擔', '藥費101-200', '基層醫療', 'S20', 20, '<=200'),
            ('藥品負擔', '藥費201-300', '基層醫療', 'S20', 40, '<=300'),
            ('藥品負擔', '藥費301-400', '基層醫療', 'S20', 60, '<=400'),
            ('藥品負擔', '藥費401-500', '基層醫療', 'S20', 80, '<=500'),
            ('藥品負擔', '藥費501-600', '基層醫療', 'S20', 100, '<=600'),
            ('藥品負擔', '藥費601-700', '基層醫療', 'S20', 120, '<=700'),
            ('藥品負擔', '藥費701-800', '基層醫療', 'S20', 140, '<=800'),
            ('藥品負擔', '藥費801-900', '基層醫療', 'S20', 160, '<=900'),
            ('藥品負擔', '藥費901-1000', '基層醫療', 'S20', 180, '<=1000'),
            ('藥品負擔', '藥費1000以上', '基層醫療', 'S20', 200, '>1000'),
            ('藥品負擔', '重大傷病', '重大傷病', '001', 0, None),
            ('藥品負擔', '低收入戶', '低收入戶', '003', 0, None),
            ('藥品負擔', '榮民', '榮民', '004', 0, None),
            ('藥品負擔', '職業傷害', '職業傷害', '006', 0, None),
            ('藥品負擔', '山地離島', '山地離島', '007', 0, None),
            ('藥品負擔', '其他免部份負擔', '其他免部份負擔', '009', 0, '針灸療程2-6次, 百歲人瑞, 921震災'),
            ('藥品負擔', '三歲以下兒童', '三歲兒童', '902', 0, None),
            ('藥品負擔', '新生兒依附', '新生兒', '903', 0, None),
            ('藥品負擔', '愛滋病', '愛滋病', '904', 0, None),
            ('藥品負擔', '替代役男', '替代役男', '906', 0, None),
        ]
        for rec in data:
            self.database.insert_record('charge_settings', fields, rec)

        self._read_drug_share()

    def _set_drug_share_data(self, rec_no, rec):
        drug_share_rec = [
            str(rec['ChargeSettingsKey']),
            strings.xstr(rec['ChargeType']),
            strings.xstr(rec['ItemName']),
            strings.xstr(rec['ShareType']),
            strings.xstr(rec['InsCode']),
            strings.xstr(rec['Amount']),
            strings.xstr(rec['Remark']),
        ]

        for column in range(0, self.ui.tableWidget_drug_share.columnCount()):
            self.ui.tableWidget_drug_share.setItem(rec_no, column, QtWidgets.QTableWidgetItem(drug_share_rec[column]))
            if column in [5]:
                self.ui.tableWidget_drug_share.item(rec_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def _drug_share_add(self):
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, None, '藥品負擔')
        result = dialog.exec_()
        if result != 0:
            current_row = self.ui.tableWidget_drug_share.rowCount()
            self.ui.tableWidget_drug_share.insertRow(current_row)
            fields = ['ChargeType', 'ItemName', 'ShareType', 'InsCode', 'Amount', 'Remark']
            data = (
                '藥品負擔',
                dialog.ui.lineEdit_item_name.text(),
                dialog.ui.comboBox_share_type.currentText(),
                dialog.ui.lineEdit_ins_code.text(),
                dialog.ui.spinBox_amount.value(),
                dialog.ui.lineEdit_remark.text()
            )
            self.database.insert_record('charge_settings', fields, data)
            sql = 'SELECT * FROM charge_settings WHERE ChargeType = "藥品負擔" ORDER BY ChargeSettingsKey desc limit 1'
            row_data = self.database.select_record(sql)[0]
            self._set_drug_share_data(current_row, row_data)
            self.ui.tableWidget_drug_share.setCurrentCell(current_row, 3)

        dialog.close_all()

    def _drug_share_delete(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除藥品負擔資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除此筆藥品負擔資料?</b></font>")
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        key = self.table_widget_drug_share.field_value(0)
        self.database.delete_record('charge_settings', 'ChargeSettingsKey', key)
        self.ui.tableWidget_drug_share.removeRow(self.ui.tableWidget_drug_share.currentRow())

    def _drug_share_edit(self):
        key = self.table_widget_drug_share.field_value(0)
        dialog = dialog_input_share.DialogInputShare(self, self.database, self.system_settings, key, '藥品負擔')
        dialog.exec_()
        dialog.close_all()
        sql = 'SELECT * FROM charge_settings WHERE ChargeSettingsKey = {0}'.format(key)
        row_data = self.database.select_record(sql)[0]
        self._set_drug_share_data(self.ui.tableWidget_drug_share.currentRow(), row_data)


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = ChargeSettingsShare()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()