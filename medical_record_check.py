#!/usr/bin/env python3
#coding: utf-8


from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox

from libs import string_utils
from libs import system_utils
from libs import date_utils


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
        self.treatment = args[6]
        self.pres_days = args[7]
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
        check_ok = True

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

