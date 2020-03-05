CREATE TABLE `images` (
  `ImageKey` int(11) NOT NULL AUTO_INCREMENT,
  `CaseKey` int(11) NOT NULL DEFAULT 0,
  `PatientKey` int(11) NOT NULL DEFAULT 0,
  `Filename` varchar(40) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`ImageKey`),
  KEY `CaseKey` (`CaseKey`,`PatientKey`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
