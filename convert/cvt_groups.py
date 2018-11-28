

def cvt_pymedical_groups(database):
    fields = [
        'DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName'
    ]

    sql = 'TRUNCATE dict_groups'
    database.exec_sql(sql)

    data = ['主訴類別', None, '內科']
    database.insert_record('dict_groups', fields, data)
    data = ['主訴類別', None, '婦科']
    database.insert_record('dict_groups', fields, data)
    data = ['主訴類別', None, '兒科']
    database.insert_record('dict_groups', fields, data)
    data = ['主訴類別', None, '傷骨科']
    database.insert_record('dict_groups', fields, data)
    data = ['舌診類別', None, '舌質']
    database.insert_record('dict_groups', fields, data)
    data = ['舌診類別', None, '舌苔']
    database.insert_record('dict_groups', fields, data)
    data = ['舌診類別', None, '其他']
    database.insert_record('dict_groups', fields, data)
    data = ['脈象類別', None, '一般']
    database.insert_record('dict_groups', fields, data)
    data = ['脈象', '一般', '一般']
    database.insert_record('dict_groups', fields, data)
    data = ['備註類別', None, '一般']
    database.insert_record('dict_groups', fields, data)
    data = ['備註', '一般', '一般']
    database.insert_record('dict_groups', fields, data)
    data = ['辨證類別', None, '內科']
    database.insert_record('dict_groups', fields, data)
    data = ['辨證類別', None, '傷骨科']
    database.insert_record('dict_groups', fields, data)
    data = ['治則類別', None, '內科']
    database.insert_record('dict_groups', fields, data)
    data = ['治則類別', None, '傷骨科']
    database.insert_record('dict_groups', fields, data)

    data = ['藥品類別', None, '單方']
    database.insert_record('dict_groups', fields, data)
    data = ['藥品類別', None, '複方']
    database.insert_record('dict_groups', fields, data)
    data = ['藥品類別', None, '水藥 ']
    database.insert_record('dict_groups', fields, data)
    data = ['藥品類別', None, '外用']
    database.insert_record('dict_groups', fields, data)
    data = ['藥品類別', None, '高貴']
    database.insert_record('dict_groups', fields, data)
    data = ['處置類別', None, '穴道']
    database.insert_record('dict_groups', fields, data)
    data = ['處置類別', None, '處置']
    database.insert_record('dict_groups', fields, data)
    data = ['處置類別', None, '照護']
    database.insert_record('dict_groups', fields, data)
    data = ['處置類別', None, '檢驗']
    database.insert_record('dict_groups', fields, data)
    data = ['成方類別', None, '成方']
    database.insert_record('dict_groups', fields, data)

def cvt_groups_name(database, source_db, product_type, progress_bar):
    fields = [
        'DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName'
    ]

    if product_type == 'Med2000':
        group_file = 'clinicgroups'
    else:
        group_file = 'groups'

    sql = 'SELECT * FROM {0} ORDER BY GroupsType, GroupsName'.format(group_file)
    rows = source_db.select_record(sql)
    progress_bar.setMaximum(len(rows))
    progress_bar.setValue(0)
    for row in rows:
        progress_bar.setValue(progress_bar.value() + 1)

        if row['GroupsType'] in ['內科', '婦科', '傷科']:
            dict_groups_type = '主訴'
        elif row['GroupsType'] in ['內辨', '傷辨']:
            dict_groups_type = '辨證'
        elif row['GroupsType'] in ['內治', '傷治']:
            dict_groups_type = '治則'
        else:
            continue

        if dict_groups_type == '主訴':
            dict_groups_top_level = row['GroupsType']
            if dict_groups_top_level == '傷科':
                dict_groups_top_level = '傷骨科'
        elif row['GroupsType'] in ['內辨', '內治']:
            dict_groups_top_level = '內科'
        elif row['GroupsType'] in ['傷辨', '傷治']:
            dict_groups_top_level = '傷骨科'
        else:
            dict_groups_top_level = None

        dict_groups_name = row['GroupsName']

        data = [
            dict_groups_type,
            dict_groups_top_level,
            dict_groups_name
        ]
        database.insert_record('dict_groups', fields, data)

