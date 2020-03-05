CREATE TABLE `icd10` (
  `ICD10Key` int(11) NOT NULL AUTO_INCREMENT,
  `ICDCode` varchar(10) NOT NULL DEFAULT '',
  `InputCode` varchar(5) DEFAULT NULL,
  `ChineseName` varchar(100) DEFAULT NULL,
  `EnglishName` varchar(100) DEFAULT NULL,
  `SpecialCode` varchar(2) DEFAULT NULL,
  `Groups` varchar(100) DEFAULT NULL,
  `HitRate` int(11) DEFAULT 0,
  `Position1` varchar(2) DEFAULT NULL,
  `Position2` varchar(2) DEFAULT NULL,
  `Remark` varchar(50) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`ICD10Key`) USING BTREE,
  KEY `ICD10Code` (`ICDCode`),
  KEY `InputCode` (`InputCode`),
  KEY `ChineseName` (`ChineseName`)
) ENGINE=MyISAM AUTO_INCREMENT=91757 DEFAULT CHARSET=utf8;
