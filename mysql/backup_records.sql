# 備份檔 2019.06.27
CREATE TABLE IF NOT EXISTS backup_records
(
	BackupRecordsKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	TableName	            VARCHAR(50),					# 表格名稱
	KeyField	            VARCHAR(50),					# 主鍵
	KeyValue	            INT,					        # 主鍵值
	JSON                    TEXT,                           # 備份內容
	Deleter	                VARCHAR(50),					# 刪除者
	DeleteDateTime	        DATETIME,					    # 刪除時間
	RecordRestored	        VARCHAR(10),					# 資料已回復 是/Null

	TimeStamp	    	TIMESTAMP,				# 上次異動日期

	PRIMARY KEY(BackupRecordsKey),
	INDEX(TableName, KeyField, KeyValue)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
