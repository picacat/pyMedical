# 日誌檔 2019.05.09
CREATE TABLE IF NOT EXISTS system_log
(
	LogKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	LogType	    VARCHAR(20),					# 申報日期, ...
	LogName	    VARCHAR(20),					# 日誌名稱, ...

	Log	        VARCHAR(100),				    # 日誌內容

	TimeStamp	    	TIMESTAMP,				# 上次異動日期

	PRIMARY KEY(LogKey),
	INDEX(LogType, LogName)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
