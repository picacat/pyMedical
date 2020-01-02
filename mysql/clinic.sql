CREATE TABLE `clinic` (
  `ClinicKey` int(11) NOT NULL AUTO_INCREMENT,
  `ClinicType` varchar(4) DEFAULT NULL,
  `ClinicCode` varchar(5) DEFAULT NULL,
  `InputCode` varchar(5) DEFAULT NULL,
  `ClinicName` varchar(100) DEFAULT NULL,
  `HitRate` int(11) DEFAULT 0,
  `Position` varchar(40) DEFAULT NULL,
  `Groups` varchar(40) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`ClinicKey`),
  KEY `ClinicCode` (`ClinicCode`,`InputCode`)
) ENGINE=MyISAM DEFAULT CHARSET=big5;
