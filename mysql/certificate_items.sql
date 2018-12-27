
# 證明文件副檔  2018.12.27      診斷證明, 收費證明

CREATE TABLE IF NOT EXISTS certificate_items
(
    CertificateItemsKey	    INT AUTO_INCREMENT NOT NULL,  # 證明序號
    CertificateKey	        INT NOT NULL,	# 證明序號

    CaseKey	                INT NOT NULL,	# 病歷號
    CaseDate                DATETIME,       # 就醫日期

#------------------ 收費證明用 ---------------------------------------
    RegistFee	      INT,	    # 掛號費
    DiagFee	        INT,	    # 診察費
    InterDrugFee	  INT,	    # 內服藥費
    PharmacyFee	    INT,	    # 藥服費
    AcupunctureFee  INT,      # 針灸費 (電針費);  處置費(TreatFee) = 針灸費+傷科費+脫臼費
    MassageFee	    INT,	    # 傷科費
    DislocateFee	  INT,	    # 脫臼費    腦疾-照護費與檢查費(治療費)
    ExamFee	        INT,    	# 檢驗費
    InsApplyFee	    INT, 	    # 健保申請
    SDiagShareFee   INT,      # 實收門診負擔
    SDrugShareFee   INT,      # 實收藥品負擔

    SDiagFee	      INT,	    # 自費診察費
    SDrugFee	      INT,	    # 自費一般藥費: 單方+複方+外用藥
    SHerbFee	      INT,	    # 自費水藥費
    SExpensiveFee   INT,	    # 自費高貴藥費
    SAcupunctureFee INT,	    # 自費針灸費
    SMassageFee	    INT,      # 自費傷科費
    SDislocateFee   INT,  	  # 自費脫臼費
    SMaterialFee    INT,      # 自費材料費: 含診斷證明, 收費證明
    SExamFee	      INT,  	  # 自費檢驗費
    SMiscFee        INT,      # 自費其他

    SelfTotalFee	  INT,	    # 自費合計,不含掛號費,欠卡費,還卡費
    DiscountFee	    INT,	    # 減免金額
    TotalFee	      INT,	    # 應收金額 (不含掛號費, 負擔金額)
    ReceiptFee	    INT,	    # 門診當天實收金額; 門診當日欠款金額=應收-實收(Virtual 顯示)

    Remark      VarChar(200),   # 備註

    TimeStamp	TIMESTAMP,	    # 上次異動日期

    PRIMARY KEY(CertificateItemsKey),
    INDEX(CertificateKey, CaseKey)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;
