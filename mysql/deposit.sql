CREATE TABLE `deposit` (
  `DepositKey` int(11) NOT NULL AUTO_INCREMENT,
  `CaseKey` int(11) NOT NULL DEFAULT 0,
  `PatientKey` int(11) NOT NULL DEFAULT 0,
  `Name` varchar(100) DEFAULT NULL,
  `DepositDate` datetime DEFAULT NULL,
  `ReturnDate` datetime DEFAULT NULL,
  `Period` varchar(4) DEFAULT NULL,
  `Register` varchar(10) DEFAULT NULL,
  `Refunder` varchar(10) DEFAULT NULL,
  `Fee` int(11) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`DepositKey`),
  KEY `CaseKey` (`CaseKey`,`PatientKey`,`DepositDate`,`ReturnDate`)
) ENGINE=MyISAM DEFAULT CHARSET=big5;
