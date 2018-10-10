#!/usr/bin/env python3
import iccard_x86 as iccard


def main():
    basic_data = iccard.ICCard(4).get_basic_data()

    print('卡片號碼: {0}'.format(basic_data['card_no']))
    print('病患姓名: {0}'.format(basic_data['name']))
    print('身分證號: {0}'.format(basic_data['patient_id']))
    print('出生日期: {0}'.format(basic_data['birthday']))
    print('性　　別: {0}'.format(basic_data['gender']))
    print('發卡日期: {0}'.format(basic_data['card_date']))
    print('註銷註記: {0}'.format(basic_data['cancel_mark']))
    print('緊急電話: {0}'.format(basic_data['emg_phone']))
    print()
    

if __name__ == '__main__':
    main()
