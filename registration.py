#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime

from libs import ui_settings
from libs import patient_utils
from libs import nhi
from libs import number
from libs import strings
from libs import registration_utils
from classes import table_widget
import print_registration


# 門診掛號 2018.01.22
class Registration(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(Registration, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.ui = None

        self._set_ui()
        self._set_signal()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_settings.load_ui_file(ui_settings.UI_REGISTRATION, self)
        ui_settings.set_completer(self.database,
                                  'SELECT Name FROM patient GROUP BY Name ORDER BY Name',
                                  'Name',
                                  self.ui.lineEdit_query)
        self.table_widget_wait = table_widget.TableWidget(self.ui.tableWidget_wait, self.database)
        self.table_widget_wait.set_column_hidden([0, 1])
        self.ui.lineEdit_query.setFocus()
        self._set_reg_mode(True)
        self._set_combobox()
        # self._set_table_width()

    # 設定信號
    def _set_signal(self):
        self.ui.action_cancel.triggered.connect(self.action_cancel_triggered)
        self.ui.action_save.triggered.connect(self.action_save_triggered)
        self.ui.action_close.triggered.connect(self.close_registration)
        self.ui.toolButton_query.clicked.connect(self.query_clicked)
        self.ui.toolButton_delete_wait.clicked.connect(self.delete_wait_clicked)
        self.ui.toolButton_print_wait.clicked.connect(self.print_wait_clicked)
        self.ui.lineEdit_query.returnPressed.connect(self.query_clicked)
        self.ui.comboBox_ins_type.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_card.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_period.currentIndexChanged.connect(self.selection_changed)
        self.ui.comboBox_room.currentIndexChanged.connect(self.selection_changed)

    def _set_table_width(self):
        width = [70, 70, 60, 80, 40, 50, 80, 80, 80, 60, 80, 40, 30, 50, 80]
        self.table_widget_wait.set_table_heading_width(width)

    def read_wait(self):
        sql = ('SELECT wait.*, patient.Gender FROM wait '
               'LEFT JOIN patient ON wait.PatientKey = patient.PatientKey '
               ' WHERE '
               'DoctorDone = "False" '
               'ORDER BY CaseDate, RegistNo')
        self.table_widget_wait.set_db_data(sql, self._set_table_data)
        row_count = self.table_widget_wait.row_count()

        if row_count > 0:
            self._set_tool_button(True)
        else:
            self._set_tool_button(False)

    def _set_table_data(self, rec_no, rec):
        wait_rec = [
            str(rec['WaitKey']),
            str(rec['CaseKey']),
            str(rec['PatientKey']),
            str(rec['Name']),
            str(rec['Gender']),
            str(rec['InsType']),
            str(rec['RegistType']),
            str(rec['Share']),
            str(rec['TreatType']),
            str(rec['Visit']),
            str(rec['Card']),
            strings.int_to_str(rec['Continuance']).strip('0'),
            str(rec['Room']),
            str(rec['RegistNo']),
            str(rec['Massager']),
        ]

        for column in range(0, self.ui.tableWidget_wait.columnCount()):
            self.ui.tableWidget_wait.setItem(rec_no, column, QtWidgets.QTableWidgetItem(wait_rec[column]))
            if column in [2, 12, 13]:
                self.ui.tableWidget_wait.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            elif column in [4, 9]:
                self.ui.tableWidget_wait.item(rec_no, column).setTextAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)

            if rec['InsType'] == '自費':
                self.ui.tableWidget_wait.item(rec_no, column).setForeground(QtGui.QColor('blue'))

    def _set_tool_button(self, enabled):
        self.ui.toolButton_modify_wait.setEnabled(enabled)
        self.ui.toolButton_delete_wait.setEnabled(enabled)
        self.ui.toolButton_ic_cancel.setEnabled(enabled)
        self.ui.toolButton_modify_patient.setEnabled(enabled)
        self.ui.toolButton_print_wait.setEnabled(enabled)

    # 設定掛號模式
    def _set_reg_mode(self, enabled):
        self.ui.action_ic_card.setEnabled(enabled)
        self.ui.action_new_patient.setEnabled(enabled)
        self.ui.action_reg_reserve.setEnabled(enabled)
        self.ui.action_cancel.setEnabled(not enabled)
        self.ui.action_save.setEnabled(not enabled)

        self.ui.groupBox_search_patient.setEnabled(enabled)
        self.ui.tabWidget_list.setEnabled(enabled)
        self.ui.groupBox_patient.setEnabled(not enabled)
        self.ui.groupBox_registration.setEnabled(not enabled)

        self._clear_group_box_patient()

    # 清除病患資料欄位
    def _clear_group_box_patient(self):
        self.ui.lineEdit_patient_key.clear()
        self.ui.lineEdit_name.clear()
        self.ui.lineEdit_id.clear()
        self.ui.lineEdit_share_type.clear()
        self.ui.lineEdit_discount_type.clear()
        self.ui.lineEdit_birthday.clear()
        self.ui.lineEdit_telephone.clear()
        self.ui.lineEdit_cellphone.clear()
        self.ui.lineEdit_address.clear()
        self.ui.lineEdit_patient_remark.clear()
        self.ui.lineEdit_regist_fee.clear()
        self.ui.lineEdit_reg_share_fee.clear()
        self.ui.lineEdit_deposit_fee.clear()
        self.ui.lineEdit_massage_fee.clear()
        self.ui.lineEdit_total_fee.clear()

    # 設定 comboBox
    def _set_combobox(self):
        ui_settings.set_combo_box(self.ui.comboBox_ins_type, nhi.INS_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_visit, nhi.VISIT)
        ui_settings.set_combo_box(self.ui.comboBox_reg_type, nhi.REG_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_share_type, nhi.SHARE_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_treat_type, nhi.TREAT_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_injury_type, nhi.INJURY_TYPE)
        ui_settings.set_combo_box(self.ui.comboBox_card, nhi.CARD)
        ui_settings.set_combo_box(self.ui.comboBox_course, nhi.COURSE)
        ui_settings.set_combo_box(self.ui.comboBox_period, nhi.PERIOD)
        ui_settings.set_combo_box(self.ui.comboBox_room, nhi.ROOM)

    # 取消掛號
    def action_cancel_triggered(self):
        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.ui.lineEdit_query.setFocus()

    # 存檔
    def action_save_triggered(self):
        self._save_files()
        self._set_reg_mode(True)
        self.ui.groupBox_search_patient.setEnabled(True)
        self.read_wait()
        self.ui.lineEdit_query.setFocus()

    # comboBox 內容變更
    def selection_changed(self, i):
        sender_name = self.sender().objectName()
        if sender_name == 'comboBox_ins_type':
            if self.ui.comboBox_ins_type.currentText() == '健保':
                self.ui.comboBox_card.setCurrentText('自動取得')
            else:
                self.ui.comboBox_card.setCurrentText('不需取得')
        elif sender_name == 'comboBox_period' or sender_name == 'comboBox_room':
            period = self.ui.comboBox_period.currentText()
            room = self.ui.comboBox_room.currentText()
            reg_no = registration_utils.get_reg_no(self.database, self.system_settings, room, period)  # 取得診號
            self.ui.spinBox_reg_no.setValue(int(reg_no))

    # 開始查詢病患資料
    def query_clicked(self):
        query_str = str(self.ui.lineEdit_query.text())
        if query_str == '':
            return

        row = patient_utils.search_patient(self.ui, self.database, self.system_settings, query_str)
        if row is None: # 找不到資料
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('查無資料')
            msg_box.setText("<font size='4' color='red'><b>找不到有關的病患資料, 請檢查關鍵字是否有誤.</b></font>")
            msg_box.setInformativeText("請確定輸入資料的正確性, 生日請輸入YYYY-MM-DD.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            self.ui.lineEdit_query.setFocus()
        elif row == -1: # 取消查詢
            self.ui.lineEdit_query.setFocus()
        else:
            self._prepare_registration_data(row)

        self.ui.lineEdit_query.clear()

    # 準備掛號
    def _prepare_registration_data(self, row):
        self._set_patient_data(row)
        self._set_registration_data(row)
        self._set_fee(row)

    # 顯示病患資料
    def _set_patient_data(self, row):
        self._set_reg_mode(False)
        self.ui.lineEdit_patient_key.setText(str(row[0]['PatientKey']))
        self.ui.lineEdit_name.setText(str(row[0]['Name']))
        self.ui.lineEdit_id.setText(str(row[0]['ID']).strip(None))
        self.ui.lineEdit_share_type.setText(str(row[0]['InsType']).strip(None))
        self.ui.lineEdit_discount_type.setText(str(row[0]['DiscountType']).strip(None))
        self.ui.lineEdit_birthday.setText(str(row[0]['Birthday']).strip(None))
        self.ui.lineEdit_telephone.setText(str(row[0]['Telephone']).strip(None))
        self.ui.lineEdit_cellphone.setText(str(row[0]['Cellphone']).strip(None))
        self.ui.lineEdit_address.setText(str(row[0]['Address']).strip(None))
        self.ui.lineEdit_patient_remark.setText(strings.get_str(row[0]['Remark'], 'utf8'))
        self.ui.comboBox_card.setFocus()

    def _set_registration_data(self, row):
        ins_type = self.system_settings.field('預設門診類別')
        room = self.system_settings.field('診療室')  # 取得預設診療室
        reg_no = registration_utils.get_reg_no(self.database, self.system_settings, room)  # 取得診號

        self.ui.comboBox_ins_type.setCurrentText(ins_type)
        self.ui.comboBox_room.setCurrentText(room)
        self.ui.spinBox_reg_no.setValue(int(reg_no))
        self.ui.comboBox_period.setCurrentText(registration_utils.get_period(self.system_settings))

    def _set_fee(self, row):
        self.ui.lineEdit_regist_fee.setText("100")

    def _save_files(self):
        case_key = self._save_medical_record()
        self._save_wait(case_key)

    def _save_medical_record(self):
        fields = ['CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType', 'Injury',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Remark']
        data = (
                str(datetime.datetime.now()),
                self.ui.lineEdit_patient_key.text(),
                self.ui.lineEdit_name.text(),
                self.ui.comboBox_visit.currentText(),
                self.ui.comboBox_reg_type.currentText(),
                self.ui.comboBox_injury_type.currentText(),
                self.ui.comboBox_treat_type.currentText(),
                self.ui.comboBox_share_type.currentText(),
                self.ui.comboBox_ins_type.currentText(),
                self.ui.comboBox_card.currentText(),
                number.str_to_int(self.ui.comboBox_course.currentText()),
                self.ui.comboBox_period.currentText(),
                self.ui.comboBox_room.currentText(),
                self.ui.spinBox_reg_no.value(),
                self.ui.comboBox_massager.currentText(),
                self.ui.comboBox_remark.currentText(),
                )
        last_row_id = self.database.insert_record('cases', fields, data)
        return last_row_id

    def _save_wait(self, case_key):
        fields = ['CaseKey', 'CaseDate', 'PatientKey', 'Name', 'Visit', 'RegistType',
                  'TreatType', 'Share', 'InsType', 'Card', 'Continuance', 'Period',
                  'Room', 'RegistNo', 'Massager', 'Remark']
        data = (case_key,
                str(datetime.datetime.now()),
                self.ui.lineEdit_patient_key.text(),
                self.ui.lineEdit_name.text(),
                self.ui.comboBox_visit.currentText(),
                self.ui.comboBox_reg_type.currentText(),
                self.ui.comboBox_treat_type.currentText(),
                self.ui.comboBox_share_type.currentText(),
                self.ui.comboBox_ins_type.currentText(),
                self.ui.comboBox_card.currentText(),
                number.str_to_int(self.ui.comboBox_course.currentText()),
                self.ui.comboBox_period.currentText(),
                self.ui.comboBox_room.currentText(),
                self.ui.spinBox_reg_no.value(),
                self.ui.comboBox_massager.currentText(),
                self.ui.comboBox_remark.currentText(),
                )
        self.database.insert_record('wait', fields, data)

    def delete_wait_clicked(self):
        name = self.table_widget_wait.field_value(3)
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('刪除掛號資料')
        msg_box.setText("<font size='4' color='red'><b>確定刪除 <font color='blue'>{0}</font> 的掛號資料?</b></font>"
                        .format(name))
        msg_box.setInformativeText("注意！資料刪除後, 將無法回復!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        delete_record = msg_box.exec_()
        if not delete_record:
            return

        wait_key = self.table_widget_wait.field_value(0)
        case_key = self.table_widget_wait.field_value(1)

        self.database.delete_record('wait', 'WaitKey', wait_key)
        self.database.delete_record('cases', 'CaseKey', case_key)
        self.ui.tableWidget_wait.removeRow(self.ui.tableWidget_wait.currentRow())
        if self.ui.tableWidget_wait.rowCount() <= 0:
            self._set_tool_button(False)

    # 補印收據
    def print_wait_clicked(self):
        case_key = self._get_tabWidget_wait_row_data(1)
        print_regist = print_registration.PrintRegistration(case_key, self.database, self.system_settings)
        print_regist.printing()
        del print_regist

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_registration(self):
        self.close_all()
        self.close_tab()


# 主程式
def main():
    app = QtWidgets.QApplication(sys.argv)
    widget = Registration()
    widget.show()
    sys.exit(app.exec_())


# 程式開始
if __name__ == '__main__':
    main()
