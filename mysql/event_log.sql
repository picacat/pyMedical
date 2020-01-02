# 日誌檔 2019.05.09
CREATE TABLE IF NOT EXISTS event_log
(
	LogKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	UserName	VARCHAR(20),					# 使用者
	IP	        VARCHAR(20),					# IP位置
	LogType	    VARCHAR(20),					# 系統操作, 資料刪除, 資料查詢, 資料匯出
	ProgramName VARCHAR(20),					# 掛號作業, 病歷查詢, ...

	Log	        VARCHAR(100),				    # 日誌內容

	TimeStamp	    	TIMESTAMP,				# 上次異動日期

	PRIMARY KEY(LogKey),
	INDEX(LogType, ProgramName)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
