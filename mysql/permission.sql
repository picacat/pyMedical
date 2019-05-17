# 權限檔 2019.05.17
CREATE TABLE IF NOT EXISTS permission
(
	PermissionKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	PersonKey           INT NOT NULL,                   # 人事資料檔索引
	ProgramName	        VARCHAR(300),					# 程式名稱
	PermissionItem	    VARCHAR(20),					# 權限名稱
	Permission	        VARCHAR(10),					# 權限: Y/N

	TimeStamp	    	TIMESTAMP,				        # 上次異動日期

	PRIMARY KEY(PermissionKey),
	INDEX(PersonKey, ProgramName, PermissionItem)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
