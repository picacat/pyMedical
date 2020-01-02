
# 養生館病歷收費檔    2019.11.21

CREATE TABLE IF NOT EXISTS massage_payment
(
    MassagePaymentKey	    INT AUTO_INCREMENT NOT NULL,    # 處方序號
    MassageCaseKey	        INT NOT NULL,	                # 病歷序號
    PaymentType             VARCHAR(40),                    # 付款方式
    Amount        	        Decimal(10, 2) DEFAULT 0,       # 付款金額
    Remark                  VARCHAR(100),                   # 備註

    TimeStamp	            TIMESTAMP,	                    # 上次異動日期

    PRIMARY KEY(MassagePaymentKey),
    INDEX(MassageCaseKey, PaymentType)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;


