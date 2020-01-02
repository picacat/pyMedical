CREATE TABLE `presextend` (
  `PresExtendKey` int(11) NOT NULL AUTO_INCREMENT,
  `PrescriptKey` int(11) DEFAULT NULL,
  `ExtendType` varchar(10) DEFAULT NULL,
  `Content` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`PresExtendKey`),
  KEY `PrescriptKey` (`PrescriptKey`,`ExtendType`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
