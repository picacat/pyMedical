/* 收費設定 2018.03.28 */
CREATE TABLE IF NOT EXISTS nurse_schedule
(
	NurseScheduleKey    INT AUTO_INCREMENT NOT NULL, # 索引鍵
	ScheduleDate        DATE,	        # 班表日期
	Doctor              VARCHAR(10),	# 醫師姓名
	Nurse1              VARCHAR(10),	# 早班護士
	Nurse2              VARCHAR(10),	# 午班護士
	Nurse3              VARCHAR(10),	# 晚班護士
	Remark              VARCHAR(200),	# 備註
	TimeStamp           TIMESTAMP,      # 上次異動日期
	PRIMARY KEY(NurseScheduleKey),
	INDEX(ScheduleDate, Doctor)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
