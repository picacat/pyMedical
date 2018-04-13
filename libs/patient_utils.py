from dialog import dialog_patient


# 尋找病患資料
def search_patient(ui, database, settings, keyword):
    if keyword.isnumeric():
        if len(keyword) >= 7:
            script = 'SELECT * FROM patient WHERE Telephone like "%{0}%" or Cellphone like "%{0}%"'.format(keyword)
        else:
            script = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(keyword)
    else:
        script = ('SELECT * FROM patient WHERE '
                  '(Name like "%{0}%") or '
                  '(ID like "{0}%") or '
                  '(Birthday = "{0}")').format(keyword)

    script += ' ORDER BY PatientKey'
    row = database.select_record(script)
    row_count = len(list(row))

    if row_count <= 0:
        return None
    elif row_count >= 2:
        dialog = dialog_patient.DialogPatient(ui, database, settings, row)
        dialog.exec_()
        patient_key = dialog.get_patient_key()
        if patient_key is None:  # 取消查詢
            return -1

        script = 'SELECT * FROM patient WHERE PatientKey = {0}'.format(patient_key)
        row = database.select_record(script)

    return row

