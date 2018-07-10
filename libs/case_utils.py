import xml.etree.ElementTree as ET
from libs import string_utils


# 取出病歷檔安全簽章XML
def extract_security_xml(xml_field, field):
    ic_card_xml = string_utils.get_str(xml_field, 'utf-8')
    try:
        root = ET.fromstring(ic_card_xml)[0]
    except ET.ParseError:
        return ''

    content_dict = {
        '寫卡時間': root[0].text,
        '健保卡序': root[1].text,
        '院所代號': root[2].text,
        '安全簽章': root[3].text,
        '安全模組': root[4].text,
        '同日就診': root[5].text,
    }

    return content_dict[field]
