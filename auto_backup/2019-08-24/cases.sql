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
-- Dumping data for table `cases`
--
-- WHERE:  CaseDate BETWEEN '2019-08-24 00:00:00' AND '2019-08-24 23:59:59'

LOCK TABLES `cases` WRITE;
/*!40000 ALTER TABLE `cases` DISABLE KEYS */;
INSERT INTO `cases` (`CaseKey`, `PatientKey`, `Name`, `CaseDate`, `StartDate`, `DoctorDate`, `ChargeDate`, `Visit`, `RegistTypex`, `RegistType`, `TreatType`, `Injury`, `SpecialCode`, `Share`, `InsType`, `ApplyType`, `PharmacyType`, `Card`, `Continuance`, `XCard`, `Period`, `ChargePeriod`, `Room`, `MassageRoom`, `RegistNo`, `MassageNo`, `ChargeNo`, `DrugNo`, `YearlyNo1`, `YearlyNo2`, `YearlyNo3`, `Doctor`, `Pharmacist`, `Massager`, `Register`, `Casher`, `Cashier`, `ReceiptShare`, `SDiagShareFee`, `SDrugShareFee`, `Weight`, `Temperature`, `BPHigh`, `BPLow`, `Symptom`, `Tongue`, `Pulse`, `Equipment`, `DiseaseCode1`, `DiseaseName1`, `DiseaseCode2`, `DiseaseName2`, `DiseaseCode3`, `DiseaseName3`, `Distincts`, `Cure`, `Remark`, `Package1`, `PresDays1`, `Instruction1`, `Package2`, `PresDays2`, `Instruction2`, `Package3`, `PresDays3`, `Instruction3`, `Acupuncture1`, `Acupuncture2`, `EAcupuncture1`, `EAcupuncture2`, `Massage1`, `Massage2`, `Dislocate1`, `Dislocate2`, `Treatment`, `Position1`, `Position2`, `RegistFee`, `DiagFee`, `InterDrugFee`, `PharmacyFee`, `AcupunctureFee`, `MassageFee`, `DislocateFee`, `ExamFee`, `InsTotalFee`, `TreatShare`, `DiagShareFee`, `DrugShare`, `DrugShareFee`, `AgentFee`, `InsApplyFee`, `DepositFee`, `Refund`, `RefundFee`, `SDiagFee`, `SDrugFee`, `SHerbFee`, `SExpensiveFee`, `SAcupunctureFee`, `SMassageFee`, `SDislocateFee`, `SMaterial`, `SMaterialFee`, `SExamFee`, `SelfTotalFee`, `DiscountFee`, `DiscountRate`, `TotalFee`, `ReceiptFee`, `Debt`, `DebtFee`, `Status`, `DoctorDone`, `MassageDone`, `ChargeDone`, `DrugDone`, `Reference`, `Note`, `Cert`, `Message`, `Security`, `TimeStamp`) VALUES (802749,88,'林明濤','2019-08-24 13:04:15',NULL,'2019-08-24 13:05:30','2019-08-24 13:05:46','複診',NULL,'一般門診','內科','普通疾病',NULL,'基層醫療','健保','申報','申報','D010',NULL,NULL,'午班','午班',5,NULL,151,NULL,NULL,NULL,NULL,NULL,NULL,'黃英傑',NULL,NULL,'黃英傑',NULL,'黃英傑',NULL,0,40,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'J00','急性鼻咽炎（感冒）',NULL,NULL,NULL,NULL,NULL,NULL,NULL,3,7,'飯後',NULL,NULL,NULL,NULL,NULL,NULL,'False','False','False','False','False','False','False','False',NULL,NULL,NULL,0,325,245,13,0,0,0,NULL,583,NULL,50,NULL,40,0,493,0,NULL,0,0,0,0,0,0,0,NULL,NULL,0,NULL,0,0,100,0,0,NULL,NULL,NULL,'True','False','True','False','False',NULL,NULL,NULL,'<DOCUMENT content=\"cshis\"><treat_data><registered_date/><seq_number/><clinic_id/><security_signature/><sam_id/><register_duplicated/><upload_time/><upload_type>2</upload_type><treat_after_check>1</treat_after_check><prescript_sign_time/></treat_data></DOCUMENT>','2019-08-24 05:05:46');
/*!40000 ALTER TABLE `cases` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2019-08-24 13:30:01