def cvt_tongue_groups(database, source_db, progress_bar):
    fields = [
        'DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName'
    ]

    sql = 'SELECT * FROM clinic WHERE ClinicType = "舌診" GROUP BY Groups ORDER BY Groups'
    rows = source_db.select_record(sql)

    progress_bar.setValue(0)
    progress_bar.setMaximum(len(rows))
    for row in rows:
        progress_bar.setValue(progress_bar.value() + 1)

        if row['Groups'] is None:
            continue

        dict_groups_type = '舌診'
        dict_groups_name = str(row['Groups'])

        if dict_groups_name.find('舌') > 0:
            dict_groups_top_level = '舌質'
        elif dict_groups_name.find('苔') > 0:
            dict_groups_top_level = '舌苔'
        else:
            dict_groups_top_level = '其他'

        data = [
            dict_groups_type,
            dict_groups_top_level,
            dict_groups_name
        ]
        database.insert_record('dict_groups', fields, data)

def cvt_pulse_groups(source_db):
    sql = 'UPDATE clinic SET groups = "一般" WHERE ClinicType = "脈象"'
    source_db.exec_sql(sql)

def cvt_remark_groups(source_db):
    sql = 'UPDATE clinic SET groups = "一般" WHERE ClinicType = "備註"'
    source_db.exec_sql(sql)

