# 詞庫類別 2018.05.09
CREATE TABLE IF NOT EXISTS dict_groups
(
	DictGroupsKey	    INT	AUTO_INCREMENT NOT NULL,	# 索引鍵
	DictGroupsType	    VARCHAR(20),					# 群組類別: 主訴, 舌診, 病名, 藥品, 處置

	DictGroupsTopLevel	VARCHAR(20),				# 上層類別名稱: 主訴: 內科, 傷科, 婦科, 兒科, 處方: 單方, 複方, 病名: 呼吸道
	DictGroupsLevel2	VARCHAR(20),				# 第二層類別: 內科-頭部, 面部, 疼痛, 婦科-月經..., 病名: 上呼吸道感染
	DictGroupsName		VARCHAR(50),				# 類別名稱

	TimeStamp	    	TIMESTAMP,				# 上次異動日期

	PRIMARY KEY(DictGroupsKey),
	INDEX(DictGroupsType, DictGroupsTopLevel, DictGroupsLevel2)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
