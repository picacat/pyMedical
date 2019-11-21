
# 養生館病歷處方檔    2019.11.20

CREATE TABLE IF NOT EXISTS massage_prescript
(
    MassagePrescriptKey	    INT AUTO_INCREMENT NOT NULL,  # 處方序號
    MassageCaseKey	        INT NOT NULL,	# 病歷序號
    MedicineKey	            INT,	        # 詞庫處方序號
    MedicineName            VARCHAR(40),  # 處方名稱

    Quantity	        Decimal(10, 2)  DEFAULT 0,   # 藥品用量
    Unit		        VARCHAR(10),	# 單位
    Price 	            Decimal(10, 2) DEFAULT 0,   # 單價
    Amount        	    Decimal(10, 2) DEFAULT 0,   # 金額
    Remark              VARCHAR(100),  # 備註

    TimeStamp	      TIMESTAMP,	  # 上次異動日期

    PRIMARY KEY(MassagePrescriptKey),
    INDEX(MassageCaseKey, MedicineKey)
) CHARACTER SET utf8;


