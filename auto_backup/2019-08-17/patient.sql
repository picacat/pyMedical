-- MariaDB dump 10.17  Distrib 10.4.7-MariaDB, for Linux (x86_64)
--
-- Host: 192.168.2.105    Database: mingi
-- ------------------------------------------------------
-- Server version	10.4.7-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `patient`
--
-- WHERE:  PatientKey IN (SELECT PatientKey FROM cases WHERE CaseDate BETWEEN '2019-08-17 00:00:00' AND '2019-08-17 23:59:59')

LOCK TABLES `patient` WRITE;
/*!40000 ALTER TABLE `patient` DISABLE KEYS */;
INSERT INTO `patient` (`PatientKey`, `CardNo`, `RegistNo`, `Name`, `Era`, `Birthday`, `ID`, `Nationality`, `Gender`, `Sex`, `Telephone`, `Officephone`, `Cellphone`, `Email`, `ZipCode`, `Address`, `Marriage`, `Education`, `Occupation`, `DiscountType`, `DiscountReason`, `InsType`, `DiseaseName`, `PrivateInsurance`, `FamilyPatientKey`, `Reference`, `Trace`, `TraceTime`, `TraceType`, `InitDate`, `LastDate`, `Alergy`, `Allergy`, `History`, `Description`, `Remark`, `Note`, `TimeStamp`) VALUES (32,'000056627577','','江建緯','','1993-09-18','H124421901','本國','男','男','034660758','',NULL,NULL,'','中壢市勵志二街７號','','','',NULL,'','基層醫療',NULL,'',NULL,'','','','',NULL,'2011-01-12 15:17:23',NULL,NULL,NULL,NULL,NULL,NULL,'2019-08-16 21:58:24'),(33,'000012841998','','黃上淩',NULL,'1965-04-28','H220844437','本國','女','女','034660758',NULL,NULL,NULL,'',NULL,'','','',NULL,'','基層醫療',NULL,'',NULL,'','','','',NULL,'2006-03-25 09:32:48',NULL,NULL,NULL,NULL,NULL,NULL,'2019-08-16 21:58:05'),(101,'000013751256','','陳蔡蝦','','1926-05-07','Q201960467','本國','女','女','034922734',NULL,NULL,NULL,'','中壢市三梁二街33號','','','','老人','','健保',NULL,'',NULL,'','','','',NULL,'2013-09-28 09:20:57',NULL,NULL,NULL,NULL,NULL,NULL,'2019-07-18 01:53:45'),(102,'000010825637','','秦慧',NULL,'1972-09-05','J220917043','本國','女','女','034655051',NULL,NULL,NULL,'','中壢市國泰街105號','','','','','','健保',NULL,'',NULL,'','','','',NULL,'2006-06-26 09:56:31',NULL,NULL,NULL,NULL,NULL,NULL,'2019-07-18 01:53:45'),(103,NULL,'','黃崧源',NULL,'1969-05-22','H120844560','本國','男','男','034723187',NULL,NULL,NULL,'','桃園縣楊梅鎮富岡里中正路10號','','','','','','健保',NULL,'',NULL,'','','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2019-07-18 01:53:45'),(104,'000013792654','','陳怡君',NULL,'1981-08-20','Q222816393','本國','女','女','034654309','','',NULL,'','','','','','','','健保',NULL,'',NULL,'','','','',NULL,'2005-11-14 20:56:56',NULL,NULL,NULL,NULL,NULL,NULL,'2019-07-18 01:53:45'),(105,'000013780887','','楊啟正',NULL,'1974-10-09','Q121582172','本國','男','男','034928175',NULL,NULL,NULL,'','中壢市環西路2段25巷6弄11號','','','','其他','','健保',NULL,'',NULL,'','','','',NULL,'2009-02-21 09:41:42',NULL,NULL,NULL,NULL,NULL,NULL,'2019-07-18 01:53:45'),(106,'000054904285','','邱福妹','','1936-07-17','H201283852','本國','女','女','034223545','','',NULL,'','','','','','其他','不收費','健保',NULL,'',NULL,'','','','',NULL,'2008-01-29 14:45:44',NULL,NULL,NULL,NULL,NULL,NULL,'2019-07-18 01:53:45');
/*!40000 ALTER TABLE `patient` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-08-17  7:11:40
