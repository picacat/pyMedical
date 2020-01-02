CREATE TABLE `hospid` (
  `HospKey` int(11) NOT NULL AUTO_INCREMENT,
  `HospID` varchar(10) DEFAULT NULL,
  `HospName` varchar(100) DEFAULT NULL,
  `Telephone` varchar(50) DEFAULT NULL,
  `Address` varchar(100) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`HospKey`),
  KEY `HospID` (`HospID`)
) ENGINE=MyISAM DEFAULT CHARSET=big5;
