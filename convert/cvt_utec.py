
from PyQt5.QtWidgets import QMessageBox, QPushButton
from libs import string_utils
from convert import cvt_groups


# 友杏轉檔 2018.05.09
class CvtUtec():
    def __init__(self, parent, *args):
        self.parent = parent
        self.product_type = parent.ui.comboBox_utec_product.currentText()
        self.database = parent.database
        self.source_db = parent.source_db
        self.progress_bar = parent.ui.progressBar

    # 開始轉檔
    def convert(self):
        if self.parent.ui.label_connection_status.text() == '未連線':
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle('尚未開啟連線')
            msg_box.setText("<font size='4' color='Red'><b>尚未執行連線測試, 請執行連線測試後再執行轉檔作業.</b></font>")
            msg_box.setInformativeText("連線尚未開啟, 無法執行轉檔作業.")
            msg_box.addButton(QPushButton("確定"), QMessageBox.YesRole)
            msg_box.exec_()
            return

        if self.product_type == 'Med2000':
            self._convert_med2000()
        else:
            self._convert_medical()

        if self.parent.ui.checkBox_address_list.isChecked():
            self._cvt_address_list()
        if self.parent.ui.checkBox_certificate.isChecked():
            self._cvt_certificate()

    def _convert_med2000(self):
        if self.parent.ui.checkBox_groups.isChecked():
            self._cvt_groups()
        if self.parent.ui.checkBox_dosage.isChecked():
            self._cvt_med2000_dosage()
        if self.parent.ui.checkBox_medical_record.isChecked():
            self._cvt_med2000_cases()

    def _convert_medical(self):
        if self.parent.ui.checkBox_groups.isChecked():
            self._cvt_groups()
        if self.parent.ui.checkBox_disease_treat.isChecked():
            self._cvt_disease_treat()
        if self.parent.ui.checkBox_dosage.isChecked():
            self._cvt_medical_dosage()
        if self.parent.ui.checkBox_patient.isChecked():
            self._cvt_medical_patient()
        if self.parent.ui.checkBox_reserve.isChecked():
            self._cvt_medical_reserve()
        if self.parent.ui.checkBox_medical_record.isChecked():
            self._cvt_medical_cases()
            self._cvt_med2000_cases()

    def _cvt_groups(self):
        self.parent.ui.label_progress.setText('詞庫類別轉檔')
        cvt_groups.cvt_pymedical_groups(self.database)
        cvt_groups.cvt_groups_name(self.database, self.source_db, self.product_type, self.progress_bar)
        cvt_groups.cvt_tongue_groups(self.database, self.source_db, self.progress_bar)
        cvt_groups.cvt_pulse_groups(self.source_db)
        cvt_groups.cvt_remark_groups(self.source_db)
        cvt_groups.cvt_pymedical_disease_groups(self.database)
        cvt_groups.cvt_pymedical_other_groups(self.source_db)

    def _cvt_med2000_dosage(self):
        sql = 'TRUNCATE dosage'
        self.database.exec_sql(sql)

        sql = '''
            SELECT CaseKey,
                Package1, Package2, Package3, Package4, Package5, Package6,
                PresDays1, PresDays2, PresDays3, PresDays4, PresDays5, PresDays6,
                Instruction1, Instruction2, Instruction3, Instruction4, Instruction5, Instruction6
             FROM cases ORDER BY CaseKey
        '''
        rows = self.source_db.select_record(sql)
        self.progress_bar.setMaximum(len(rows))
        self.progress_bar.setValue(0)
        fields = ['CaseKey', 'MedicineSet', 'Packages', 'Days', 'Instruction']
        for row in rows:
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            for i in range(1, 7):
                if row['Package{0}'.format(i)] is not None or row['PresDays{0}'.format(i)] is not None:
                    data = [
                        row['CaseKey'],
                        i,
                        row['Package{0}'.format(i)],
                        row['PresDays{0}'.format(i)],
                        row['Instruction{0}'.format(i)]
                    ]
                    self.database.insert_record('dosage', fields, data)

    def _cvt_med2000_cases(self):
        self.parent.ui.label_progress.setText('Med2000病歷檔轉檔')
        self.progress_bar.setMaximum(10)
        self.progress_bar.setValue(0)

        sql = 'UPDATE cases SET PharmacyType = "不申報" WHERE ApplyType = "調劑不報"'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET PharmacyType = "申報" WHERE PharmacyType IS NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET ApplyType = "申報" WHERE ApplyType != "不申報"'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "內科" WHERE TreatType = "一般"'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "針灸治療" WHERE TreatType IN ("針灸", "針藥", "針灸給藥")'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "電針治療" WHERE TreatType IN ("電針", "電藥", "電針給藥")'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "複雜針灸" WHERE TreatType IN ("複針", "複針給藥")'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "傷科治療" WHERE TreatType IN ("傷科", "傷藥", "傷科給藥")'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "複雜傷科" WHERE TreatType IN ("複傷", "複傷給藥")'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = "脫臼整復" WHERE TreatType IN ("脫臼", "脫藥", "脫臼給藥")'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _cvt_medical_patient(self):
        self.parent.ui.label_progress.setText('病患基本資料檔轉檔')
        self.progress_bar.setMaximum(4)
        self.progress_bar.setValue(0)

        sql = 'UPDATE patient SET Gender = Sex WHERE Sex IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE patient SET Allergy = Alergy WHERE Alergy IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE patient SET Nationality = "本國" WHERE SUBSTRING(ID, 2, 1) IN ("1", "2") AND Nationality IS NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE patient SET Nationality = "外國" WHERE SUBSTRING(ID, 2, 1) NOT IN ("1", "2") AND Nationality IS NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _cvt_medical_cases(self):
        self.parent.ui.label_progress.setText('Medical病歷檔轉檔')
        self.progress_bar.setMaximum(7)
        self.progress_bar.setValue(0)

        sql = 'UPDATE cases SET SDiagShareFee = ReceiptShare WHERE ReceiptShare IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET Cashier = Casher WHERE Casher IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET DiagShareFee = TreatShare WHERE TreatShare IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET DrugShareFee = DrugShare WHERE DrugShare IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET RefundFee = Refund WHERE Refund IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET SMaterialFee = SMaterial WHERE SMaterial IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

        sql = 'UPDATE cases SET TreatType = RegistType WHERE RegistType IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _cvt_medical_dosage(self):
        self.parent.ui.label_progress.setText('處方用藥轉檔')
        sql = 'TRUNCATE dosage'
        self.database.exec_sql(sql)

        self._cvt_medical_dosage_by_cases()
        self._cvt_medical_dosage_by_caseextend()

    def _cvt_medical_dosage_by_cases(self):
        sql = '''
            SELECT 
                CaseKey,
                Package1, Package2, Package3,
                PresDays1, PresDays2, PresDays3,
                Instruction1, Instruction2, Instruction3
             FROM cases 
             ORDER BY CaseKey 
        '''

        rows = self.source_db.select_record(sql)

        self.progress_bar.setMaximum(len(rows))
        self.progress_bar.setValue(0)
        fields = ['CaseKey', 'MedicineSet', 'Packages', 'Days', 'Instruction']
        for row in rows:
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            for i in range(1, 4):
                if row['Package{0}'.format(i)] is not None or row['PresDays{0}'.format(i)] is not None:
                    data = [
                        row['CaseKey'],
                        i,
                        row['Package{0}'.format(i)],
                        row['PresDays{0}'.format(i)],
                        row['Instruction{0}'.format(i)]
                    ]
                    self.database.insert_record('dosage', fields, data)

    def _cvt_medical_dosage_by_caseextend(self):
        sql = '''
            SELECT *
             FROM caseextend
             WHERE
                ExtendType IN ("藥日4", "藥日5", "藥日6", "藥包4", "藥包5", "藥包6", "指示4", "指示5", "指示6") AND
                (Content IS NOT NULL AND LENGTH(Content) > 0) AND
                Content NOT LIKE "ComboBox%"
             ORDER BY CaseKey 
        '''

        rows = self.source_db.select_record(sql)
        if len(rows) <= 0:
            return

        self.progress_bar.setMaximum(len(rows))
        self.progress_bar.setValue(0)
        for row in rows:
            self.progress_bar.setValue(self.progress_bar.value() + 1)

            if string_utils.xstr(row['ExtendType'])[:2] == '藥日':
                field = 'Days'
            elif string_utils.xstr(row['ExtendType'])[:2] == '藥包':
                field = 'Packages'
            elif string_utils.xstr(row['ExtendType'])[:2] == '指示':
                field = 'Instruction'
            else:
                continue

            medicine_set = string_utils.xstr(row['ExtendType'])[2]

            sql = '''
                SELECT * FROM dosage
                WHERE
                    CaseKey = {0} AND
                    MedicineSet = {1}
            '''.format(
                row['CaseKey'], medicine_set,
            )
            dosage_rows = self.database.select_record(sql)
            value = string_utils.xstr(row['Content'])
            if field in ['Days', 'Packages'] and not value.isdigit():
                value = 0

            if len(dosage_rows) > 0:
                self.database.exec_sql(
                    'UPDATE dosage SET {0} = "{1}" WHERE DosageKey = {2}'.format(
                        field, value, dosage_rows[0]['DosageKey'],
                    )
                )
            else:
                fields = ['CaseKey', 'MedicineSet', field]
                data = [
                    row['CaseKey'], medicine_set, value,
                ]
                self.database.insert_record('dosage', fields, data)

    def _cvt_medical_reserve(self):
        self.parent.ui.label_progress.setText('預約掛號檔轉檔')
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)

        sql = 'UPDATE reserve SET ReserveNo = Sequence WHERE Sequence IS NOT NULL'
        self.database.exec_sql(sql)
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _cvt_address_list(self):
        self.parent.ui.label_progress.setText('地址郵遞區號轉檔')
        self.progress_bar.setMaximum(61034)
        self.progress_bar.setValue(0)

        self.database.exec_sql('truncate address_list')

        fields = ['ZipCode', 'City', 'District', 'Street', 'MailRange']
        import csv
        f = open('zip_code.csv', 'r', encoding='utf8')
        for row in csv.DictReader(f):
            try:
                data = [row['郵遞區號'], row['縣市名稱'], row['鄉鎮市區'], row['原始路名'], row['投遞範圍']]
                self.database.insert_record('address_list', fields, data)
            except:
                pass

            self.progress_bar.setValue(self.progress_bar.value() + 1)

    def _cvt_certificate(self):
        rows = self.database.select_record('SELECT * FROM proof ORDER BY ProofKey')
        row_count = len(rows)

        self.parent.ui.label_progress.setText('診斷及收費證明轉檔')
        self.progress_bar.setMaximum(row_count)
        self.progress_bar.setValue(0)

        self.database.exec_sql('truncate certificate')

        fields = [
            'CertificateKey', 'CaseKey', 'PatientKey', 'Name', 'CertificateDate', 'CertificateType',
            'InsType', 'StartDate', 'EndDate', 'Diagnosis', 'DoctorComment',

        ]
        for row in rows:
            self.progress_bar.setValue(self.progress_bar.value() + 1)
            data = [
                row['ProofKey'],
                0,
                row['PatientKey'],
                row['Name'],
                row['ProofDate'],
                row['ProofType'],
                row['InsType'],
                row['StartDate'],
                row['StopDate'],
                row['Disease'],
                row['Diagnosis'],
            ]

            self.database.insert_record('certificate', fields, data)

    def _cvt_disease_treat(self):
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.parent.ui.label_progress.setText('病名詞庫傷骨科類別轉檔')
        cvt_groups.cvt_disease_treat(self.database)
        self.progress_bar.setValue(100)
