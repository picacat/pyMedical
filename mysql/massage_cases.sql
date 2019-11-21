
# 養生館病歷資料檔  2019.11.19

CREATE TABLE IF NOT EXISTS massage_cases
(
    MassageCaseKey  INT AUTO_INCREMENT NOT NULL,	# 病歷序號
    CustomerKey	    INT NOT NULL,		# 顧客編號
    Name	        VARCHAR(20),		# 病患姓名 (Option: 有名填名, 無名填自購藥)
    CaseDate        DATETIME NOT NULL,  # 消費日期
    FinishDate      DATETIME NOT NULL,	# 結束日期
    TreatType	    VARCHAR(10),        # 就醫類別: 養生館
    InsType	        VARCHAR(04),	    # 保險類別: 自費
    Period 	        VARCHAR(04),        # 班別: 早班, 午班, 晚班
    Massager	    VARCHAR(10),	    # 推拿師父姓名
    Register	    VARCHAR(10),	    # 掛號員姓名
    Cashier	        VARCHAR(10),	    # 收費員姓名
    Remark	        BLOB,               # 備註
    DesignatedMassager ENUM("False", "True") NOT NULL,  # 指定推拿師父


    SelfTotalFee	INT,	            # 自費合計,不含掛號費,欠卡費,還卡費
    DiscountFee	    INT,	            # 減免金額
    TotalFee	    INT,	            # 應收金額 (不含掛號費, 負擔金額)
    ReceiptFee	    INT,	            # 門診當天實收金額; 門診當日欠款金額=應收-實收(Virtual 顯示)
    DebtFee		    INT,	            # 尚欠金額(欠款餘額); 還款時, 同時更新

    TimeStamp	TIMESTAMP,	        # 上次異動日期

    PRIMARY KEY(MassageCaseKey),
    INDEX(CustomerKey, CaseDate)
) CHARACTER SET utf8;


