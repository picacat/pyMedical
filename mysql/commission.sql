# 抽成檔 2019.05.27
CREATE TABLE IF NOT EXISTS commission
(
	CommissionKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	MedicineKey         INT NOT NULL,                   # 處方檔索引
	Name	            VARCHAR(20),					# 程式名稱
	Commission	        VARCHAR(10),					# 抽成
	Remark              VARCHAR(100),                   # 備註

	TimeStamp	    	TIMESTAMP,				        # 上次異動日期

	PRIMARY KEY(CommissionKey),
	INDEX(MedicineKey, Name)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
