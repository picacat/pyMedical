-- MariaDB dump 10.17  Distrib 10.4.11-MariaDB, for Linux (x86_64)
--
-- Host: localhost    Database: new
-- ------------------------------------------------------
-- Server version	10.4.11-MariaDB

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

LOCK TABLES `cases` WRITE;
/*!40000 ALTER TABLE `cases` DISABLE KEYS */;
INSERT INTO `cases` (`CaseKey`, `PatientKey`, `Name`, `CaseDate`, `StartDate`, `DoctorDate`, `ChargeDate`, `Visit`, `RegistTypex`, `RegistType`, `TourArea`, `TreatType`, `Injury`, `SpecialCode`, `Share`, `InsType`, `ApplyType`, `PharmacyType`, `Card`, `Continuance`, `XCard`, `Period`, `ChargePeriod`, `Room`, `MassageRoom`, `RegistNo`, `MassageNo`, `ChargeNo`, `DrugNo`, `YearlyNo1`, `YearlyNo2`, `YearlyNo3`, `Doctor`, `Pharmacist`, `Massager`, `Register`, `Casher`, `Cashier`, `ReceiptShare`, `SDiagShareFee`, `SDrugShareFee`, `Weight`, `Temperature`, `BPHigh`, `BPLow`, `Symptom`, `Tongue`, `Pulse`, `Equipment`, `DiseaseCode1`, `DiseaseName1`, `DiseaseCode2`, `DiseaseName2`, `DiseaseCode3`, `DiseaseName3`, `Distincts`, `Cure`, `Remark`, `Package1`, `PresDays1`, `Instruction1`, `Package2`, `PresDays2`, `Instruction2`, `Package3`, `PresDays3`, `Instruction3`, `Acupuncture1`, `Acupuncture2`, `EAcupuncture1`, `EAcupuncture2`, `Massage1`, `Massage2`, `Dislocate1`, `Dislocate2`, `Treatment`, `Position1`, `Position2`, `RegistFee`, `DiagFee`, `InterDrugFee`, `PharmacyFee`, `AcupunctureFee`, `MassageFee`, `DislocateFee`, `ExamFee`, `InsTotalFee`, `TreatShare`, `DiagShareFee`, `DrugShare`, `DrugShareFee`, `AgentFee`, `InsApplyFee`, `DepositFee`, `Refund`, `RefundFee`, `SDiagFee`, `SDrugFee`, `SHerbFee`, `SExpensiveFee`, `SAcupunctureFee`, `SMassageFee`, `SDislocateFee`, `SMaterial`, `SMaterialFee`, `SExamFee`, `SelfTotalFee`, `DiscountFee`, `DiscountRate`, `TotalFee`, `ReceiptFee`, `Debt`, `DebtFee`, `Status`, `DoctorDone`, `MassageDone`, `ChargeDone`, `DrugDone`, `DesignatedDoctor`, `DesignatedMassager`, `Reference`, `Note`, `Cert`, `Message`, `Security`, `TimeStamp`) VALUES (1,1,'黃從輝','2020-01-02 17:37:22',NULL,NULL,NULL,'初診',NULL,'一般門診',NULL,'內科','普通疾病',NULL,'基層醫療','健保','申報','不申報','D000',NULL,NULL,'午班',NULL,1,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'黃從輝',NULL,NULL,NULL,50,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'False','False','False','False','False','False','False','False',NULL,NULL,NULL,100,325,0,0,0,0,0,NULL,325,NULL,50,NULL,0,0,275,0,NULL,0,0,0,0,0,0,0,NULL,NULL,0,NULL,0,0,100,0,0,NULL,NULL,NULL,'False','False','False','False','False','False','False',NULL,NULL,NULL,'<DOCUMENT content=\"cshis\"><treat_data><registered_date/><seq_number/><clinic_id/><security_signature/><sam_id/><register_duplicated/><upload_time/><upload_type>2</upload_type><treat_after_check>1</treat_after_check><prescript_sign_time/></treat_data></DOCUMENT>','2020-01-02 09:37:41');
/*!40000 ALTER TABLE `cases` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-01-02 17:37:48
