/* 地址郵遞區號資料 2018.12.17 */
CREATE TABLE IF NOT EXISTS address_list
(
	AddressListKey   		INT AUTO_INCREMENT NOT NULL, # 索引鍵
	ZipCode          		VARCHAR(5),		# 郵遞區號: 3+2碼
	City            		VARCHAR(10),	# 縣市名稱
	District            VARCHAR(10),	# 鄉鎮市區
	Street           		VARCHAR(20),	# 原始路名
	MailRange           VARCHAR(50),	# 投遞範圍
	TimeStamp           TIMESTAMP,      # 上次異動日期
	PRIMARY KEY(AddressListKey),
	INDEX(ZipCode, City, District)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