def cvt_pymedical_disease_groups(database):
    fields = [
        'DictGroupsType', 'DictGroupsTopLevel', 'DictGroupsName'
    ]

    data = ['病名類別', None, '01感染症和寄生蟲']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A08病毒及其他特定腸道感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A09感染性胃腸炎及大腸炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A36白喉']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A37百日咳']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A38猩紅熱']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A40敗血症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A46丹毒']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A50梅毒']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A54淋病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A56披衣菌感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A59滴蟲病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A60疱疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'A71砂眼']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B00疱疹病毒性感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B01水痘']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B02帶狀疱疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B05麻疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B07病毒性疣']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B15病毒性肝炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B20人類免疫不全病毒疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B26腮腺炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B35皮癬']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B36表淺性黴菌病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B37念珠菌病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B85蝨病及陰蝨']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '01感染症和寄生蟲', 'B86疥瘡']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '02腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C00唇,舌,口惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C11鼻,咽,食道惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C16胃,腸惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C21肛門及肛(門)管惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C22肝,膽,胰臟惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C33呼吸系統惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C38心臟惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C40肢體骨關節惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C43惡性黑色素瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C44皮膚惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C46肉瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C47神經系統惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C50乳房惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C51女性生殖器官惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C60男性生殖器官惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C64泌尿器官惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C71腦部惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C73內分泌腺體惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C77其他惡性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'C91白血病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D00原位癌']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D10口及咽部之良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D12結腸,直腸,肛門之良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D13消化系統之良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D15胸腔器官之良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D16骨骼及關節軟骨之良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D17良性脂肪瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D18血管瘤及淋巴管瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D21結締組織之良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D22黑色素細胞痣']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D23皮膚良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D24乳房良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D25女性生殖器官良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D29男性生殖器官良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D30泌尿器官良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D35內分泌腺體良性腫瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '02腫瘤', 'D36其他良性腫瘤']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '03血液和造血器官']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '03血液和造血器官', 'D50貧血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '03血液和造血器官', 'D69紫斑症及其他出血性病態']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '03血液和造血器官', 'D70白血球疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '03血液和造血器官', 'D73脾臟疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '03血液和造血器官', 'D75其他血液與造血器官疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '03血液和造血器官', 'D81複合性免疫缺乏症']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '04內分泌,營養和代謝']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E00甲狀腺疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E08起因於潛在病的糖尿病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E09藥物或化學物導致之糖尿病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E10第1型糖尿病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E11第2型糖尿病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E16低血糖']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E20副甲狀腺低下症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E22腦下腺功能亢進']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E23腦下腺功能低下']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E25腎上腺性生殖疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E26高醛固酮症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E27其他腎上腺疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E28卵巢功能障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E29睪丸功能障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E30青春期疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E34其他內分泌疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E40營養不良']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E50維生素缺乏']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E61其他營養元素缺乏']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E66體重過重及肥胖']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E67營養過度']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E70胺基酸代謝疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E73乳糖酶缺乏']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E74碳水化合物代謝疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E78脂蛋白代謝疾患及其他血脂症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E79嘌呤及嘧啶代謝疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E80紫質症及膽紅素代謝疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E83礦物質代謝疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E87體液,電解質及酸鹼平衡疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '04內分泌,營養和代謝', 'E88其他代謝疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '05精神與行為']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F01失智症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F04生理狀況之精神疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F10酒精相關疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F11藥物濫用']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F17尼古丁依賴']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F20精神分裂症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F30躁症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F32鬱症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F40焦慮症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F42強迫症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F43嚴重壓力反應與適應障礙症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F44解離性和轉化症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F50飲食疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F51睡眠疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F52性功能障礙症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F60特定人格疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F63衝動疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F64性別認同疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F65性倒錯']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F70智能不足']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F80發展疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F90注意力缺失過動疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F91行為疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F93兒童或青少年期功能疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F95抽搐症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '05精神與行為', 'F98兒童及青少年期行為情緒疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '06神經系統與感覺器官']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G00腦膜炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G04腦炎,脊髓炎及腦脊髓炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G10舞蹈症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G11遺傳性共濟失調']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G12脊髓性肌肉萎縮及相關症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G20帕金森氏病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G24肌張力不全']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G25顫抖']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G30阿茲海默氏病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G35多發性硬化症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G40癲癇']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G43偏頭痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G44其他頭痛症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G45短暫性腦缺血發作症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G46腦血管症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G47睡眠疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G50三叉神經疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G51顏面神經疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G52其他腦神經疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G54神經根及神經叢疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G56上肢單一神經病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G57下肢單一神經病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G70重症肌無力及其他肌肉神經疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G71肌肉特發性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G80嬰兒腦性麻痺']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G81偏癱']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G82下身癱瘓[截癱]及四肢癱']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G83其他麻痺性症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G89痛，他處未分類']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G90自主神經系統疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G91水腦症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '06神經系統與感覺器官', 'G93腦其他疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '07眼睛及其附屬器官']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H00眼瞼疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H04淚道系統疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H05眼窩疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H10結膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H15鞏膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H16角膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H20虹膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H25白內障']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H27水晶體疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H30視網膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H40青光眼']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H43玻璃體疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H44眼球疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H47視神經疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H49斜視']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H51雙眼運動疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H52屈光調節疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H53視覺障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H54失明及低視力']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H55眼球震顫及不規則眼球運動']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '07眼睛及其附屬器官', 'H57眼睛及附屬器官其他疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '08耳與乳突']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H60外耳疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H65中耳疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H68耳咽管疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H70乳突疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H71中耳膽脂瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H72鼓膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H74中耳乳突疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H80耳硬化症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H81前庭功能疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H83內耳疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H90耳聾']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H92耳痛及積液']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '08耳與乳突', 'H93耳部其他疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '09循環系統']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I00風濕性心臟病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I10本態性高血壓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I11高血壓性心臟及腎臟病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I15續發性高血壓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I20心絞痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I21心肌梗塞']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I24缺血性心臟病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I26肺栓塞']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I27肺性心臟病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I28肺血管疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I30心包膜炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I34非風濕性二尖瓣疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I40心肌疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I46心跳休止']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I47心搏過速']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I48心房顫動']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I49心臟節律不整']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I50心臟衰竭']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I51其他心臟疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I60非外傷性蜘蛛網膜下腔出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I61非外傷性腦出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I63腦梗塞']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I65腦動脈阻塞及狹窄']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I67腦血管疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I69腦血管疾病後遺症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I70動脈粥樣硬化']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I71動脈瘤']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I73末梢血管疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I74動脈栓塞及血栓症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I77其他動脈疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I78毛細血管疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I80靜脈炎及血栓靜脈炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I83下肢靜脈曲張']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I85其他部位靜脈曲張']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I88淋巴管和淋巴結疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '09循環系統', 'I95低血壓']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '10呼吸系統']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J00急性鼻咽炎（感冒）']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J01急性鼻竇炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J02急性咽炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J03急性扁桃腺炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J04急性喉炎和氣管炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J05急性阻塞性喉炎和會厭炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J06急性上呼吸道感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J09流行性感冒']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J12病毒性肺炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J13細菌性肺炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J18肺炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J20急性支氣管炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J22急性下呼吸道感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J30過敏性鼻炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J31慢性鼻炎,鼻咽炎及咽炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J32慢性鼻竇炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J33鼻息肉']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J34鼻及鼻竇疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J35慢性扁桃腺疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J37慢性喉炎及喉氣管炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J38聲帶及喉部疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J40支氣管炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J43肺氣腫']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J44慢性阻塞性肺病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J45氣喘']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J47支氣管擴張症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J60塵肺症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J68吸入外物所致之肺炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J80成人呼吸窘迫症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J81肺水腫']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J85肺和縱膈膿瘍']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J93氣胸']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J94其他肋膜病況']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '10呼吸系統', 'J96呼吸衰竭']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '11消化系統']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K02齲齒']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K05齒齦炎及牙周疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K09口腔部位囊腫']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K11唾液腺疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K12口腔炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K13唇及口腔黏膜疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K14舌疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K20食道炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K21胃食道逆流性疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K22食道其他疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K25胃潰瘍']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K26十二指腸潰瘍']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K27消化性潰瘍']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K29胃炎及十二指腸炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K30消化不良']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K31胃及十二指腸其他疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K35闌尾疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K40疝氣']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K50克隆氏病(局部性腸炎)']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K51結腸炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K56腸阻塞']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K57腸憩室性疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K58激躁性腸症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K59便秘及腹瀉']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K60肛門裂隙及瘻管']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K61肛門及直腸疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K63腸其他疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K64痔瘡及肛門周圍靜脈血栓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K65腹膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K70酒精性肝疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K71毒性肝疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K72肝衰竭']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K73慢性肝炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K74肝纖維化及硬化']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K75發炎性肝疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K76肝其他疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K80膽結石']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K81膽囊疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K83膽管炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K85胰臟疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K90腸吸收不良']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '11消化系統', 'K92消化系統其他疾病']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '12皮膚及皮下組織']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L01膿痂疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L02皮膚膿瘍，癤和癰']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L03蜂窩組織炎和急性淋巴管炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L05潛毛性囊腫和瘻管']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L08皮膚及皮下組織的其他局部感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L10天疱瘡']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L13水疱性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L20異位性皮膚炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L21脂漏性皮膚炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L22尿布疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L23接觸性皮膚炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L26剝落性皮膚炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L27內服物質所致之皮膚炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L28慢性單純苔癬和癢疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L30其他皮膚炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L40乾癬']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L42玫瑰糠疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L43扁平苔癬']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L44鱗屑性丘疹樣疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L49紅疹剝落']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L50蕁麻疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L51紅斑']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L55曬傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L56紫外線照射皮膚疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L60指(趾)甲疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L63圓禿落髮']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L67髮色及髮幹異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L68多毛症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L70痤瘡']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L71酒渣']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L72皮膚及皮下組織毛囊疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L74汗腺疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L80白斑']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L81色素沉著疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L82脂漏性角化症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L83黑棘皮症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L84雞眼及胼胝']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L85表皮增厚']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L89壓迫性潰瘍']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L90皮膚萎縮性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L91皮膚肥厚性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L92皮膚及皮下組織肉芽腫疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L93紅斑性狼瘡']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '12皮膚及皮下組織', 'L94局限性結締組織疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '13肌肉骨骼系統及結締組織']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M00化膿性關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M01感染及寄生蟲所致關節感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M02感染後及反應性關節病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M05類風濕性關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M08幼年型關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M10痛風']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M11結晶性關節病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M12其他關節病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M13其他關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M14多關節病症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M16髖部骨關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M17膝部骨關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M18腕掌關節骨關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M19其他骨關節炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M1A慢性痛風']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M20手指及(足)趾後天性變形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M21其他後天性肢體變形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M22髕骨疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M23膝內在障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M24其他關節障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M25其他關節疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M32全身性紅斑性狼瘡']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M33皮多肌炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M34全身性硬化症(硬皮症)']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M35結締組織其他全身性侵犯']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M40脊椎後彎症及脊椎前彎症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M41脊椎側彎症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M42脊椎骨軟骨症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M43其他變形性背部病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M45僵直性脊椎炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M46其他發炎性脊椎病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M47退化性脊椎炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M48其他脊椎病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M50頸椎椎間盤疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M51胸椎,胸腰椎及腰薦椎椎間盤疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M53其他背部病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M54背痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M60肌炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M61肌肉鈣化及骨化']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M62肌肉其他疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M65滑膜炎及腱鞘炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M66滑膜及肌腱自發性破裂']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M67滑膜及肌腱其他疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M70過度使用及壓力軟組織疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M71其他滑囊病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M72纖維母細胞性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M75肩部病灶']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M76下肢軟組織附著處病變，足除外']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M77其他軟組織附著處病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M80骨質疏鬆症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M83成人軟骨症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M85骨密度及構造其他疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M86骨髓炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M87骨壞死']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M88變形性骨炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M89其他骨疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M91幼年型髖部及骨盆骨軟骨症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '13肌肉骨骼系統及結締組織', 'M93其他軟骨疾患']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '14生殖泌尿系統']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N00急性腎炎症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N02慢性腎炎症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N04腎病症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N10腎小管－間質腎炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N13阻塞性及逆流性泌尿道病變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N17急性腎衰竭']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N18慢性腎臟疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N20腎結石及輸尿管結石']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N21下泌尿道結石']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N23未特定之腎絞痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N25腎小管功能不良疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N26未特定腎臟萎縮']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N28腎及輸尿管其他疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N30膀胱炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N31膀胱神經肌肉機功能障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N32其他膀胱疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N34尿道炎及尿道症候群']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N35尿道狹窄']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N36尿道疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N39泌尿系統疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N40攝護腺疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N43陰囊水腫和精液囊腫']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N44睪丸疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N46男性不孕症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N47包皮疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N48陰莖疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N49男性生殖器官炎性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N52男性勃起障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N53男性性功能障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N60乳房發育不良']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N61乳房疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N70輸卵管炎和卵巢炎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N71子宮及子宮頸炎性疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N73女性骨盆炎性疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N75前庭大腺疾病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N76陰道及女外陰其他炎症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N80子宮內膜異位症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N81女性生殖器脫垂']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N82女性生殖道瘻管']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N83卵巢,輸卵管疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N84女性生殖道息肉']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N85子宮及子宮頸非炎性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N89陰道非炎性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N90女外陰及會陰非炎性疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N91無月經,月經過少及稀少']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N92月經過多,頻繁且不規則']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N93子宮及陰道異常出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N94女性生殖器官及月經週期疼痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N95停經疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N96習慣性流產']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N97女性不孕症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '14生殖泌尿系統', 'N98人工受孕相關併發症']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '15妊娠,生產與產褥期合併症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O00子宮外孕']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O01葡萄胎']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O03自然流產']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O04終止妊娠']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O09高危險妊娠之監測']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O10妊娠,生產及產褥期本態性高血壓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O11高血壓性疾患伴有加重蛋白尿']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O12妊娠性水腫及蛋白尿無高血壓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O13妊娠性高血壓無明顯蛋白尿']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O14子癇前症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O15子癇症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O16母體高血壓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O20早期妊娠出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O21妊娠孕吐']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O22妊娠靜脈併發症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O23妊娠生殖泌尿道感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O24妊娠,生產及產褥期糖尿病']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O25妊娠,生產及產褥期營養不良']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O26妊娠引起其他狀況的母體照護']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O368特定胎兒問題的母體照護']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O40羊水及羊膜疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O46產前出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O47假性陣痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O72產後出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O86產褥期感染']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O87產褥期靜脈併發症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O90產褥期併發症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O92妊娠與產褥期乳房及乳汁分泌疾患']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '15妊娠,生產與產褥期合併症', 'O99妊娠及產褥期母體感染']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '16源於週產期的指引']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '16源於週產期的指引', 'P58新生兒黃疸']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '17先天性畸形,變形與染色體異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q00無腦症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q02小頭症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q03先天性水腦症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q04腦先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q05脊椎裂']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q06脊髓先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q07神經系統先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q11無眼症,小眼畸形及巨眼畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q17耳先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q18顏面及頸先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q20心臟先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q27血管系統先天性畸形 ']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q28循環系統先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q30鼻先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q31喉先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q32氣管和支氣管先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q33先天性肺畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q35唇腭裂']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q38舌,口腔及咽先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q39食道先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q40消化道先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q41腸先天性缺損,閉鎖狹窄與畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q50輸卵管及子宮先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q51子宮及子宮頸先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q52女性生殖器先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q53隱睪及睪丸異位']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q54尿道下裂']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q55男性生殖器先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q56性別不明及假性陰陽人']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q60腎無發育及腎其他縮減缺陷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q62先天性腎盂阻塞缺陷及輸尿管畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q63先天性腎畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q64先天性泌尿系統畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q65先天性髖部變形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q66先天性足變形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q67先天性肌肉骨骼變形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q69多指[趾]']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q70併指[趾]']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q71先天性上肢完全缺損']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q72先天性下肢完全缺損']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q73先天性肢體短縮缺陷及畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q75先天性顱骨及顏面骨畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q76先天性脊椎及骨胸廓畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q77骨發育不良及脊椎生長缺陷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q80先天性魚鱗癬']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q81水疱性表皮鬆解症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q82皮膚先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q83乳房先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q84體表先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q85斑痣性瘤症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q89其他先天性畸形']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q90唐氏症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '17先天性畸形,變形與染色體異常', 'Q91染色體異常']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '18症狀,癥候,與臨床異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R00心搏異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R03異常血壓']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R04呼吸道出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R05咳嗽']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R06呼吸異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R07喉嚨痛及胸痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R09循環及呼吸系統症狀']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R10腹痛及骨盆痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R11噁心及嘔吐']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R12胸口灼熱感']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R13吞嚥不能及吞嚥困難']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R14胃腸脹氣']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R15大便失禁']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R16肝腫大及脾腫大']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R17未特定性黃疸']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R18腹水']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R19消化系統及腹部症狀']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R20皮膚感覺障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R21皮疹及其他皮膚出疹']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R22皮膚及皮下組織局部腫脹,腫塊及小腫塊']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R23皮膚改變']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R25異常不自主運動']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R26異常步態及移動性異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R27協同作用缺乏']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R29神經及肌肉骨骼系統症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R30排尿及相關疼痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R31血尿']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R32尿失禁']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R33尿滯留']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R34無尿及少尿']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R35多尿']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R36尿道分泌物']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R37性功能障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R39生殖系統其他症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R40嗜眠,木僵及昏迷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R41認知功能與察覺能力症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R42頭暈及目眩']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R43嗅覺及味覺障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R44感覺及知覺症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R45情緒狀態症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R46外觀及行為症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R47言語障礙']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R48讀字困難']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R49嗓音共振異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R50不明原因發燒']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R51頭痛與疼痛']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R53乏力及疲勞']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R55暈厥及虛脫']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R56痙攣']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R57休克及出血']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R59淋巴結腫大']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R60水腫']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R61全身性多汗症']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R62兒童期及成人生理發育不符正常預期']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R63飲食攝取症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R65全身炎症及感染症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R68其他一般性症狀及徵候']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R71血液異常']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '18症狀,癥候,與臨床異常', 'R80尿液異常']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '19傷害,中毒與其它外因']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S00頭部表淺損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S03頭部關節及韌帶脫臼及扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S04腦神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S06顱內損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S07頭部壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S09頭部其他損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S10頸部表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S13頸部關節及韌帶脫臼及扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S14頸部神經及脊髓損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S16頸部肌肉，筋膜和肌腱損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S17頸部壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S19頸部損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S20胸部表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S23胸部關節及靱帶之扭傷及脫位']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S24胸椎脊髓及神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S28胸部壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S30腹部,下背部和骨盆和外生殖器官表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S33腰部,腰椎,骨盆關節和韌帶脫臼,扭傷及拉傷(勞損)']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S37泌尿和骨盆腔器官傷害']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S40肩膀和上臂表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S43肩帶的關節和韌帶脫臼和扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S44肩部和上臂神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S46肩部肌肉,筋膜和肌腱損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S47肩部和上臂壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S49肩部及上臂損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S50肘部表淺損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S53手肘關節及韌帶脫臼及拉傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S54前臂區位神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S56前臂區位肌肉,筋膜及肌腱損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S57手肘及前臂壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S59側性手肘及前臂損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S60腕部,手部及手指表淺損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S63腕部及手部關節及韌帶脫臼及扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S64腕及手部位之神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S66腕和手位於肌肉,筋膜及肌腱損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S67腕,手部及手指壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S69腕,手及手指損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S70髖及大腿表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S72股骨閉鎖性骨折']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S73髖關節及韌帶之脫臼及扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S74神經在髖及大腿處損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S76髖肌肉,筋膜及肌腱在髖及大腿處之損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S77髖及大腿壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S79髖及大腿損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S80膝及小腿表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S82小腿,包括踝部閉鎖性骨折']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S83膝關節及韌帶脫臼及扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S84小腿神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S86肌肉,筋膜,跟鍵損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S87小腿壓砸(擠壓)傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S89小腿損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S90踝部,足部及腳趾表淺性損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S92足部與腳趾骨折,足踝除外']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S93踝,足,趾關節及韌帶脫臼和扭傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S94踝和足神經損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S96踝和足肌肉和肌腱損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S97踝及足部壓砸傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'S99踝部和足其他損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T07未特定多處損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T14身體損傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T20頭,臉及頸程度燒傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T21軀幹燒傷及腐蝕傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T22肩部及上肢燒傷及腐蝕傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T23腕及手燒傷及腐蝕傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T24下肢燒燙傷及腐蝕傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T25踝及足燒燙傷和腐蝕傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T33表淺性凍傷']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T67熱及光的影響']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T68體溫過低']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T69溫度降低的其他之影響']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T71窒息']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '19傷害,中毒與其它外因', 'T76受虐及遺棄']
    database.insert_record('dict_groups', fields, data)

    data = ['病名類別', None, '20罹病與致死之外因']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'V00行人運輸工具之意外事故']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'W01在同一平面上滑倒,絆倒及踉蹌']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'W19跌倒']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'W21被運動設備撞擊或擊中']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'W22撞擊或被其他物體撞擊']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'W23被物件鉤住,壓砸,卡住或夾到']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'W50意外被人打,撞,踢,擰(扭),咬或抓(傷)']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'Y80物理治療裝置備的不良事件']
    database.insert_record('dict_groups', fields, data)
    data = ['病名', '20罹病與致死之外因', 'Y84醫療處置引起病人異常反應']
    database.insert_record('dict_groups', fields, data)

def cvt_pymedical_other_groups(source_db):
    sql = 'UPDATE clinic SET ClinicType = "辨證" WHERE ClinicType = "內辨"'
    source_db.exec_sql(sql)
    sql = 'UPDATE clinic SET ClinicType = "辨證" WHERE ClinicType = "傷辨"'
    source_db.exec_sql(sql)
    sql = 'UPDATE clinic SET ClinicType = "治則" WHERE ClinicType = "內治"'
    source_db.exec_sql(sql)
    sql = 'UPDATE clinic SET ClinicType = "治則" WHERE ClinicType = "傷治"'
    source_db.exec_sql(sql)

