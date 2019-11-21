/* 休診日期 2018.08.31 */
CREATE TABLE IF NOT EXISTS off_day_list
(
	OffDayListKey   INT AUTO_INCREMENT NOT NULL, 	# 索引鍵
	OffDate         Date,			                # 休診日期
	Period          VARCHAR(20),	        	    # 休診班別
	Doctor          VARCHAR(20),	        	    # 休診醫師
	TimeStamp       TIMESTAMP,      		        # 上次異動日期

	PRIMARY KEY(OffDayListKey),
	INDEX(OffDate, Period)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
