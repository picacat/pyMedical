# 檢驗檔 2019.08.09
CREATE TABLE IF NOT EXISTS examination
(
	ExaminationKey	        INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
    PatientKey	            INT NOT NULL,		            # 病歷號
    Name	                VARCHAR(20),		            # 病患姓名
    ExaminationDate         DATE NOT NULL,                  # 檢驗日期
	Laboratory	            VARCHAR(50),					# 檢驗所
	MLS	                    VARCHAR(20),					# 醫檢師

	TimeStamp	    	    TIMESTAMP,				        # 上次異動日期

	PRIMARY KEY(ExaminationKey),
	INDEX(PatientKey, ExaminationDate)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
