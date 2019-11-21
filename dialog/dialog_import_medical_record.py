#!/usr/bin/env python3
#coding: utf-8

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import json

from classes import table_widget

from libs import ui_utils
from libs import system_utils
from libs import string_utils
from libs import case_utils


# 匯入病歷資料 2019.09.29
class DialogImportMedicalRecord(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogImportMedicalRecord, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]

        self.ui = None

        self._set_ui()
        self._set_signal()
        self._open_file_dialog()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_IMPORT_MEDICAL_RECORD, self)
        # self.setFixedSize(self.size())  # non resizable dialog
        system_utils.set_css(self, self.system_settings)
        self.center()
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('匯入資料庫')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')

        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )
        self.table_widget_medical_record.set_column_hidden([0])
        self._set_table_width()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center_point = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_medical_record.itemSelectionChanged.connect(self._item_selection_changed)

    def accepted_button_clicked(self):
        self._import_to_database()

        self.close()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 20, 180, 90, 50, 90, 70, 50, 200, 50, 90]
        self.table_widget_medical_record.set_table_heading_width(width)

    def _open_file_dialog(self):
        options = QFileDialog.Options()

        file_name, _ = QFileDialog.getOpenFileName(
            self, "開啟病歷JSON檔",
            '*.json', "json 檔 (*.json);;", options=options
        )
        if not file_name:
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).animateClick()
            return

        self._read_medical_record_json(file_name)

    def _read_medical_record_json(self, file_name):
        with open(file_name, encoding='utf8') as json_file:
            rows = json.load(json_file)
            for row_no, row in zip(range(len(rows)), rows):
                self._set_medical_record(row_no, row)

    def _set_medical_record(self, row_no, row):
        self.ui.tableWidget_medical_record.insertRow(row_no)

        medical_record_row = [
            string_utils.xstr(row),
            None,
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['DiseaseName1']),
            None,
            string_utils.xstr(row['Doctor']),
        ]

        for col_no in range(len(medical_record_row)):
            item = QtWidgets.QTableWidgetItem()
            item.setData(QtCore.Qt.EditRole, medical_record_row[col_no])

            self.ui.tableWidget_medical_record.setItem(
                row_no, col_no, item
            )
            if col_no in [9]:
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif col_no in [4, 7]:
                self.ui.tableWidget_medical_record.item(
                    row_no, col_no).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        check_box = QtWidgets.QCheckBox(self.ui.tableWidget_medical_record)
        check_box.setChecked(True)
        self.ui.tableWidget_medical_record.setCellWidget(row_no, 1, check_box)

    def _item_selection_changed(self):
        row_no = self.ui.tableWidget_medical_record.currentRow()
        item = self.ui.tableWidget_medical_record.item(row_no, 0)
        if item is None:
            return

        row = eval(item.text())
        html = case_utils.get_medical_record_row_html(row)
        self.ui.textEdit_medical_record.setHtml(html)

    def _import_to_database(self):
        row_count = self.ui.tableWidget_medical_record.rowCount()
        progress_dialog = QtWidgets.QProgressDialog(
            '正在匯入資料庫中, 請稍後...', '取消', 0, row_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no in range(row_count):
            progress_dialog.setValue(row_no)
            if progress_dialog.wasCanceled():
                break

            check_box = self.ui.tableWidget_medical_record.cellWidget(row_no, 1)
            if not check_box.isChecked():
                continue

            item = self.ui.tableWidget_medical_record.item(row_no, 0)
            if item is None:
                return

            medical_row = eval(item.text())

            patient_row = medical_row['PatientJSON']
            del medical_row['PatientJSON']
            patient_key = self._write_patient(patient_row)

            medical_row['PatientKey'] = patient_key

            treat_row = medical_row['TreatJSON']
            dosage_row = medical_row['DosageJSON']
            prescript_row = medical_row['PrescriptJSON']

            self._remove_medical_row_field(medical_row)

            fields = list(medical_row.keys())
            data = list(medical_row.values())

            case_key = self.database.insert_record('cases', fields, data)
            # try:
            #     massage_case_key = self.database.insert_record('cases', fields, data)
            # except:
            #     del medical_row['Symptom']
            #     fields = list(medical_row.keys())
            #     data = list(medical_row.values())
            #     massage_case_key = self.database.insert_record('cases', fields, data)

            self._write_pres_extend(treat_row, case_key)
            self._write_dosage(dosage_row, case_key)
            self._write_prescript(prescript_row, case_key)

        progress_dialog.setValue(row_count)
        system_utils.show_message_box(
            QMessageBox.Information,
            'JSON資料匯入完成',
            '<h3>病歷資料匯入完成.</h3>',
            '資料正確無誤'
        )

    def _remove_medical_row_field(self, medical_row):
        del medical_row['TreatJSON']
        del medical_row['DosageJSON']
        del medical_row['PrescriptJSON']

        del medical_row['CaseKey']
        del medical_row['TimeStamp']
        medical_row.pop('RegistTypex', None)
        medical_row.pop('Casher', None)
        medical_row.pop('Height', None)
        medical_row.pop('HeartBeat', None)
        for i in range(4, 7):
            medical_row.pop('Package{0}'.format(i), None)
            medical_row.pop('PresDays{0}'.format(i), None)
            medical_row.pop('Instruction{0}'.format(i), None)

        medical_row.pop('SelfTreatment', None)
        medical_row.pop('Acupuncture1', None)
        medical_row.pop('Acupuncture2', None)
        medical_row.pop('EAcupuncture1', None)
        medical_row.pop('EAcupuncture2', None)
        medical_row.pop('Massage1', None)
        medical_row.pop('Massage2', None)
        medical_row.pop('Dislocate1', None)
        medical_row.pop('Dislocate2', None)
        medical_row.pop('ReceiptShare', None)
        medical_row.pop('SMiscFee', None)
        medical_row.pop('TreatShare', None)
        medical_row.pop('DrugShare', None)
        medical_row.pop('Refund', None)
        medical_row.pop('SMaterial', None)
        medical_row.pop('Debt', None)
        medical_row.pop('Cert', None)

    def _write_patient(self, patient_row):
        if len(patient_row) <= 0:
            return 0

        row = patient_row[0]
        sql = '''
            SELECT PatientKey FROM patient
            WHERE
                Name = "{name}" AND
                ID = "{id}"
        '''.format(
            name=string_utils.xstr(row['Name']),
            id=string_utils.xstr(row['ID']),
        )
        rows = self.database.select_record(sql)
        if len(rows) > 0:
            return rows[0]['PatientKey']

        del row['PatientKey']
        row.pop('Sex', None)
        row.pop('Alergy', None)
        del row['TimeStamp']
        fields = list(row.keys())
        data = list(row.values())

        patient_key = self.database.insert_record('patient', fields, data)

        return patient_key

    def _write_pres_extend(self, treat_row, prescript_key):
        if treat_row is None or len(treat_row) <= 0:
            return

        row = treat_row[0]
        del row['PresExtendKey']
        row['PrescriptKey'] = prescript_key
        fields = list(row.keys())
        data = list(row.values())
        self.database.insert_record('presextend', fields, data)

    def _write_dosage(self, dosage_row, case_key):
        for row in dosage_row:
            del row['DosageKey']
            del row['TimeStamp']
            row['CaseKey'] = case_key
            fields = list(row.keys())
            data = list(row.values())
            self.database.insert_record('dosage', fields, data)

    def _write_prescript(self, prescript_row, case_key):
        for row in prescript_row:
            pres_extend_row = row['PresExtendJSON']
            del row['PrescriptKey']
            del row['TimeStamp']
            del row['PresExtendJSON']
            row.pop('Charged', None)

            row['CaseKey'] = case_key
            fields = list(row.keys())
            data = list(row.values())
            prescript_key = self.database.insert_record('prescript', fields, data)
            self._write_pres_extend(pres_extend_row, prescript_key)

