CREATE TABLE `debt` (
  `DebtKey` int(11) NOT NULL AUTO_INCREMENT,
  `CaseKey` int(11) NOT NULL DEFAULT 0,
  `PatientKey` int(11) NOT NULL DEFAULT 0,
  `DebtType` varchar(10) DEFAULT NULL,
  `Name` varchar(100) DEFAULT NULL,
  `CaseDate` datetime DEFAULT NULL,
  `Period` varchar(4) DEFAULT NULL,
  `Doctor` varchar(10) DEFAULT NULL,
  `Fee` int(11) DEFAULT NULL,
  `ReturnDate1` datetime DEFAULT NULL,
  `Period1` varchar(4) DEFAULT NULL,
  `Casher1` varchar(10) DEFAULT NULL,
  `Cashier1` varchar(10) DEFAULT NULL,
  `Fee1` int(11) DEFAULT NULL,
  `ReturnDate2` datetime DEFAULT NULL,
  `Period2` varchar(4) DEFAULT NULL,
  `Casher2` varchar(10) DEFAULT NULL,
  `Cashier2` varchar(10) DEFAULT NULL,
  `Fee2` int(11) DEFAULT NULL,
  `ReturnDate3` datetime DEFAULT NULL,
  `Period3` varchar(4) DEFAULT NULL,
  `Casher3` varchar(10) DEFAULT NULL,
  `Cashier3` varchar(10) DEFAULT NULL,
  `Fee3` int(11) DEFAULT NULL,
  `TotalReturn` int(11) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`DebtKey`),
  KEY `CaseKey` (`CaseKey`,`PatientKey`,`CaseDate`)
) ENGINE=MyISAM DEFAULT CHARSET=big5;