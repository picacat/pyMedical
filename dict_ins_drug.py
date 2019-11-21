#!/usr/bin/env python3
#coding: utf-8

import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton, QFileDialog, QProgressBar

import urllib.request
from threading import Thread
from queue import Queue

import datetime
from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import nhi_utils
from libs import string_utils
from pyexcel_ods3 import get_data


# 健保藥品 2019.03.13
class DictInsDrug(QtWidgets.QMainWindow):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DictInsDrug, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._read_medicine()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    def close_tab(self):
        current_tab = self.parent.ui.tabWidget_window.currentIndex()
        self.parent.close_tab(current_tab)

    def close_app(self):
        self.close_all()
        self.close_tab()

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DICT_INS_DRUG, self)
        system_utils.set_css(self, self.system_settings)
        self.table_widget_medicine = table_widget.TableWidget(
            self.ui.tableWidget_medicine, self.database
        )
        self.table_widget_drug = table_widget.TableWidget(
            self.ui.tableWidget_drug, self.database
        )
        self.table_widget_drug.set_column_hidden([0])
        self.table_widget_medicine.set_column_hidden([0])
        self._set_table_width()
        self._set_combo_box_supplier()
        self._set_spin_box_valid_date()

        self.ui.action_update_valid_date.setEnabled(False)

    def _set_combo_box_supplier(self):
        sql = '''
            SELECT Supplier FROM drug
            WHERE
                Supplier IS NOT NULL AND
                LENGTH(Supplier) > 0
            GROUP BY Supplier
            ORDER BY LENGTH(Supplier), CAST(CONVERT(`Supplier` using big5) AS BINARY)
        '''
        rows = self.database.select_record(sql)
        supplier_list = []
        for row in rows:
            supplier_list.append(string_utils.xstr(row['Supplier']))

        ui_utils.set_combo_box(self.ui.comboBox_supplier, supplier_list, '全部')

    def _set_spin_box_valid_date(self):
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month

        self.ui.spinBox_valid_year.setValue(current_year)
        self.ui.spinBox_valid_month.setValue(current_month)

        self.ui.spinBox_valid_year.setMinimum(current_year-1)

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 100, 250, 100, 280, 120, 50]
        self.table_widget_drug.set_table_heading_width(width)

        width = [100, 50, 180, 100, 120, 50, 180]
        self.table_widget_medicine.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.action_sync_drug.triggered.connect(self._sync_drug)
        self.ui.action_update_drug.triggered.connect(self._update_ins_drug)
        self.ui.action_close.triggered.connect(self._close_ins_drug)
        self.ui.action_update_valid_date.triggered.connect(self._update_valid_date)
        self.ui.tableWidget_medicine.itemSelectionChanged.connect(self._medicine_item_selection_changed)
        self.ui.lineEdit_medicine_query.textChanged.connect(self._medicine_name_changed)
        self.ui.lineEdit_drug_query.textChanged.connect(self._drug_name_changed)
        self.ui.radioButton_all.clicked.connect(self._filter_medicine)
        self.ui.radioButton_errors.clicked.connect(self._filter_medicine)
        self.ui.spinBox_valid_year.valueChanged.connect(self._valid_date_changed)
        self.ui.spinBox_valid_month.valueChanged.connect(self._valid_date_changed)

    def _read_medicine(self, medicine_name=None):
        medicine_name_script = ''
        if medicine_name is not None and medicine_name != '':
            medicine_name_script = ' AND medicine.MedicineName LIKE "%{medicine_name}%"'.format(
                medicine_name=medicine_name,
            )

        sql = '''
            SELECT medicine.*, drug.ValidDate FROM medicine
                LEFT JOIN drug ON medicine.InsCode = drug.InsCode
            WHERE
                medicine.MedicineType IN ({medicine_type})
                {medicine_name_script}
            ORDER BY FIELD(medicine.MedicineType, {medicine_type}), 
                     LENGTH(MedicineName), CAST(CONVERT(`MedicineName` using big5) AS BINARY)
        '''.format(
            medicine_type=str(nhi_utils.INS_MEDICINE_TYPE)[1:-1],
            medicine_name_script=medicine_name_script,
        )
        self.table_widget_medicine.set_db_data(sql, self._set_medicine_data)

    def _set_medicine_data(self, row_no, row):
        error_message = []

        medicine_key = string_utils.xstr(row['MedicineKey'])
        ins_code = string_utils.xstr(row['InsCode']).strip()
        valid_date = string_utils.xstr(row['ValidDate'])
        if valid_date != '' and '-' not in valid_date:
            valid_date = '{year}-{month:0>2}-{day:0>2}'.format(
                year=valid_date[:4],
                month=valid_date[4:6],
                day=valid_date[6:8],
            )

        expire_date = '{valid_year}-{valid_month:0>2}-01'.format(
            valid_year=self.ui.spinBox_valid_year.value(),
            valid_month=self.ui.spinBox_valid_month.value(),
        )

        if ins_code != '':
            if valid_date == '':
                error_message.append('健保碼無效')
            elif valid_date < expire_date:
                error_message.append('健保碼過期')

        medicine_row = [
            medicine_key,
            string_utils.xstr(row['MedicineType']),
            string_utils.xstr(row['MedicineName']),
            ins_code,
            valid_date,
            None,
            ', '.join(error_message)
        ]

        for column in range(len(medicine_row)):
            self.ui.tableWidget_medicine.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medicine_row[column])
            )
            if len(error_message) > 0:
                self.ui.tableWidget_medicine.item(
                    row_no, column).setForeground(
                    QtGui.QColor('red')
                )

        gtk_apply = './icons/gtk-clear.svg'
        if ins_code != '':
            ui_utils.set_table_widget_field_icon(
                self.ui.tableWidget_medicine, row_no, 5, gtk_apply,
                'medicine_key', medicine_key, self._clear_ins_code)

    def _clear_ins_code(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('清除健保碼')
        msg_box.setText(
            '''
            <font size="4" color="red">
              <b>確定清除{medicine_name}的健保藥碼?<br>
            </font>
            '''.format(medicine_name=self.table_widget_medicine.field_value(2))
        )
        msg_box.setInformativeText("健保碼清除後, 若想反悔, 可以至右邊的健保藥品詞庫點選新的健保藥品資料.")
        msg_box.addButton(QPushButton("確定清除"), QMessageBox.YesRole)
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        cancel = msg_box.exec_()
        if cancel:
            return

        medicine_key = self.table_widget_medicine.field_value(0)
        sql = '''
            UPDATE medicine
            SET
                InsCode = NULL
            WHERE
                MedicineKey = {medicine_key}
        '''.format(
            medicine_key=medicine_key,
        )
        self.database.exec_sql(sql)

        row_no = self.ui.tableWidget_medicine.currentRow()

        for column in range(3, 5):
            self.ui.tableWidget_medicine.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem('')
            )
        self.ui.tableWidget_medicine.setCellWidget(
            row_no, 5, None
        )

    def _sync_drug(self):
        options = QFileDialog.Options()

        file_name, _ = QFileDialog.getOpenFileName(
            self, "開啟健保藥品檔",
            '*.ods', "ods 檔 (*.ods);;Text Files (*.txt)", options = options
        )
        if not file_name:
            return

        medicine_type = '單方'
        if medicine_type not in file_name:
            medicine_type = '複方'

        sql = '''
            DELETE FROM drug
            WHERE
                MedicineType = "{medicine_type}" OR
                MedicineType IS NULL
        '''.format(
            medicine_type=medicine_type,
        )
        self.database.exec_sql(sql)

        rows = get_data(file_name)['Sheet1']
        progress_bar = QProgressBar()
        progress_bar.setMaximum(len(rows))
        progress_bar.setValue(0)
        self.ui.statusbar.addWidget(progress_bar)
        self._write_ins_drug(medicine_type, rows, progress_bar)

        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('健保碼轉入完成')
        msg_box.setText(
            '''
                <b>{medicine_type}類健保藥碼更新完成.<br>
            '''.format(
                medicine_type=medicine_type
            )
        )
        msg_box.setInformativeText("恭喜您, 現在已經是最新的健保藥品資料.")
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        msg_box.exec_()

        self.ui.statusbar.removeWidget(progress_bar)

    def _write_ins_drug(self, medicine_type, rows, progress_bar):
        ins_code_no = self._get_field_number(rows[0], '藥品代碼')
        drug_name_no = self._get_field_number(rows[0], '藥品名稱')
        drug_type_no = self._get_field_number(rows[0], '劑型')
        supplier_no = self._get_field_number(rows[0], '製造廠名稱')
        valid_date_no = self._get_field_number(rows[0], '有效期間')

        for row_no, row in zip(range(len(rows)), rows):
            progress_bar.setValue(row_no+1)
            if row_no == 0:  # data heading 不轉檔
                continue

            try:
                ins_code = row[ins_code_no]
                drug_name = row[drug_name_no]
                drug_type = row[drug_type_no]
                supplier = row[supplier_no]
                valid_date = string_utils.xstr(row[valid_date_no])
                valid_date = '{0}-{1}-{2}'.format(
                    valid_date[:4],
                    valid_date[4:6],
                    valid_date[6:8],
                )
            except IndexError:
                continue

            field = [
                'InsCode', 'DrugName', 'MedicineType', 'Unit', 'Supplier', 'ValidDate',
            ]

            data = [
                ins_code, drug_name, medicine_type, drug_type, supplier, valid_date,
            ]

            self.database.insert_record('drug', field, data)

    def _get_field_number(self, row, field_name):
        for col_no, col_name in zip(range(len(row)), row):
            if col_name == field_name:
                return col_no

        return 0

    def _close_ins_drug(self):
        self.close_all()
        self.close_tab()

    def _medicine_item_selection_changed(self):
        medicine_name = string_utils.strip_string(self.table_widget_medicine.field_value(2))
        self._read_drug(medicine_name)

    def _read_drug(self, drug_name):
        if drug_name == '':
            self.ui.tableWidget_drug.setRowCount(0)
            return

        supplier = self.ui.comboBox_supplier.currentText()
        if supplier == '全部':
            supplier_script = ''
        else:
            supplier_script = ' AND Supplier LIKE "%{supplier}%"'.format(
                supplier=supplier,
            )

        sql = '''
            SELECT * FROM drug
            WHERE
                DrugName LIKE "%{drug_name}%"
                {supplier_script}
            ORDER BY ValidDate DESC, LENGTH(DrugName), CAST(CONVERT(`DrugName` using big5) AS BINARY)
        '''.format(
            drug_name=drug_name,
            supplier_script=supplier_script,
        )

        self.table_widget_drug.set_db_data(sql, self._set_drug_data)
        self.ui.tableWidget_medicine.setFocus(True)

    def _set_drug_data(self, row_no, row):
        drug_row = [
            string_utils.xstr(row['DrugKey']),
            string_utils.xstr(row['InsCode']),
            string_utils.xstr(row['DrugName']),
            string_utils.xstr(row['Unit']),
            string_utils.xstr(row['Supplier']),
            string_utils.xstr(row['ValidDate']),
        ]

        for column in range(len(drug_row)):
            self.ui.tableWidget_drug.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(drug_row[column])
            )
            if string_utils.xstr(row['InsCode']) == self.table_widget_medicine.field_value(3):
                self.ui.tableWidget_drug.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

        gtk_apply = './icons/gtk-edit.svg'
        drug_key = self.table_widget_drug.field_value(0)
        ui_utils.set_table_widget_field_icon(
            self.ui.tableWidget_drug, row_no, 6, gtk_apply,
            'drug_key', drug_key, self._set_ins_drug)

    def _set_ins_drug(self):
        drug_code = self.table_widget_drug.field_value(1)
        valid_date = self.table_widget_drug.field_value(5)
        medicine_key = self.table_widget_medicine.field_value(0)
        sql = '''
            UPDATE medicine
            SET
                InsCode = "{ins_code}"
            WHERE
                MedicineKey = {medicine_key}
        '''.format(
            ins_code=drug_code,
            medicine_key=medicine_key,
        )

        self.database.exec_sql(sql)

        self.ui.tableWidget_medicine.setItem(
            self.ui.tableWidget_medicine.currentRow(), 3,
            QtWidgets.QTableWidgetItem(string_utils.xstr(drug_code))
        )
        self.ui.tableWidget_medicine.setItem(
            self.ui.tableWidget_medicine.currentRow(), 4,
            QtWidgets.QTableWidgetItem(string_utils.xstr(valid_date))
        )

        gtk_apply = './icons/gtk-clear.svg'
        ui_utils.set_table_widget_field_icon(
            self.ui.tableWidget_medicine, self.ui.tableWidget_medicine.currentRow(), 5, gtk_apply,
            'medicine_key', medicine_key, self._clear_ins_code)

    def _locate_drug(self, ins_code):
        ins_code_found = False
        for row_no in range(self.ui.tableWidget_drug.rowCount()):
            self.ui.tableWidget_drug.setCurrentCell(row_no, 1)
            drug_code = self.table_widget_drug.field_value(1)
            if ins_code == drug_code:
                ins_code_found = True

        if not ins_code_found:
            self.ui.tableWidget_drug.setCurrentCell(0, 1)

    def _medicine_name_changed(self):
        medicine_name = self.ui.lineEdit_medicine_query.text()
        self._read_medicine(medicine_name)
        self._medicine_item_selection_changed()
        self.ui.lineEdit_medicine_query.setFocus(True)
        self.ui.lineEdit_medicine_query.setCursorPosition(len(medicine_name))

    def _filter_medicine(self):
        self.ui.action_update_valid_date.setEnabled(True)

        if self.ui.radioButton_all.isChecked():
            self.ui.action_update_valid_date.setEnabled(False)
            self._read_medicine()
            return

        for row_no in range(self.ui.tableWidget_medicine.rowCount()-1, -1, -1):
            error_item = self.ui.tableWidget_medicine.item(row_no, 6)
            if error_item is None or error_item.text() == '':
                self.ui.tableWidget_medicine.removeRow(row_no)

    def _drug_name_changed(self):
        drug_name = self.ui.lineEdit_drug_query.text()
        self._read_drug(drug_name)
        self.ui.lineEdit_drug_query.setFocus(True)
        self.ui.lineEdit_drug_query.setCursorPosition(len(drug_name))

    def _valid_date_changed(self):
        self._read_medicine()
        self._filter_medicine()

    def _update_valid_date(self):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle('更新有效期限')
        msg_box.setText("<font size='4' color='blue'><b>確定更新過期藥品的有效期限?</b></font>")
        msg_box.setInformativeText("注意！有效期限只會更新健保藥品第一欄的資料!")
        msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
        msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
        update_record = msg_box.exec_()
        if not update_record:
            return

        record_count = self.ui.tableWidget_medicine.rowCount()

        progress_dialog = QtWidgets.QProgressDialog(
            '正在更新健保藥品有效期限中, 請稍後...', '取消', 0, record_count, self
        )

        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no in range(record_count):
            progress_dialog.setValue(row_no)
            if progress_dialog.wasCanceled():
                break

            self.ui.tableWidget_medicine.setCurrentCell(row_no, 1)
            if self.ui.tableWidget_drug.rowCount() > 0:
                self._set_ins_drug()

        progress_dialog.setValue(record_count)
        self._read_medicine()
        self._filter_medicine()

    @staticmethod
    def _message_box(title, message, hint):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setInformativeText(hint)
        msg_box.setStandardButtons(QMessageBox.NoButton)

        return msg_box

    def _download_file_thread(self, out_queue, download_file_name, url):
        QtCore.QCoreApplication.processEvents()

        u = urllib.request.urlopen(url)
        data = u.read()
        u.close()
        with open(download_file_name, "wb") as f:
            f.write(data)

        out_queue.put(download_file_name)

    # 取得安全簽章
    def _download_drug_file(self, file_name, url):
        title = '下載健保藥品更新檔'
        message = '<font size="4" color="red"><b>正在下載健保藥品更新檔, 請稍後...</b></font>'
        hint = '正在與更新檔資料庫連線, 會花費一些時間.'
        msg_box = self._message_box(title, message, hint)
        msg_box.show()

        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()

        t = Thread(target=self._download_file_thread, args=(msg_queue, file_name, url))
        t.start()
        download_file_name = msg_queue.get()
        msg_box.close()

        return download_file_name

    def _update_drug(self, medicine_type, file_name, url):
        file_name = self._download_drug_file(file_name, url)

        sql = '''
            DELETE FROM drug
            WHERE
                MedicineType = "{medicine_type}" OR
                MedicineType IS NULL
        '''.format(
            medicine_type=medicine_type,
        )
        self.database.exec_sql(sql)

        rows = get_data(file_name)['工作表1']

        progress_bar = QProgressBar()
        progress_bar.setMaximum(len(rows))
        progress_bar.setValue(0)
        self.ui.statusbar.addWidget(progress_bar)
        self._write_ins_drug(medicine_type, rows, progress_bar)
        self.ui.statusbar.removeWidget(progress_bar)

    def _update_ins_drug(self):
        self._update_drug(
            '單方',
            'drug1.ods',
            'https://www.dropbox.com/s/w3g0qdqh47w7i42/drug1.ods?dl=1',
        )
        self._update_drug(
            '複方',
            'drug2.ods',
            'https://www.dropbox.com/s/yhdxk52tod05e81/drug2.ods?dl=1',
        )

        system_utils.show_message_box(
            QMessageBox.Information,
            '線上更新健保碼',
            '<font size="4" color="blue"><b>最新版本的健保碼更新已完成.</b></font>',
            '恭喜您! 現在已經是最新的健保藥品'
        )

