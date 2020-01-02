CREATE TABLE `reserve` (
  `ReserveKey` int(11) NOT NULL AUTO_INCREMENT,
  `PatientKey` int(11) NOT NULL DEFAULT 0,
  `Name` varchar(100) DEFAULT NULL,
  `ReserveDate` datetime DEFAULT NULL,
  `Period` varchar(4) DEFAULT NULL,
  `Room` int(11) DEFAULT NULL,
  `Sequence` int(11) DEFAULT NULL,
  `ReserveNo` int(11) DEFAULT NULL,
  `Doctor` varchar(10) DEFAULT NULL,
  `Arrival` enum('False','True') NOT NULL,
  `Source` varchar(10) DEFAULT NULL,
  `Registrar` varchar(10) DEFAULT NULL,
  `Regist` enum('False','True') NOT NULL DEFAULT 'False',
  `Remark` text DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`ReserveKey`),
  KEY `PatientKey` (`PatientKey`,`ReserveDate`)
) ENGINE=MyISAM DEFAULT CHARSET=big5;
