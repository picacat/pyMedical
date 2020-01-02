/* 養生館休診日期 2019.11.23 */
CREATE TABLE IF NOT EXISTS massage_off_day_list
(
	OffDayListKey           INT AUTO_INCREMENT NOT NULL, 	# 索引鍵
	OffDate                 Date,			                # 休診日期
	Period                  VARCHAR(20),	        	    # 休診班別
	Massager                VARCHAR(20),	        	    # 休診師父
	TimeStamp               TIMESTAMP,      		        # 上次異動日期

	PRIMARY KEY(OffDayListKey),
	INDEX(OffDate, Period)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
