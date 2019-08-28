-- MariaDB dump 10.17  Distrib 10.4.7-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: mingi
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
-- WHERE:  PatientKey IN (SELECT PatientKey FROM cases WHERE CaseDate BETWEEN '2019-08-24 00:00:00' AND '2019-08-24 23:59:59')

LOCK TABLES `patient` WRITE;
/*!40000 ALTER TABLE `patient` DISABLE KEYS */;
INSERT INTO `patient` (`PatientKey`, `CardNo`, `RegistNo`, `Name`, `Era`, `Birthday`, `ID`, `Nationality`, `Gender`, `Sex`, `Telephone`, `Officephone`, `Cellphone`, `Email`, `ZipCode`, `Address`, `Marriage`, `Education`, `Occupation`, `DiscountType`, `DiscountReason`, `InsType`, `DiseaseName`, `PrivateInsurance`, `FamilyPatientKey`, `Reference`, `Trace`, `TraceTime`, `TraceType`, `InitDate`, `LastDate`, `Alergy`, `Allergy`, `History`, `Description`, `Remark`, `Note`, `TimeStamp`) VALUES (88,NULL,'','林明濤',NULL,'1957-03-16','V120007791','本國','男','男','034931338',NULL,NULL,NULL,'','桃園縣中壢市五福里五族街129號','','','','眷屬','','基層醫療',NULL,'',NULL,'','','','',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2019-08-24 05:04:15');
/*!40000 ALTER TABLE `patient` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-08-24 13:30:01
