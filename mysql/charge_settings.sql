/* 收費設定 2018.03.28 */
CREATE TABLE IF NOT EXISTS charge_settings
(
	ChargeSettingsKey   INT AUTO_INCREMENT NOT NULL, # 索引鍵
	ChargeType          VARCHAR(20),	# 收費類別: 掛號費, 門診負擔, 藥品負擔, 健保支付標準
	ItemName            VARCHAR(100),	# 項目名稱
	InsType             VARCHAR(10),	# 門診類別: 健保, 自費
	ShareType           VARCHAR(20),	# 負擔類別: 一般, 榮民, 福保, 重大傷病...
	TreatType           VARCHAR(20),	# 就醫類別: 內科, 針灸治療, 傷科治療
	Course              VARCHAR(10),	# 療程: 首次, 療程
	InsCode             VARCHAR(20),	# 健保代碼
	Amount              INT,            # 金額
	Remark              VARCHAR(200),	# 備註
	TimeStamp           TIMESTAMP,      # 上次異動日期
	PRIMARY KEY(ChargeSettingsKey),
	INDEX(ChargeType, ItemName, InsType, ShareType, TreatType)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
