-- MariaDB dump 10.17  Distrib 10.4.7-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: med2000
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
-- Dumping data for table `reserve`
--
-- WHERE:  ReserveDate BETWEEN '2019-08-20 00:00:00' AND '2019-08-20 23:59:59'

LOCK TABLES `reserve` WRITE;
/*!40000 ALTER TABLE `reserve` DISABLE KEYS */;
INSERT INTO `reserve` (`ReserveKey`, `PatientKey`, `Name`, `ReserveDate`, `Period`, `Room`, `ReserveNo`, `Doctor`, `Source`, `Arrival`, `PatInitial`, `Remark`, `TimeStamp`) VALUES (6762,914,'徐靜琳','2019-08-20 18:10:00','晚班',1,2,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-12 11:06:08'),(6881,1271,'白御豪','2019-08-20 18:50:00','晚班',1,6,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 10:14:31'),(6966,276,'劉鈺婷','2019-08-20 20:50:00','晚班',1,18,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 07:10:50'),(6918,100,'郭子輝','2019-08-20 16:00:00','午班',1,16,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-15 06:18:38'),(6724,1186,'蘇文仲','2019-08-20 14:30:00','午班',1,3,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-11 12:15:29'),(7032,1987,'陳逸芬','2019-08-20 20:30:00','晚班',1,19,'薛如妤','現場預約','False',NULL,NULL,'2019-08-17 15:10:36'),(6795,124,'黃子豪','2019-08-20 18:40:00','晚班',1,5,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-13 01:03:07'),(7026,940,'陳森彥','2019-08-20 15:00:00','午班',1,8,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-17 10:22:38'),(6805,65,'陳秀卿','2019-08-20 15:30:00','午班',1,11,'吳柏儒','現場預約','False',NULL,NULL,'2019-08-13 07:10:37'),(6806,702,'陳政揚','2019-08-20 19:50:00','晚班',1,12,'吳柏儒','網路初診預約','False',NULL,NULL,'2019-08-13 07:18:27'),(6814,731,'魏子涵','2019-08-20 18:20:00','晚班',1,3,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-13 10:28:46'),(6820,627,'蔡孟真','2019-08-20 18:00:00','晚班',1,3,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 11:20:59'),(6822,1340,'田榿綪','2019-08-20 18:30:00','晚班',1,7,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 11:32:33'),(6825,1879,'張芷瑜','2019-08-20 19:00:00','晚班',1,8,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 11:41:29'),(6829,220,'翁榕鎂','2019-08-20 20:00:00','晚班',1,13,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-13 12:23:18'),(6830,1803,'周恒光','2019-08-20 18:00:00','晚班',1,1,'吳柏儒','現場預約','False',NULL,NULL,'2019-08-13 12:23:50'),(6834,1645,'陳子禾','2019-08-20 19:00:00','晚班',1,11,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 12:41:02'),(6836,284,'游惠鈺','2019-08-20 20:00:00','晚班',1,15,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 13:10:57'),(6843,1580,'黃瓘婷','2019-08-20 20:00:00','晚班',1,17,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 13:59:53'),(6844,1581,'謝瓊瑢','2019-08-20 20:00:00','晚班',1,18,'薛如妤','網路預約','False',NULL,NULL,'2019-08-13 14:00:00'),(6850,1762,'孫鵬鈞','2019-08-20 20:10:00','晚班',1,14,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-13 15:58:45'),(6864,345,'蔡月惠','2019-08-20 20:20:00','晚班',1,15,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 04:24:27'),(6865,307,'洪宏霖','2019-08-20 20:30:00','晚班',1,16,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 04:24:45'),(6879,1431,'王之尹','2019-08-20 16:00:00','午班',1,15,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 10:03:44'),(6882,1425,'張嘉雯','2019-08-20 19:00:00','晚班',1,7,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 10:14:40'),(6898,1745,'李家豪','2019-08-20 19:10:00','晚班',1,8,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 14:03:50'),(7033,1986,'袁語柔','2019-08-20 20:30:00','晚班',1,21,'薛如妤','現場預約','False',NULL,NULL,'2019-08-17 15:10:42'),(6905,38,'張筑威','2019-08-20 19:20:00','晚班',1,9,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 17:06:05'),(6906,40,'李宜芬','2019-08-20 19:30:00','晚班',1,10,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-14 17:06:56'),(6909,1123,'周姵吟','2019-08-20 17:00:00','午班',1,21,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-15 00:59:58'),(6963,1027,'黃琦雅','2019-08-20 16:00:00','午班',1,17,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 05:23:29'),(6932,713,'范煥松','2019-08-20 16:30:00','午班',1,20,'吳柏儒','網路初診預約','False',NULL,NULL,'2019-08-15 11:03:17'),(6967,545,'楊哲雄','2019-08-20 20:40:00','晚班',1,17,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 07:12:54'),(6964,1635,'劉玉蘭','2019-08-20 15:00:00','午班',1,7,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 06:41:32'),(6971,103,'羅喬凌','2019-08-20 16:30:00','午班',1,18,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 08:01:21'),(6978,41,'賴明輝','2019-08-20 21:00:00','晚班',1,19,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 11:46:41'),(6979,42,'賴洪賽英','2019-08-20 21:20:00','晚班',1,21,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-16 11:46:59'),(6998,822,'陳曉棋','2019-08-20 20:00:00','晚班',1,16,'薛如妤','網路預約','False',NULL,NULL,'2019-08-16 16:35:28'),(7023,189,'蔣郁芬','2019-08-20 16:30:00','午班',1,19,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-17 09:55:06'),(7024,719,'鍾芳美','2019-08-20 14:30:00','午班',1,4,'吳柏儒','網路初診預約','False',NULL,NULL,'2019-08-17 10:03:13'),(7057,150,'羅育軒','2019-08-20 22:00:00','晚班',1,25,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-18 12:14:09'),(7039,723,'許家豪','2019-08-20 18:30:00','晚班',1,4,'吳柏儒','網路初診預約','False',NULL,NULL,'2019-08-18 02:13:01'),(7045,1564,'高誠德','2019-08-20 21:30:00','晚班',1,22,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-18 06:34:57'),(7052,728,'吳聲廷','2019-08-20 15:30:00','午班',1,12,'吳柏儒','網路初診預約','False',NULL,NULL,'2019-08-18 09:36:20'),(7050,1862,'王冠中','2019-08-20 19:40:00','晚班',1,11,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-18 08:01:47'),(7055,1718,'楊琇惠','2019-08-20 21:40:00','晚班',1,23,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-18 11:46:15'),(7056,1626,'張譽瀚','2019-08-20 21:50:00','晚班',1,24,'吳柏儒','網路預約','False',NULL,NULL,'2019-08-18 11:46:31'),(7058,729,'林雅文','2019-08-20 19:30:00','晚班',1,12,'薛如妤','網路初診預約','False',NULL,NULL,'2019-08-18 13:12:51'),(7061,1850,'陳苾琳','2019-08-20 21:00:00','晚班',1,22,'薛如妤','網路預約','False',NULL,NULL,'2019-08-18 15:36:18'),(7074,1993,'邵暐浩','2019-08-20 09:00:00','早班',1,3,'陳敬智','現場預約','False',NULL,NULL,'2019-08-19 07:03:15'),(7094,190,'廖姵雯','2019-08-20 09:30:00','早班',1,7,'陳敬智','網路預約','False',NULL,NULL,'2019-08-19 13:55:25'),(7108,733,'吳家禎','2019-08-20 20:30:00','晚班',1,20,'薛如妤','網路初診預約','False',NULL,NULL,'2019-08-19 17:57:56');
/*!40000 ALTER TABLE `reserve` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-08-20  7:41:21
