CREATE TABLE `medicine` (
  `MedicineKey` int(11) NOT NULL AUTO_INCREMENT,
  `MedicineType` varchar(10) DEFAULT NULL,
  `MedicineMode` varchar(20) DEFAULT NULL,
  `MedicineCode` varchar(5) DEFAULT NULL,
  `InputCode` varchar(5) DEFAULT NULL,
  `InsCode` varchar(12) DEFAULT NULL,
  `MedicineName` varchar(40) DEFAULT NULL,
  `MedicineAlias` varchar(40) DEFAULT NULL,
  `Unit` varchar(10) DEFAULT NULL,
  `Dosage` decimal(10,2) DEFAULT NULL,
  `Location` varchar(20) DEFAULT NULL,
  `SalePrice` decimal(10,2) DEFAULT NULL,
  `InPrice` decimal(10,2) DEFAULT NULL,
  `Commission` varchar(10) DEFAULT NULL,
  `Project` varchar(50) DEFAULT NULL,
  `DoctorProject` varchar(50) DEFAULT NULL,
  `Charged` varchar(4) DEFAULT NULL,
  `Quantity` decimal(10,2) DEFAULT NULL,
  `SafeQuantity` decimal(10,2) DEFAULT NULL,
  `Description` mediumtext DEFAULT NULL,
  `HitRate` int(11) DEFAULT 0,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`MedicineKey`),
  KEY `InsCode` (`InsCode`,`InputCode`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;