# 系統設定 2018.03.28
CREATE TABLE IF NOT EXISTS system_settings
(
	SystemSettingsKey	INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	StationNo		INT,					# 工作站編號
									# 00-全院   01-99 各工作站
	Field			VARCHAR(100),				# 項目名稱
	Value			VARCHAR(200),				# 設定內容

	TimeStamp		TIMESTAMP,				# 上次異動日期

	PRIMARY KEY(SystemSettingsKey),
	INDEX(StationNo, Field)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
