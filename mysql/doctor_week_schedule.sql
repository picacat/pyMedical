/* 收費設定 2018.03.28 */
CREATE TABLE IF NOT EXISTS doctor_schedule
(
	DoctorScheduleKey   INT AUTO_INCREMENT NOT NULL, # 索引鍵
    Room 	            INT,            # 診別: 1, 2, 3...
    Period 	            VARCHAR(04),    # 班別: 早班, 午班, 晚班
	Monday              VARCHAR(10),	# 週一醫師
	Tuesday             VARCHAR(10),	# 週二醫師
	Wednesday           VARCHAR(10),	# 週三醫師
	Thursday            VARCHAR(10),	# 週四醫師
	Friday              VARCHAR(10),	# 週五醫師
	Saturday            VARCHAR(10),	# 週六醫師
	Sunday              VARCHAR(10),	# 週日醫師
	TimeStamp           TIMESTAMP,      # 上次異動日期
	PRIMARY KEY(DoctorScheduleKey),
	INDEX(Room, Period)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
