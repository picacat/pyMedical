#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui

from classes import db
from classes import table_widget

from libs import system_utils
from libs import ui_utils
from libs import string_utils
from libs import number_utils
from libs import case_utils


# 主視窗
class DialogMedicalRecordHosts(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogMedicalRecordHosts, self).__init__(parent)
        self.parent = parent
        self.database = args[0]
        self.system_settings = args[1]
        self.patient_id = args[2]

        self.ui = None
        self.copy_medical_record = True

        self._set_ui()
        self._set_signal()
        self._read_medical_records()

    # 解構
    def __del__(self):
        self.close_all()

    # 關閉
    def close_all(self):
        pass

    # 設定GUI
    def _set_ui(self):
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_MEDICAL_RECORD_HOSTS, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('拷貝病歷')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.table_widget_medical_records = table_widget.TableWidget(
            self.ui.tableWidget_medical_records, self.database
        )
        self.table_widget_medical_records.set_column_hidden([0])
        self._set_table_width()

    # 設定欄位寬度
    def _set_table_width(self):
        width = [100, 170, 110, 50, 80, 60, 50, 220, 45, 80, 80]
        self.table_widget_medical_records.set_table_heading_width(width)

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.accepted_button_clicked)
        self.ui.tableWidget_medical_records.itemSelectionChanged.connect(self._medical_record_changed)

    def accepted_button_clicked(self):
        if not self.copy_medical_record:
            return

        case_key = self.table_widget_medical_records.field_value(0)
        clinic_name = self.table_widget_medical_records.field_value(1)
        database = self.database_list[clinic_name]

        if self.ui.radioButton_ins_prescript.isChecked():
            copy_ins_prescript_to = '健保處方'
        else:
            copy_ins_prescript_to = '自費處方'

        case_utils.copy_host_medical_record(
            database, self.parent, case_key,
            self.ui.checkBox_diagnostic.isChecked(),
            self.ui.checkBox_remark.isChecked(),
            self.ui.checkBox_disease.isChecked(),
            self.ui.checkBox_ins_prescript.isChecked(),
            copy_ins_prescript_to,
            self.ui.checkBox_ins_treat.isChecked(),
            self.ui.checkBox_self_prescript.isChecked(),
        )

    def _read_medical_records(self):
        medical_records = []

        sql = '''
            SELECT * FROM hosts
            ORDER BY HostsKey
        '''
        rows = self.database.select_record(sql)
        self.database_list = {}
        for row in rows:
            clinic_name = string_utils.xstr(row['ClinicName'])
            HIS_version = string_utils.xstr(row['HISVersion'])
            database_hosts = db.Database(
                host=row['Host'],
                user=row['UserName'],
                password=row['Password'],
                database=row['DatabaseName'],
                charset=row['Charset'],
            )
            self.database_list[clinic_name] = database_hosts
            medical_records += self._get_medical_records(
                database_hosts, clinic_name, HIS_version
            )

        if len(medical_records) <= 0:
            html = '''
                {br} 
                <center><b>無分院病歷</b></center>
            '''.format(
                br='<br>' * 12,
            )
            self.ui.textEdit_medical_record.setHtml(html)
            self.ui.groupBox_copy_option.setEnabled(False)
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

            return

        self._set_group_box_title(medical_records[0])
        self._set_table_data(medical_records)

    def _get_medical_records(self, database_hosts, clinic_name, HIS_version):
        if HIS_version == 'Medical':
            gender = 'Sex'
            treat_type = 'RegistType'
        else:
            gender = 'Gender'
            treat_type = 'TreatType'

        medical_records = []
        sql = '''
            SELECT PatientKey, {gender}, Birthday FROM patient
            WHERE
                ID = "{patient_id}"
        '''.format(
            gender=gender,
            patient_id=self.patient_id,
        )
        rows = database_hosts.select_record(sql)
        if len(rows) <= 0:
            return medical_records

        patient_key = rows[0]['PatientKey']
        gender = rows[0][gender]
        birthday = rows[0]['Birthday']

        sql = '''
            SELECT
                CaseKey, PatientKey, Name, CaseDate, InsType, {treat_type},
                Card, Continuance, PresDays1, PresDays2, 
                DiseaseName1, Doctor, TotalFee 
            FROM cases
            WHERE
                PatientKey = {patient_key}
        '''.format(
            treat_type=treat_type,
            patient_key=patient_key,
        )
        rows = database_hosts.select_record(sql)
        if len(rows) <= 0:
            return medical_records

        for row in rows:
            medical_records.append(
                {
                    'CaseKey': row['CaseKey'],
                    'ClinicName': clinic_name,
                    'PatientKey': row['PatientKey'],
                    'Name': row['Name'],
                    'Gender': gender,
                    'Birthday': birthday,
                    'CaseDate': row['CaseDate'],
                    'InsType': row['InsType'],
                    'TreatType': row[treat_type],
                    'Card': row['Card'],
                    'Continuance': row['Continuance'],
                    'PresDays1': row['PresDays1'],
                    'PresDays2': row['PresDays2'],
                    'DiseaseName1': row['DiseaseName1'],
                    'Doctor': row['Doctor'],
                    'TotalFee': row['TotalFee'],
                    'HISVersion': HIS_version,
                }
            )

        return medical_records

    def _set_table_data(self, medical_records):
        record_count = len(medical_records)

        self.ui.tableWidget_medical_records.setRowCount(record_count)
        for row_no, row in zip(range(record_count), medical_records):
            self._set_row_data(row_no, row)

        self.ui.tableWidget_medical_records.setAlternatingRowColors(True)
        self.ui.tableWidget_medical_records.resizeRowsToContents()
        self.ui.tableWidget_medical_records.sortItems(2, QtCore.Qt.DescendingOrder)
        self.ui.tableWidget_medical_records.setCurrentCell(0, 1)

    def _set_row_data(self, row_no, row):
        case_key = row['CaseKey']
        if row['InsType'] == '健保':
            medicine_set = 1
        else:
            medicine_set = 2

        HIS_version = string_utils.xstr(row['HISVersion'])
        if HIS_version in ['Medical', 'Med2000']:
            pres_days = row['PresDays{0}'.format(medicine_set)]
        else:
            pres_days = case_utils.get_pres_days(self.database, case_key, medicine_set)

        medical_record_data = [
            string_utils.xstr(case_key),
            string_utils.xstr(row['ClinicName']),
            string_utils.xstr(row['CaseDate'].date()),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['TreatType']),
            string_utils.xstr(row['Card']),
            string_utils.xstr(row['Continuance']),
            string_utils.xstr(row['DiseaseName1']),
            string_utils.xstr(pres_days),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr('{0:,}'.format(number_utils.get_integer(row['TotalFee']))),
        ]

        for column in range(len(medical_record_data)):
            self.ui.tableWidget_medical_records.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record_data[column])
            )
            if column in [0, 8, 10]:
                self.ui.tableWidget_medical_records.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [6]:
                self.ui.tableWidget_medical_records.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

            if row['InsType'] == '自費' or number_utils.get_integer(row['TotalFee']) > 0:
                self.ui.tableWidget_medical_records.item(
                    row_no, column).setForeground(
                    QtGui.QColor('blue')
                )

            if row['Continuance'] == 1:
                self.ui.tableWidget_medical_records.item(
                    row_no, column).setBackground(
                    QtGui.QColor('lightgray')
                )

    def _set_group_box_title(self, row):
        self.ui.groupBox_medical_record.setTitle(
            '{name}({gender}) 出生日期: {birthday}  病歷內容'.format(
                name=string_utils.xstr(row['Name']),
                gender=string_utils.xstr(row['Gender']),
                birthday=string_utils.xstr(row['Birthday']),
            )
        )

    def _medical_record_changed(self):
        case_key = self.table_widget_medical_records.field_value(0)
        clinic_name = self.table_widget_medical_records.field_value(1)

        self._set_copy_prescript_check_box()
        html = case_utils.get_medical_record_html(
            self.database_list[clinic_name], self.system_settings, case_key
        )
        self.ui.textEdit_medical_record.setHtml(html)

    def _set_copy_prescript_check_box(self):
        case_key = self.table_widget_medical_records.field_value(0)
        clinic_name = self.table_widget_medical_records.field_value(1)
        ins_type = self.table_widget_medical_records.field_value(3)
        database = self.database_list[clinic_name]

        self.ui.checkBox_ins_prescript.setChecked(False)  # 健保療程2-6次預設不拷貝藥品
        self.ui.checkBox_ins_prescript.setEnabled(False)  # 健保療程2-6次預設不拷貝藥品

        self.ui.radioButton_ins_prescript.setEnabled(False)
        self.ui.radioButton_self_prescript.setEnabled(False)

        self.ui.checkBox_ins_treat.setChecked(False)
        self.ui.checkBox_ins_treat.setEnabled(False)

        if ins_type == '健保':
            sql = 'SELECT Treatment FROM cases WHERE CaseKey = {0}'.format(case_key)
            rows = database.select_record(sql)
            treatment = string_utils.xstr(rows[0]['Treatment'])

            if treatment != '':
                self.ui.checkBox_ins_treat.setEnabled(True)
                self.ui.checkBox_ins_treat.setChecked(True)

            sql = '''
                SELECT PrescriptKey FROM prescript 
                WHERE 
                    CaseKey = {case_key} AND 
                    MedicineSet = 1 
            '''.format(
                case_key=case_key,
            )
            rows = database.select_record(sql)
            if len(rows) > 0:
                self.ui.checkBox_ins_prescript.setEnabled(True)
                self.ui.radioButton_ins_prescript.setEnabled(True)
                self.ui.radioButton_self_prescript.setEnabled(True)
                if treatment == '':
                    self.ui.checkBox_ins_prescript.setChecked(True)  # 預設非療程才拷貝藥品

        sql = 'SELECT MedicineSet FROM prescript WHERE CaseKey = {0} AND MedicineSet >= 2'.format(case_key)
        rows = database.select_record(sql)
        if len(rows) > 0:
            copy_self_prescript = True
        else:
            copy_self_prescript = False

        self.ui.checkBox_self_prescript.setEnabled(copy_self_prescript)
        self.ui.checkBox_self_prescript.setChecked(copy_self_prescript)
        if copy_self_prescript:
            self.ui.checkBox_self_prescript.setChecked(False)  # 預設不要拷貝

