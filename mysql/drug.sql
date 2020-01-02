CREATE TABLE `drug` (
  `DrugKey` int(11) NOT NULL AUTO_INCREMENT,
  `InsCode` varchar(12) DEFAULT NULL,
  `DrugName` varchar(40) DEFAULT NULL,
  `MedicineType` varchar(10) DEFAULT NULL,
  `Unit` varchar(10) DEFAULT NULL,
  `InsPrice` int(11) DEFAULT NULL,
  `Supplier` varchar(50) DEFAULT NULL,
  `ValidDate` varchar(10) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`DrugKey`),
  KEY `InsCode` (`InsCode`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
