
# 顧客檔  2019.11.14      養生館

CREATE TABLE IF NOT EXISTS massage_customer
(
    MassageCustomerKey	    INT AUTO_INCREMENT NOT NULL,  # 顧客檔主鍵
    PatientKey	        INT ,	# 病患資料主鍵
    Name        VARCHAR(20),    # 病患姓名
    Birthday    DATE,           # 出生日期
    ID          VARCHAR(10),    # 身份證號
    Gender      VARCHAR(04),    # 性別
    Telephone	  VARCHAR(15),	  # 聯絡電話 (Home)
    Cellphone	  VARCHAR(15),	  # 行動電話
    Email       VARCHAR(50),

    ZipCode	    VARCHAR(05),	  # 郵遞區號
    Address	    VARCHAR(50),	  # 聯絡地址

    InitDate	    DATETIME,	      # 初診日期

    Remark      VarChar(200),   # 備註

    TimeStamp	TIMESTAMP,	    # 上次異動日期

    PRIMARY KEY(MassageCustomerKey),
    INDEX(PatientKey, Name, ID)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
