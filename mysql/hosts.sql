# 分院連線設定 2019.06.21
CREATE TABLE IF NOT EXISTS hosts
(
	HostsKey	            INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	ClinicName	            VARCHAR(50),					# 分院名稱
	Host	                VARCHAR(30),					# 伺服器IP
	DatabaseName	        VARCHAR(20),					# 資料庫名稱
	UserName	            VARCHAR(20),					# 使用者名稱
	Password	            VARCHAR(20),					# 密碼
	Charset	                VARCHAR(20),					# 字元編碼
	Vendor	                VARCHAR(20),					# 醫療系統廠商
	HISVersion	            VARCHAR(20),					# 醫療系統版本

	TimeStamp	    	    TIMESTAMP,				        # 上次異動日期

	PRIMARY KEY(HostsKey),
	INDEX(ClinicName, Host, DatabaseName)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
