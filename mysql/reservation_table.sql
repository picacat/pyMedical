/* 預約班表 2018.09.19 */
CREATE TABLE IF NOT EXISTS reservation_table
(
	ReservationTableKey INT AUTO_INCREMENT NOT NULL, # 索引鍵
	Room                INT,	        # 診別
	Period              VARCHAR(10),	# 班別
	RowNo               INT,	        # row position
	ColumnNo            INT,	        # column position
	Time                VARCHAR(10),	# 時間
	ReserveNo           INT,	        # 診號
	TimeStamp           TIMESTAMP,      # 上次異動日期
	PRIMARY KEY(ReservationTableKey),
	INDEX(Room, Period, ColumnNo, RowNo)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
