# 檢驗檔內容 2019.08.13
CREATE TABLE IF NOT EXISTS examination_item
(
	ExaminationItemKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	ExaminationKey	        INT NOT NULL,	                # 檢驗主檔索引鍵
    PatientKey	            INT NOT NULL,		            # 病歷號
    Name	                VARCHAR(20),		            # 病患姓名
    ExaminationDate         DATE NOT NULL,                  # 檢驗日期
	ExaminationItem	        VARCHAR(50),					# 檢驗項目
	TestResult	            VARCHAR(40),					# 檢驗結果

	TimeStamp	    	    TIMESTAMP,				        # 上次異動日期

	PRIMARY KEY(ExaminationItemKey),
	INDEX(ExaminationKey, PatientKey, ExaminationDate)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
