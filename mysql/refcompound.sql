CREATE TABLE `refcompound` (
  `RefCompoundKey` int(11) NOT NULL AUTO_INCREMENT,
  `CompoundKey` int(11) NOT NULL DEFAULT 0,
  `MedicineKey` int(11) DEFAULT NULL,
  `Quantity` float DEFAULT NULL,
  `Unit` varchar(10) DEFAULT NULL,
  `TimeStamp` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`RefCompoundKey`),
  KEY `CompoundKey` (`CompoundKey`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
