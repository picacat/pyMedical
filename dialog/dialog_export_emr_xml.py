#!/usr/bin/env python3
# 病歷查詢 2014.09.22
#coding: utf-8

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox, QPushButton
import datetime
from lxml import etree as ET
import os

from classes import table_widget
from libs import system_utils
from libs import ui_utils
from libs import case_utils
from libs import string_utils
from libs import personnel_utils
from libs import number_utils
from libs import patient_utils
from libs import nhi_utils


# 匯出電子病歷交換檔 xml
class DialogExportEMRXml(QtWidgets.QDialog):
    # 初始化
    def __init__(self, parent=None, *args):
        super(DialogExportEMRXml, self).__init__(parent)
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
        self.ui = ui_utils.load_ui_file(ui_utils.UI_DIALOG_EXPORT_EMR_XML, self)
        system_utils.set_css(self, self.system_settings)
        self.setFixedSize(self.size())  # non resizable dialog
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText('匯出')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).setText('取消')
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.table_widget_medical_record = table_widget.TableWidget(
            self.ui.tableWidget_medical_record, self.database
        )

        self.table_widget_medical_record.set_column_hidden([0])
        self.ui.dateEdit_start_date.setDate(datetime.datetime.now())
        self.ui.dateEdit_end_date.setDate(datetime.datetime.now())

    # 設定信號
    def _set_signal(self):
        self.ui.buttonBox.accepted.connect(self.button_accepted)
        self.ui.buttonBox.rejected.connect(self.button_rejected)
        self.ui.pushButton_read_medical_record.clicked.connect(self._read_medical_record)
        self.ui.toolButton_set_bookmark.clicked.connect(self._set_bookmark)
        self.ui.toolButton_add_bookmark.clicked.connect(self._add_bookmark)
        self.ui.dateEdit_start_date.dateChanged.connect(self._set_date_edit)

    def _set_date_edit(self):
        self.ui.dateEdit_end_date.setDate(self.ui.dateEdit_start_date.date())

    def button_accepted(self):
        self._export_xml_files()

    def button_rejected(self):
        pass

    def _read_medical_record(self):
        start_date = self.ui.dateEdit_start_date.date().toString('yyyy-MM-dd 00:00:00')
        end_date = self.ui.dateEdit_end_date.date().toString('yyyy-MM-dd 23:59:59')
        sql = '''
            SELECT * FROM cases
            WHERE
                CaseDate BETWEEN "{start_date}" AND "{end_date}" AND
                InsType = "健保" AND
                DoctorDone = "True"
            ORDER BY CaseKey
        '''.format(
            start_date=start_date,
            end_date=end_date,
        )

        rows = self.database.select_record(sql)
        if len(rows) > 0:
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.table_widget_medical_record.set_db_data(sql, self._set_table_data)

    def _set_table_data(self, row_no, row):
        if row['InsType'] == '健保':
            medicine_set = 1
        else:
            medicine_set = 2

        case_key = string_utils.xstr(row['CaseKey'])
        pres_days = case_utils.get_pres_days(self.database, case_key, medicine_set)

        full_card = case_utils.get_full_card(row['Card'], row['Continuance'])

        export_date = None
        sql = '''
            SELECT * FROM caseextend
            WHERE
                CaseKey = {0} AND
                ExtendType = "EMRDate"
        '''.format(case_key)
        extend_rows = self.database.select_record(sql)
        if len(extend_rows) > 0:
            export_date = string_utils.xstr(extend_rows[0]['Content'])

        if export_date is None:
            remark = '*'
        else:
            remark = None

        medical_record = [
            string_utils.xstr(row['CaseKey']),
            remark,
            string_utils.xstr(row['CaseDate']),
            string_utils.xstr(row['Period']),
            string_utils.xstr(row['PatientKey']),
            string_utils.xstr(row['Name']),
            string_utils.xstr(row['InsType']),
            string_utils.xstr(row['Share']),
            string_utils.xstr(row['TreatType']),
            full_card,
            string_utils.int_to_str(pres_days),
            string_utils.xstr(row['Doctor']),
            string_utils.xstr(row['DiseaseName1']),
            export_date,
        ]

        for column in range(len(medical_record)):
            self.ui.tableWidget_medical_record.setItem(
                row_no, column,
                QtWidgets.QTableWidgetItem(medical_record[column])
            )
            if column in [4, 11]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
            elif column in [1, 3, 6]:
                self.ui.tableWidget_medical_record.item(
                    row_no, column).setTextAlignment(
                    QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
                )

        self._set_row_color(row_no, 1)

    def _set_row_color(self, row_no, col_no):
        remark = self.ui.tableWidget_medical_record.item(row_no, col_no)

        if remark is not None and remark.text() == '*':
            color = QtGui.QColor('black')
        else:
            color = QtGui.QColor('darkgray')

        for col in range(self.ui.tableWidget_medical_record.columnCount()):
            self.ui.tableWidget_medical_record.item(row_no, col).setForeground(color)

    def _export_xml_files(self):
        xml_file_path = self.system_settings.field('電子病歷交換檔輸出路徑')
        if xml_file_path is None or xml_file_path == '':
            system_utils.show_message_box(
                QMessageBox.Critical,
                '查無電子病歷檔路徑',
                '<font color="red"><h3>系統設定內的「電子病歷檔路徑尚未設定」, 請設定後再執行!</h3></font>',
                '請至系統設定->其他->設定電子病歷檔路徑.'
            )
            return

        row_count = self.ui.tableWidget_medical_record.rowCount()

        progress_dialog = QtWidgets.QProgressDialog(
            '正在產生電子病歷交換檔中, 請稍後...', '取消', 0, row_count, self
        )
        progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        progress_dialog.setValue(0)

        for row_no in range(row_count):
            progress_dialog.setValue(row_no)
            if progress_dialog.wasCanceled():
                break

            self.ui.tableWidget_medical_record.setCurrentCell(row_no, 1)
            case_key = self.table_widget_medical_record.field_value(0)
            case_date = self.table_widget_medical_record.field_value(2)
            remark = self.table_widget_medical_record.field_value(1)
            if remark != '*':
                continue

            self._export_emr_file(xml_file_path, case_key)
            self._set_emr_date(case_key, case_date)

        progress_dialog.setValue(row_count)

        system_utils.show_message_box(
            QMessageBox.Information,
            '匯出完成',
            '<h4>電子病歷交換檔匯出完成 !</h4>',
            '請繼續完成電子病歷簽章作業'
        )

    def _set_emr_date(self, case_key, case_date):
        self.database.exec_sql(
            'DELETE FROM caseextend WHERE CaseKey = {0} AND ExtendType = "EMRDate"'.format(case_key)
        )

        fields = ['CaseKey', 'ExtendType', 'Content']
        data = [
            case_key,
            'EMRDate',
            case_date,
        ]
        self.database.insert_record('caseextend', fields, data)

    def _get_xml_file_name(self, xml_file_path, row):
        doctor_name = string_utils.xstr(row['Doctor'])
        cert_card_no = personnel_utils.get_personnel_field_value(
            self.database, doctor_name, 'CertCardNo')
        doctor_id = personnel_utils.get_personnel_field_value(
            self.database, doctor_name, 'ID')
        patient_key = string_utils.xstr(row['PatientKey'])
        case_date = '{0}{1:0>2}{2:0>2}{3:0>2}{4:0>2}'.format(
            row['CaseDate'].year, row['CaseDate'].month, row['CaseDate'].day,
            row['CaseDate'].hour, row['CaseDate'].minute,
        )
        regist_no = number_utils.get_integer(row['RegistNo'])
        name = string_utils.xstr(row['Name'])

        xml_file_name = '{cert_card_no}-{doctor_id}-{doctor_name}-TW.Foxconn.Clinic.ChineseMedicine.1-60-{patient_key}-{case_date}-{regist_no}-{name}.xml'.format(
            cert_card_no=cert_card_no,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            patient_key=patient_key,
            case_date=case_date,
            regist_no=regist_no,
            name=name,
        )

        return os.path.join(xml_file_path, xml_file_name)

    def _export_emr_file(self, xml_file_path, case_key):
        sql = 'SELECT * FROM cases WHERE CaseKEy = {0}'.format(case_key)
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        row = rows[0]

        xml_file_name = self._get_xml_file_name(xml_file_path, row)
        if xml_file_name is None:
            return

        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        nsmap = {'xsi': xsi}

        attrib = {'{' + xsi + '}noNamespaceSchemaLocation': 'TW.Foxconn.Clinic.ChineseMedicine.1.1.xsd'}
        root = ET.Element('EMR', nsmap=nsmap, attrib=attrib)

        patient_key = string_utils.xstr(row['PatientKey'])
        self._add_document_info(root, row)
        self._add_patient_info(root, row, patient_key)
        self._add_encounter(root, row)
        self._add_drugs(root, row)

        tree = ET.ElementTree(root)
        tree.write(xml_file_name, pretty_print=True, xml_declaration=True, encoding='UTF-8')

    def _add_document_info(self, root, row):
        document_info = ET.SubElement(root, 'DocumentInfo')

        his_doc_pk = ET.SubElement(document_info, 'HISDocPK')
        his_doc_pk.text = string_utils.xstr(row['CaseKey'])

        hospital_id = ET.SubElement(document_info, 'HospitalID')
        hospital_id.text = self.system_settings.field('院所代號')

        hospital_name = ET.SubElement(document_info, 'HospitalName')
        hospital_name.text = self.system_settings.field('院所名稱')

        sheet = ET.SubElement(document_info, 'Sheet')

        id = ET.SubElement(sheet, 'ID')
        id.text = 'TW.Foxconn.Clinic.ChineseMedicine.1'

        name = ET.SubElement(sheet, 'Name')
        name.text = '中醫門診單'

        version = ET.SubElement(sheet, 'Version')
        version.text = '1'

        doc = ET.SubElement(document_info, 'Doc')

        doc_confidentiality_code = ET.SubElement(doc, 'DocConfidentialityCode')
        doc_confidentiality_code.text = 'N'

        now = datetime.datetime.now()
        present = '{0}{1:0>2}{2:0>2}{3:0>2}{4:0>2}{5:0>2}'.format(
            now.year, now.month, now.day,
            now.hour, now.minute, now.second
        )
        create_time = ET.SubElement(doc, 'CreateTime')
        create_time.text = present

    def _add_patient_info(self, root, case_row, patient_key):
        sql = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        row = rows[0]

        patient_info = ET.SubElement(root, 'PatientInfo')

        chart_no = ET.SubElement(patient_info, 'ChartNo')
        chart_no.text = patient_key

        patient_name = ET.SubElement(patient_info, 'PatientName')
        patient_name.text = string_utils.xstr(row['Name'])

        patient_birthday = row['Birthday']
        if patient_birthday is not None:
            birthday = ET.SubElement(patient_info, 'Birthday')
            birthday.text = '{0}{1:0>2}{2:0>2}'.format(
                patient_birthday.year,
                patient_birthday.month,
                patient_birthday.day
            )

        identity = ET.SubElement(patient_info, 'Identity')
        identity.text = string_utils.xstr(case_row['InsType'])

        gender = ET.SubElement(patient_info, 'Gender')
        gender.text = patient_utils.get_gender_code(string_utils.xstr(row['Gender']))

        patient_id = ET.SubElement(patient_info, 'PatientID')
        patient_id.text = string_utils.xstr(row['ID'])

        telephone = string_utils.xstr(row['Telephone'])
        office_phone = string_utils.xstr(row['Officephone'])
        cellphone = string_utils.xstr(row['Cellphone'])

        if telephone != '' or office_phone != '' or cellphone != '':
            tel = ET.SubElement(patient_info, 'TEL')
            if telephone != '':
                home = ET.SubElement(tel, 'Home')
                home.text = telephone

            if office_phone != '':
                office = ET.SubElement(tel, 'Office')
                office.text = office_phone

            if cellphone != '':
                mobile = ET.SubElement(tel, 'Mobile')
                mobile.text = cellphone

        marriage = ET.SubElement(patient_info, 'MarriageStatus')
        marriage.text = patient_utils.get_marriage_code(string_utils.xstr(row['Marriage']))

        patient_occupation = string_utils.xstr(row['Occupation'])
        if patient_occupation != '':
            occupation = ET.SubElement(patient_info, 'Occupation')
            occupation.text = patient_occupation

        patient_address = string_utils.xstr(row['Address'])
        if patient_address != '':
            address = ET.SubElement(patient_info, 'Address')
            contact = ET.SubElement(address, 'Contact')

            zip = patient_utils.get_zip_code(self.database, patient_address)

            zip_code = ET.SubElement(contact, 'ZipCode')
            zip_code.text = zip

            location = ET.SubElement(contact, 'Location')
            location.text = patient_address

        patient_email = string_utils.xstr(row['Email'])
        if patient_email != '':
            email = ET.SubElement(patient_info, 'Email')
            email.text = patient_email

        patient_history = string_utils.get_str(row['History'], 'utf-8')
        if patient_history != '':
            history = ET.SubElement(patient_info, 'History')
            history.text = patient_history

        patient_allergy = string_utils.get_str(row['Allergy'], 'utf-8')
        if patient_allergy != '':
            allergy = ET.SubElement(patient_info, 'Allergy')
            allergy.text = patient_allergy

        patient_init_date =  row['InitDate']
        if patient_init_date is not None:
            first_visit_date = ET.SubElement(patient_info, 'FirstVisitDate')
            first_visit_date.text = '{0}{1:0>2}{2:0>2}'.format(
                patient_init_date.year,
                patient_init_date.month,
                patient_init_date.day
            )

        patient_education = string_utils.xstr(row['Education'])
        if patient_education != '':
            education = ET.SubElement(patient_info, 'Education')
            education.text = patient_education

    def _add_encounter(self, root, row):
        encounter = ET.SubElement(root, 'Encounter')

        self._add_registration_data(encounter, row)
        self._add_diagnosis_data(encounter, row)
        self._add_disease_data(encounter, row)
        self._add_major_injuries(encounter, row)
        self._add_treatment(encounter, row)

    def _add_registration_data(self, encounter, row):
        case_date = row['CaseDate']
        visit_date = ET.SubElement(encounter, 'VisitDate')
        visit_date.text = '{0}{1:0>2}{2:0>2}{3:0>2}{4:0>2}'.format(
            case_date.year,
            case_date.month,
            case_date.day,
            case_date.hour,
            case_date.minute,
        )

        visit_seq = ET.SubElement(encounter, 'VisitSeq')
        visit_seq.text = string_utils.xstr(number_utils.get_integer(row['RegistNo']))

        department = ET.SubElement(encounter, 'Department')
        department.text = '60'

        doc_name = string_utils.xstr(row['Doctor'])
        if doc_name != '':
            doc_id = personnel_utils.get_personnel_field_value(self.database, doc_name, 'ID')
            doctor_id = ET.SubElement(encounter, 'DoctorID')
            doctor_id.text = doc_id

            doctor_name = ET.SubElement(encounter, 'DoctorName')
            doctor_name.text = doc_name

    def _add_diagnosis_data(self, encounter, row):
        symptom = string_utils.get_str(row['Symptom'], 'utf-8')

        if symptom is not None and symptom != '':
            chief_complain = ET.SubElement(encounter, 'ChiefComplain')
            try:
                chief_complain.text = symptom
            except ValueError:
                symptom = string_utils.remove_control_characters(symptom)
                chief_complain.text = symptom

        tongue = string_utils.get_str(row['Tongue'], 'utf-8')
        if tongue is not None and tongue != '':
            tongue_condition = ET.SubElement(encounter, 'TongueCondition')
            try:
                tongue_condition.text = tongue
            except ValueError:
                tongue = string_utils.remove_control_characters(tongue)
                tongue_condition.text = tongue

        pulse = string_utils.get_str(row['Pulse'], 'utf-8')
        if pulse is not None and pulse != '':
            pulse_condition = ET.SubElement(encounter, 'PulseCondition')
            try:
                pulse_condition.text = pulse
            except ValueError:
                pulse = string_utils.remove_control_characters(pulse)
                pulse_condition.text = pulse

        distinct = string_utils.get_str(row['Distincts'], 'utf-8')
        if distinct is not None and distinct != '':
            manifestation = ET.SubElement(encounter, 'Manifestation')
            try:
                manifestation.text = distinct
            except ValueError:
                distinct = string_utils.remove_control_characters(distinct)
                manifestation.text = distinct

        cure = string_utils.get_str(row['Cure'], 'utf-8')
        if cure is not None and cure != '':
            therapeutic_discipline = ET.SubElement(encounter, 'TherapeuticDiscipline')
            try:
                therapeutic_discipline.text = cure
            except ValueError:
                cure = string_utils.remove_control_characters(cure)
                therapeutic_discipline.text = cure

    def _add_disease_data(self, encounter, row):
        for i in range(1, 4):
            code_field = 'DiseaseCode{0}'.format(i)
            disease_code = string_utils.xstr(row[code_field])
            if disease_code == '':
                continue

            name_field = 'DiseaseName{0}'.format(i)
            disease_name = string_utils.xstr(row[name_field])

            diagnosis = ET.SubElement(encounter, 'Diagnosis')
            code = ET.SubElement(diagnosis, 'Code')
            code.text = disease_code
            name = ET.SubElement(diagnosis, 'Name')
            name.text = disease_name

    def _add_major_injuries(self, encounter, row):
        major_injuries = ET.SubElement(encounter, 'MajorInjuries')

        major_injury_flag = ET.SubElement(major_injuries, 'MajorInjuryFlag')
        if string_utils.xstr(row['SpecialCode']) != '':
            major_injury_flag.text = '是'

            major_injury_code = ET.SubElement(major_injuries, 'MajorInjuryCode')
            major_injury_code.text = string_utils.xstr(row['DiseaseCode1'])

            major_injury_name = ET.SubElement(major_injuries, 'MajorInjuryName')
            major_injury_name.text = string_utils.xstr(row['DiseaseName1'])
        else:
            major_injury_flag.text = '否'

    def _add_treatment(self, encounter, row):
        medical_record_treatment = string_utils.xstr(row['Treatment'])
        if medical_record_treatment == '':
            return

        treatment = ET.SubElement(encounter, 'Treatment')

        treatment_nhi_code = ET.SubElement(treatment, 'TreatmentNHICode')
        treatment_nhi_code.text = nhi_utils.TREAT_DICT[medical_record_treatment]

        treatment_description = ET.SubElement(treatment, 'TreatmentDescription')
        treatment_description.text = medical_record_treatment

        self._add_treatment_prescript(treatment, medical_record_treatment, row)

    def _add_treatment_prescript(self, treatment, medical_record_treatment, row):
        case_key = string_utils.xstr(row['CaseKey'])
        medicine_type = '處置'
        treatment_region = None

        if medical_record_treatment in nhi_utils.ACUPUNCTURE_TREAT:
            medicine_type = '穴道'
            treatment_region_field = 'AcupunctureRegion'
            treatment_region = ET.SubElement(treatment, treatment_region_field)
        elif medical_record_treatment in nhi_utils.MASSAGE_TREAT:
            treatment_region_field = 'ContusionRegion'
        elif medical_record_treatment in nhi_utils.DISLOCATE_DICT:
            treatment_region_field = 'DislocateRegion'
        else:
            return

        sql = '''
            SELECT * FROM prescript
            WHERE
                MedicineSet = 1 AND
                CaseKey = {0} AND
                MedicineType = "{1}" AND
                MedicineName IS NOT NULL AND
                LENGTH(MedicineName) > 0
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(
            case_key,
            medicine_type,
        )
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        if medical_record_treatment in nhi_utils.ACUPUNCTURE_TREAT:
            node_name = 'AcupunctureRegionNHICode'
            treatment_nhi_code = ET.SubElement(treatment_region, node_name)
            treatment_nhi_code.text = '9'

        electric_acupuncture = ''
        for prescript_row in rows:
            medicine_name = string_utils.xstr(prescript_row['MedicineName']).replace(' ', '')
            if '波形' in medicine_name or '頻率' in medicine_name or '時間' in medicine_name:  # 電針處置暫不處理
                if electric_acupuncture == '':
                    electric_acupuncture += medicine_name
                else:
                    electric_acupuncture += ',' + medicine_name

                continue

            if medical_record_treatment in nhi_utils.ACUPUNCTURE_TREAT:
                point = ET.SubElement(treatment_region, 'Point')
                point_name = ET.SubElement(point, 'PointName')
                point_name.text = medicine_name

                if medical_record_treatment == '電針治療':
                    point_comment = ET.SubElement(point, 'PointComment')
                    point_comment.text = electric_acupuncture
            else:
                treatment_region = ET.SubElement(treatment, treatment_region_field)

                treatment_nhi_code = ET.SubElement(treatment_region, 'ContusionRegionNHICode')
                treatment_nhi_code.text = '9'

                contusion_technique = ET.SubElement(treatment_region, 'ContusionTechnique')
                contusion_technique.text = medicine_name

    def _add_drugs(self, root, row):
        case_key = string_utils.xstr(row['CaseKey'])

        sql = '''
            SELECT * FROM prescript
            WHERE
                MedicineSet = 1 AND
                CaseKey = {0} AND
                MedicineType IN ("單方", "複方", "水藥", "外用", "高貴", "成方") AND
                MedicineName IS NOT NULL AND
                LENGTH(MedicineName) > 0
            ORDER BY PrescriptNo, PrescriptKey
        '''.format(case_key)
        rows = self.database.select_record(sql)

        if len(rows) <= 0:
            return

        pres_days = case_utils.get_pres_days(self.database, row['CaseKey'])
        packages = case_utils.get_packages(self.database, case_key)
        instruction = case_utils.get_instruction(self.database, case_key)

        drugs = ET.SubElement(root, 'Drugs')

        for prescript_row in rows:
            drug = ET.SubElement(drugs, 'Drug')

            ins_code = string_utils.xstr(prescript_row['InsCode'])
            if ins_code != '':
                drug_nhi_code = ET.SubElement(drug, 'DrugNHICode')
                drug_nhi_code.text = ins_code

            medicine_key = string_utils.xstr(prescript_row['MedicineKey'])
            if medicine_key == '':
                medicine_code = 'NA'
            else:
                medicine_code = self._get_drug_code(medicine_key)

            drug_code = ET.SubElement(drug, 'DrugCode')
            drug_code.text = medicine_code

            drug_name = ET.SubElement(drug, 'DrugName')
            drug_name.text = string_utils.xstr(prescript_row['MedicineName'])

            try:
                dose = ET.SubElement(drug, 'Dose')
                dose.text = '{0:01.2f}'.format(prescript_row['Dosage'] / packages)     # 用量
            except TypeError:
                pass

            unit = string_utils.xstr(prescript_row['Unit'])
            if unit == '':
                unit = '克'

            dose_unit = ET.SubElement(drug, 'DoseUnit')
            dose_unit.text = unit

            start_date = row['CaseDate']
            end_date = start_date + datetime.timedelta(days=90)

            drug_start_date = ET.SubElement(drug, 'DrugStartDate')
            drug_start_date.text = '{0}{1:0>2}{2:0>2}'.format(
                start_date.year, start_date.month, start_date.day,
            )
            drug_end_date = ET.SubElement(drug, 'DrugEndDate')
            drug_end_date.text = '{0}{1:0>2}{2:0>2}'.format(
                end_date.year, end_date.month, end_date.day,
            )

            try:
                total_amount = ET.SubElement(drug, 'TotalAmount')
                total_amount.text = '{0:01.2f}'.format(prescript_row['Dosage'] * pres_days)     # 用量
            except TypeError:
                pass

            package_number = ET.SubElement(drug, 'PackageNumber')
            package_number.text = string_utils.xstr(packages)

            days = ET.SubElement(drug, 'Days')
            days.text = string_utils.xstr(pres_days)

            frequency = ET.SubElement(drug, 'Frequency')
            frequency.text = self._get_frequency(packages, instruction)

            prescription_method = ET.SubElement(drug, 'PrescriptionMethod')
            prescription_method.text = self._get_prescript_method(
                string_utils.xstr(prescript_row)
            )

    def _get_drug_code(self, medicine_key):
        drug_code = 'NA'

        rows = self.database.select_record('SELECT * FROM medicine WHERE MedicineKey = {0}'.format(medicine_key))
        if len(rows) > 0:
            drug_code = string_utils.xstr(rows[0]['MedicineCode'])

        return drug_code

    def _get_frequency(self, packages, instruction):
        try:
            frequency = nhi_utils.FREQUENCY[packages]
        except:
            frequency = 'TID'

        try:
            usage = nhi_utils.USAGE[instruction]
        except:
            usage = 'PC'

        return '{0},{1}'.format(frequency, usage)

    def _get_prescript_method(self, medicine_type):
        prescript_method = '磨粉'

        if medicine_type in ['單方', '複方']:
            prescript_method = '磨粉'
        elif medicine_type in ['水藥']:
            prescript_method = '先煎'
        elif medicine_type in ['外用']:
            prescript_method = '外敷'

        return prescript_method

    def _set_bookmark(self):
        for row_no in range(self.ui.tableWidget_medical_record.rowCount()):
            self._set_bookmark_field(row_no, 1)

    def _add_bookmark(self):
        row_no = self.ui.tableWidget_medical_record.currentRow()
        self._set_bookmark_field(row_no, 1)

    def _set_bookmark_field(self, row_no, col_no):
        bookmark = self.ui.tableWidget_medical_record.item(row_no, col_no)
        if bookmark is not None and bookmark.text() == '*':
            bookmark = ''
        else:
            bookmark = '*'

        self.ui.tableWidget_medical_record.setItem(
            row_no, col_no, QtWidgets.QTableWidgetItem(bookmark)
        )
        self.ui.tableWidget_medical_record.item(
            row_no, col_no).setTextAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter
        )
        self._set_row_color(row_no, col_no)
