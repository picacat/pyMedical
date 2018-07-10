

# 取得服藥頻率代碼
def get_usage_code(package):
    usage_dict = {
        1: 'QD',
        2: 'BID',
        3: 'TID',
        4: 'QID',
    }

    return usage_dict[package]


# 取得服藥方式代碼
def get_instruction_code(instruction):
    if instruction.find('飯前') >= 0:
        instruction_code = 'AC'
    elif instruction.find('飯後') >= 0:
        instruction_code = 'PC'
    else:
        instruction_code = ''

    return  instruction_code
