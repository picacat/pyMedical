#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
from threading import Thread
from queue import Queue

from libs import string_utils
from libs import number_utils
from libs import system_utils
from libs import date_utils
from libs import prescript_utils
from libs import case_utils
from libs import nhi_utils
from libs import dialog_utils
from libs import registration_utils


# 系統設定 2018.03.19
class MedicalRecordCheck(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(MedicalRecordCheck, self).__init__(parent)
        self.database = args[0]
        self.system_settings = args[1]
        self.medical_record = args[2]
        self.patient_record = args[3]
        self.treat_type = args[4]
        self.disease_code1 = args[5]
        self.disease_code2 = args[6]
        self.disease_code3 = args[7]
        self.special_code = args[8]
        self.treatment = args[9]
        self.pres_days = args[10]
        self.packages = args[11]
        self.instruction = args[12]
        self.table_widget_ins_prescript = args[13]
        self.table_widget_ins_treat = args[14]
        self.table_widget_ins_care = args[15]
        self.parent = parent

        self._set_ui()
        self._set_signal()

    # 設定GUI
    def _set_ui(self):
        pass

    # 設定信號
    def _set_signal(self):
        pass

    def check_medical_record(self):
        if self.treat_type == '腦血管疾病':
            check_ok = self._check_brain()
        elif self.treat_type == '助孕照護':
            check_ok = self._check_aid_pregnant_care()
        elif self.treat_type == '保胎照護':
            check_ok = self._check_keep_baby_care()
        elif self.treat_type in ['乳癌照護', '肝癌照護']:
            check_ok = self._check_cancer_care()
        elif self.treat_type == '兒童鼻炎':
            check_ok = self._check_child_rhinitis()
        else:
            check_ok = self._check_general()

        return check_ok

    # 檢查主診斷碼
    def _check_disease1_error(self, treat_type, disease_code1):
        error_message = None

        if treat_type == '腦血管疾病':
            if 'G450' <= self.disease_code1 <= 'G468':
                pass
            elif 'I60' <= self.disease_code1 <= 'I68':
                pass
            else:
                error_message = '* ICD-10-CM主診斷碼非腦血管疾病<br>腦血管疾病範圍範圍: G450~G468, I60~I68'
        elif treat_type == '助孕照護':
            if 'N970' <= self.disease_code1 <= 'N979':  # 女性不孕症
                pass
            elif 'N460' <= self.disease_code1 <= 'N469':  # 男性不孕症
                pass
            else:
                error_message = '* ICD-10-CM主診斷碼非不孕症<br>女性不孕症主診斷碼範圍: N970 ~ N979<br>男性不孕症主診斷碼範圍: N4601 ~ N469'
        elif treat_type == '乳癌照護':
            if disease_code1[:3] == 'C50':  # 乳房惡性腫瘤
                pass
            elif disease_code1 == 'C7981':  # 乳房續發性惡性腫瘤
                pass
            else:
                error_message = '* ICD-10-CM主診斷碼非乳癌病名<br>乳癌主診斷碼範圍: C50~, C7981<br>'
        elif treat_type == '肝癌照護':
            if disease_code1[:3] in ['C22', 'C23', 'C24']:  # 肝惡性腫瘤
                pass
            else:
                error_message = '* ICD-10-CM主診斷碼非肝癌病名<br>肝癌主診斷碼範圍: C22~, C23~, C24~<br>'
        elif treat_type == '兒童鼻炎':
            if disease_code1 in ['J301', 'J302', 'J305', 'J3081', 'J3089', 'J309']:
                pass
            else:
                error_message = '* ICD-10-CM主診斷碼非兒童過敏性鼻炎病名<br>過敏性鼻炎主診斷碼範圍: J301, J302, J305, J3081, J3089, J309<br>'

        return error_message

    # 檢查開藥日數
    def _check_pres_days_error(self, treat_type, pres_days):
        error_message = None

        if treat_type == '助孕照護' and pres_days < 7:
            error_message = '* 助孕照護未開立七天以上的內服藥, 請開立內服藥至少七天'
        elif treat_type == '保胎照護' and pres_days < 7:
            error_message = '* 保胎照護未開立七天以上的內服藥, 請開立內服藥至少七天'
        elif treat_type == '乳癌照護' and pres_days < 7:
            error_message = '* 乳癌照護未開立七天以上的內服藥, 請開立內服藥至少七天'
        elif treat_type == '肝癌照護' and pres_days < 7:
            error_message = '* 肝癌照護未開立七天以上的內服藥, 請開立內服藥至少七天'

        return error_message

    # 年齡範圍檢查
    def _check_age_range_error(self, treat_type, medical_record, patient_record, age_range):
        error_message = None

        age_year, age_month = date_utils.get_age(
            patient_record['Birthday'], medical_record['CaseDate'])

        if age_year < age_range[0] or age_year > age_range[1]:
            if treat_type == '兒童鼻炎':
                error_message = '* 兒童過敏性鼻炎病患年齡非{0}-{1}歲兒童, 請改為一般門診'.format(
                    age_range[0], age_range[1],
                )

        return error_message

    def _check_duration_by_ins_code(self, patient_key, case_date,
                                    treat_type, check_ins_code, table_widget_ins_care):
        error_message = None

        if treat_type in ['乳癌照護', '肝癌照護']:
            if table_widget_ins_care is None:
                return error_message

            treat_exists = False
            for row_no in range(table_widget_ins_care.rowCount()):
                ins_code = table_widget_ins_care.item(row_no, 8)
                if ins_code is not None:
                    ins_code = ins_code.text()
                    if ins_code == check_ins_code:
                        treat_exists = True
                        break

            if not treat_exists:  # 無此醫令
                return error_message

            last_two_months = datetime.date(case_date.year, case_date.month, 1) - datetime.timedelta(60)
            start_date = last_two_months.replace(day=1).strftime('%Y-%m-%d 00:00:00')
            end_date = '{0} 23:59:59'.format(case_date.date() - datetime.timedelta(1))
            sql = '''
                SELECT cases.CaseDate, prescript.MedicineName FROM prescript
                LEFT JOIN cases ON prescript.CaseKey = cases.CaseKey
                WHERE
                    cases.PatientKey = {0} AND
                    cases.CaseDate BETWEEN "{1}" AND "{2}" AND
                    InsCode = "{3}"
            '''.format(patient_key, start_date, end_date, check_ins_code)
            rows = self.database.select_record(sql)
            if len(rows) >= 1:
                error_message = '* {0}限三個月申報一次, 上次申報日期為{1}, 請刪除此項醫令'.format(
                    string_utils.xstr(rows[0]['MedicineName']),
                    rows[0]['CaseDate'].date(),
                )
        elif treat_type == '兒童鼻炎':
            if table_widget_ins_care is None:
                return error_message

            treat_exists = False
            for row_no in range(table_widget_ins_care.rowCount()):
                ins_code = table_widget_ins_care.item(row_no, 8)
                if ins_code is not None:
                    ins_code = ins_code.text()
                    if ins_code == check_ins_code:
                        treat_exists = True
                        break

            if not treat_exists:  # 無此醫令
                return error_message

            start_date = datetime.date(case_date.year, 1, 1)
            end_date = '{0} 23:59:59'.format(case_date.date() - datetime.timedelta(1))
            sql = '''
                SELECT cases.CaseDate, prescript.MedicineName FROM prescript
                LEFT JOIN cases ON prescript.CaseKey = cases.CaseKey
                WHERE
                    cases.PatientKey = {0} AND
                    cases.CaseDate BETWEEN "{1}" AND "{2}" AND
                    InsCode = "{3}"
            '''.format(patient_key, start_date, end_date, check_ins_code)
            rows = self.database.select_record(sql)
            if len(rows) <= 0:
                return

            first_date = rows[0]['CaseDate']
            duration = case_date.date() - first_date.date()
            if duration.days >= 105:  # 今年度不可超過105天
                error_message = '* {0}限105日內完成, 上次申報日期為{1}, 請改為一般門診'.format(
                    string_utils.xstr(rows[0]['MedicineName']),
                    rows[0]['CaseDate'].date(),
                )

        return error_message

    # 腦血管疾病檢查 (必須執行針灸或傷科處置)
    def _check_brain(self):
        check_ok = True
        error_message = []

        if self.treatment == '':
            error_message.append('* 未執行針灸或傷科處置')

        error = self._check_disease1_error(self.treat_type, self.disease_code1)
        if error is not None:
            error_message.append(error)

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '腦血管疾病加強照護檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        腦血管疾病加強照護檢查錯誤訊息:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    # 助孕照護檢查 (至少開藥七天)
    def _check_aid_pregnant_care(self):
        check_ok = True
        error_message = []

        error = self._check_disease1_error(self.treat_type, self.disease_code1)
        if error is not None:
            error_message.append(error)

        error = self._check_pres_days_error(self.treat_type, self.pres_days)
        if error is not None:
            error_message.append(error)

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '助孕照護檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        助孕照護檢查錯誤訊息:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    # 保胎照護檢查 (至少開藥七天)
    def _check_keep_baby_care(self):
        check_ok = True
        error_message = []

        error = self._check_pres_days_error(self.treat_type, self.pres_days)
        if error is not None:
            error_message.append(error)

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '保胎照護檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        保胎照護檢查錯誤訊息:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    # 癌症檢查 (至少開藥七天)
    def _check_cancer_care(self):
        check_ok = True
        error_message = []

        error = self._check_disease1_error(self.treat_type, self.disease_code1)
        if error is not None:
            error_message.append(error)

        error = self._check_pres_days_error(self.treat_type, self.pres_days)
        if error is not None:
            error_message.append(error)

        check_ins_code_list = ['P56006', 'P56007']
        for check_ins_code in check_ins_code_list:
            error = self._check_duration_by_ins_code(
                string_utils.xstr(self.patient_record['PatientKey']),
                self.medical_record['CaseDate'],
                self.treat_type,
                check_ins_code,
                self.table_widget_ins_care,
            )
            if error is not None:
                error_message.append(error)

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '癌症照護檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        肝癌、乳癌照護檢查錯誤訊息:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_child_rhinitis(self):
        check_ok = True
        error_message = []

        age_range = [5, 14]  # 5-14兒童
        error = self._check_age_range_error(
            self.treat_type, self.medical_record, self.patient_record, age_range
        )
        if error is not None:
            error_message.append(error)

        error = self._check_disease1_error(self.treat_type, self.disease_code1)
        if error is not None:
            error_message.append(error)

        error = self._check_duration_by_ins_code(
            string_utils.xstr(self.patient_record['PatientKey']),
            self.medical_record['CaseDate'],
            self.treat_type,
            'P58005',
            self.table_widget_ins_care,
        )
        if error is not None:
            error_message.append(error)

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '兒童過敏性鼻炎照護檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        兒童過敏性鼻炎照護檢查錯誤訊息:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_general(self):
        check_ok = self._check_empty_disease()
        if not check_ok:
            return check_ok

        check_ok = self._check_disease_duplicated()
        if not check_ok:
            return check_ok

        check_ok = self._check_disease_neat()
        if not check_ok:
            return check_ok

        check_ok = self._check_disease_self_payment()
        if not check_ok:
            return check_ok

        check_ok = self._check_course_disease()
        if not check_ok:
            return check_ok

        check_ok = self._check_ins_medicine()
        if not check_ok:
            return check_ok

        check_ok = self._check_empty_prescript()
        if not check_ok:
            return check_ok

        check_ok = self._check_empty_treat()
        if not check_ok:
            return check_ok

        check_ok = self._check_injury_treat()
        if not check_ok:
            return check_ok

        check_ok = self._check_dosage()
        if not check_ok:
            return check_ok

        if self.treatment == '複雜針灸':
            check_ok = self._check_complicated_acupuncture()
            if not check_ok:
                return check_ok
        elif self.treatment == '複雜傷科':
            check_ok = self._check_complicated_massage()
            if not check_ok:
                return check_ok

        check_ok = self._check_special_code()
        if not check_ok:
            return check_ok

        check_ok = self._check_pres_days()
        if not check_ok:
            return check_ok

        return check_ok

    def _check_dosage(self):
        check_ok = True
        error_message = []

        row_count = self.table_widget_ins_prescript.rowCount()

        if row_count <= 0:
            return check_ok

        for row_no in range(row_count):
            self.table_widget_ins_prescript.setCurrentCell(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])
            medicine_key = self.table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineKey'])
            if medicine_key is None:
                continue

            medicine_name = self.table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName'])
            dosage = self.table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['Dosage'])

            if dosage is None or dosage.text() == '':
                error_message.append('{0} 無劑量'.format(medicine_name.text()))
                break

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '劑量檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        處方及劑量檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_empty_disease(self):
        check_ok = True
        error_message = []

        if self.disease_code1 == '' and self.disease_code2 == '' and self.disease_code3 == '':
            error_message.append('所有診斷碼均為空白, 請確定是否遺漏輸入.')

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '診斷碼檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        診斷碼檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_course_disease(self):
        check_ok = True
        if number_utils.get_integer(self.medical_record['Continuance']) <= 1:
            return  check_ok

        error_message = []

        case_date = self.medical_record['CaseDate']
        last_treat_date = (case_date - datetime.timedelta(days=30)).strftime('%Y-%m-%d 00:00:00')
        sql = '''
            SELECT 
                Name, CaseDate, Card, Continuance, DiseaseCode1, DiseaseName1 FROM cases 
            WHERE
                (CaseKey != {case_key}) AND
                (PatientKey = {patient_key}) AND
                (CaseDate >= "{last_treat_date}") AND
                (InsType = "健保") AND
                (Card = "{card}") AND
                (Continuance >= 2)
            ORDER BY CaseDate DESC LIMIT 1
        '''.format(
            case_key = self.medical_record['CaseKey'],
            patient_key=self.medical_record['PatientKey'],
            last_treat_date=last_treat_date,
            card=string_utils.xstr(self.medical_record['Card']),
        )
        rows = self.database.select_record(sql)
        if len(rows) <= 0:
            return check_ok

        row = rows[0]
        last_disease_code1 = string_utils.xstr(row['DiseaseCode1'])
        if self.disease_code1 != last_disease_code1:
            error_message.append(
                '''
                    本次療程主診斷碼與上次不同, 請確定是否輸入正確!<br>
                    上次病歷為:<br>
                    <font color="navy">
                    病患姓名: {name}<br>
                    門診日期: {case_date}<br>
                    健保卡序: {card}-{course}<br>
                    主診斷碼: {disease_code1}<br>
                    中文名稱: {disease_name1}
                    </font>
                '''.format(
                    name=string_utils.xstr(row['Name']),
                    case_date=string_utils.xstr(row['CaseDate'].date()),
                    card=string_utils.xstr(row['Card']),
                    course=string_utils.xstr(row['Continuance']),
                    disease_code1=string_utils.xstr(row['DiseaseCode1']),
                    disease_name1=string_utils.xstr(row['DiseaseName1']),
                )
            )

        if len(error_message) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('診斷碼檢查錯誤')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                        診斷碼檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
            )
            msg_box.setInformativeText("請確定上次療程診斷碼與本次是否差異過大.")
            msg_box.addButton(QPushButton("繼續存檔"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            save_file = msg_box.exec_()
            if save_file == QMessageBox.RejectRole:
                check_ok = False

        return check_ok

    def _check_empty_prescript(self):
        check_ok = True
        error_message = []

        medicine_name = self.table_widget_ins_prescript.item(
            0, prescript_utils.INS_PRESCRIPT_COL_NO['MedicineName'])
        treat_name = self.table_widget_ins_treat.item(
            0, prescript_utils.INS_TREAT_COL_NO['MedicineName'])

        if (medicine_name is None and
            self.treatment == '' and treat_name is None):
            error_message.append('所有處方均為空白, 請確定是否遺漏輸入.')

        if len(error_message) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('處方空白')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                        處方檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
            )
            msg_box.setInformativeText("請確定是否為問診或遺漏輸入處方.")
            msg_box.addButton(QPushButton("繼續存檔"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            save_file = msg_box.exec_()
            if save_file == QMessageBox.RejectRole:
                check_ok = False

        return check_ok

    def _check_empty_treat(self):
        check_ok = True
        error_message = []

        treat_exists = False
        for row_no in range(self.table_widget_ins_treat.rowCount()):
            treat_name = self.table_widget_ins_treat.item(
                row_no, prescript_utils.INS_TREAT_COL_NO['MedicineName'])

            if treat_name is not None:
                treat_exists = True
                break

        if self.treatment != '' and not treat_exists:
            error_message.append('有執行針傷處置但無針灸穴道或處置手法, 請確定是否遺漏輸入.')

        if len(error_message) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('處置空白')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                        處置檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
            )
            msg_box.setInformativeText("請確定是否遺漏輸入處置.")
            msg_box.addButton(QPushButton("繼續存檔"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            save_file = msg_box.exec_()
            if save_file == QMessageBox.RejectRole:
                check_ok = False

        return check_ok

    def _check_injury_treat(self):
        check_ok = True
        error_message = []

        if self.medical_record['Share'] == '職業傷害' and self.treatment == '':
            error_message.append('此病歷為職業傷害案件, 但無針灸或傷科處置, 請確定是否遺漏輸入.')

        if len(error_message) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('處置空白')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                        處置檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
            )
            msg_box.setInformativeText("請確定是否遺漏輸入處置.")
            msg_box.addButton(QPushButton("繼續存檔"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            save_file = msg_box.exec_()
            if save_file == QMessageBox.RejectRole:
                check_ok = False

        return check_ok

    def _check_pres_days(self):
        check_ok = True

        if self.pres_days <= 0:  # 沒開藥不用檢查
            return check_ok

        message = registration_utils.check_prescription_finished(
            self.database, self.patient_record['PatientKey'],
            self.medical_record['CaseDate']
        )

        if message is not None:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('用藥重複')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                        用藥檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format(message),
            )
            msg_box.setInformativeText("請注意用藥重複.")
            msg_box.addButton(QPushButton("繼續存檔"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            save_file = msg_box.exec_()
            if save_file == QMessageBox.RejectRole:
                check_ok = False

        return check_ok

    def _check_disease_self_payment(self):
        check_ok = True
        error_message = []

        disease_code_list = [
            self.disease_code1,
            self.disease_code2,
            self.disease_code3,
        ]

        for disease_code in disease_code_list:
            if disease_code == '':
                continue

            if disease_code[:3] in ['E65', 'E66']:
                error_message.append('肥胖症')
            elif disease_code[:3] in ['L67']:
                error_message.append('白髮或髮色異常')
            elif disease_code[:4] in ['L812']:
                error_message.append('雀斑')
            elif disease_code[:3] in ['H49', 'H50']:
                error_message.append('斜視')
            elif disease_code[:4] in ['H521']:
                error_message.append('近視')
            elif disease_code[:4] in ['H522']:
                error_message.append('散光')
            elif disease_code[:4] in ['H524']:
                error_message.append('老花眼')

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '診斷碼檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        診斷碼檢查錯誤如下:<br>
                        <br>
                        {0}為健保中醫門診不給付項目之病名
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_disease_neat(self):
        check_ok = True
        error_message = []

        disease_code_list = [
            self.disease_code1,
            self.disease_code2,
            self.disease_code3,
        ]

        for disease_code in disease_code_list:
            if disease_code == '':
                continue

            if not case_utils.is_disease_code_neat(self.database, disease_code):
                error_message.append('診斷碼 {0} 非最細碼<br>'.format(disease_code))
            elif not case_utils.is_disease_code_exist(self.database, disease_code):
                error_message.append('診斷碼 {0} 無效<br>'.format(disease_code))

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '診斷碼檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        診斷碼檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_disease_duplicated(self):
        check_ok = True
        error_message = []

        disease_code_list = [
            self.disease_code1,
            self.disease_code2,
            self.disease_code3,
        ]

        disease_duplicate = [x for n, x in enumerate(disease_code_list) if x in disease_code_list[:n]]
        if len(disease_duplicate) and ''.join(disease_duplicate) != '':
            error_message.append('診斷碼 {0} 重複輸入<br>'.format(', '.join(disease_duplicate)))

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '診斷碼檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        診斷碼檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_special_code(self):
        check_ok = True
        error_message = []

        if self.treatment != '':  # 有處置不受限制
            return check_ok

        if self.special_code != '' and self.pres_days < 7:
            error_message.append('慢性病開藥至少要七天')
        elif self.special_code == '' and self.pres_days > 7:
            error_message.append('非慢性病開藥不得超過七天')

        if len(error_message) > 0:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle('診斷碼檢查錯誤')
            msg_box.setText(
                '''
                    <font size="4" color="red">
                      <b>
                        診斷碼檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
            )
            msg_box.setInformativeText("請確定慢性病開藥天數是否正確.")
            msg_box.addButton(QPushButton("繼續存檔"), QMessageBox.YesRole)
            msg_box.addButton(QPushButton("取消"), QMessageBox.NoRole)
            save_file = msg_box.exec_()
            if save_file == QMessageBox.RejectRole:
                check_ok = False

        return check_ok

    def _get_complicated_acupuncture_list_thread(self, out_queue, disease):
        complicated_acupuncture_list1 = nhi_utils.get_complicated_acupuncture_list(self.database, disease)

        out_queue.put((complicated_acupuncture_list1,))

    # 取得安全簽章
    def _get_complicated_acupuncture_list(self, disease=1):
        message_box = dialog_utils.message_box(
            '複雜性針灸檢查', '複雜性針灸適應症病名檢查中...', '這樣會花費一些時間, 請稍後',
        )
        message_box.show()

        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()

        t = Thread(target=self._get_complicated_acupuncture_list_thread, args=(msg_queue, disease))
        t.start()
        (complicated_acupuncture_list,) = msg_queue.get()
        message_box.close()

        return complicated_acupuncture_list

    def _check_complicated_acupuncture(self):
        check_ok = True
        error_message = []

        complicated_acupuncture_list1 = self._get_complicated_acupuncture_list(disease=1)

        if self.disease_code1 not in complicated_acupuncture_list1:
            error_message.append('主診斷碼{0}非複雜性針灸適應症'.format(self.disease_code1))

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '複雜性針灸檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        複雜性針灸檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _get_complicated_massage_list_thread(self, out_queue, disease):
        complicated_massage_list1 = nhi_utils.get_complicated_massage_list(self.database, disease)

        out_queue.put((complicated_massage_list1,))

    # 取得安全簽章
    def _get_complicated_massage_list(self, disease=1):
        message_box = dialog_utils.message_box(
            '複雜性傷科檢查', '複雜性傷科適應症病名檢查中...', '這樣會花費一些時間, 請稍後',
        )
        message_box.show()

        msg_queue = Queue()
        QtCore.QCoreApplication.processEvents()

        t = Thread(target=self._get_complicated_massage_list_thread, args=(msg_queue, disease))
        t.start()
        (complicated_massage_list,) = msg_queue.get()
        message_box.close()

        return complicated_massage_list

    def _check_complicated_massage(self):
        check_ok = True
        error_message = []

        complicated_massage_list1 = self._get_complicated_massage_list(disease=1)

        if self.disease_code1 not in complicated_massage_list1:
            error_message.append('主診斷碼{0}非複雜性傷科適應症'.format(self.disease_code1))

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '複雜性傷科檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        複雜性傷科檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

    def _check_ins_medicine(self):
        check_ok = True
        error_message = []

        if self.pres_days <= 0:  # 沒開藥不用檢查
            return check_ok

        ins_medicine = 0
        for row_no in range(self.table_widget_ins_prescript.rowCount()):
            ins_code = self.table_widget_ins_prescript.item(
                row_no, prescript_utils.INS_PRESCRIPT_COL_NO['InsCode'],
            )
            if ins_code is not None and ins_code.text() != '':
                ins_medicine += 1

        if ins_medicine <= 0:
            error_message.append('有健保開藥天數但無健保處方'.format(self.disease_code1))

        if self.packages < 2:
            error_message.append('給藥包數不足2包')

        if self.pres_days < 3:
            error_message.append('給藥天數不足3日')

        if self.instruction in [None, '']:
            error_message.append('服藥方式空白')

        if len(error_message) > 0:
            system_utils.show_message_box(
                QMessageBox.Critical,
                '健保藥品檢查錯誤',
                '''
                    <font size="4" color="red">
                      <b>
                        健保藥品檢查錯誤如下:<br>
                        <br>
                        {0}
                      </b>
                    </font>
                '''.format('<br>'.join(error_message)),
                '請更正上述的錯誤，以利健保申報.'
            )
            check_ok = False

        return check_ok

