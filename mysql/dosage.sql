/* 收費設定 2018.03.28 */
CREATE TABLE IF NOT EXISTS dosage
(
	DosageKey           INT AUTO_INCREMENT NOT NULL, # 索引鍵
	CaseKey             INT NOT NULL,  # 病歷主鍵
	MedicineSet         INT,	        # 給藥組別
	Packages            INT,	        # 包
	Days                INT,	        # 天
	Instruction         VARCHAR(100),	# 服用方式
	Amount              INT,            # 金額
	Remark              VARCHAR(200),	# 備註
	TimeStamp           TIMESTAMP,      # 上次異動日期
	PRIMARY KEY(DosageKey),
	INDEX(CaseKey, MedicineSet)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
