
# 證明文件	2018.12.21

CREATE TABLE IF NOT EXISTS certificate
(
    CertificateKey	    INT AUTO_INCREMENT NOT NULL,  # 證明序號
    CaseKey	            INT NOT NULL,	# 連結證明書收費病歷資料
    PatientKey	        INT NOT NULL,	# 系統號
    Name  	            VARCHAR(100),	# 病患姓名
    CertificateDate	    DATE,		    # 開立證明日期
    CertificateType	    VARCHAR(10),	# 證明類別: 診斷證明, 收費證明

    InsType	            VARCHAR(10),	# 收據(保險)類別: 全部, 健保, 健保負擔(收費證明用), 自費
    StartDate	        DATE,		    # 病歷統計開始日期
    EndDate	            DATE,		    # 病歷統計結束日期

    Diagnosis           TEXT,           # 診斷證明-診斷
    DoctorComment       TEXT,           # 診斷證明-醫師囑言
    CertificateFee      INT,

    TimeStamp	TIMESTAMP,	    # 上次異動日期

    PRIMARY KEY(CertificateKey),
    INDEX(CaseKey, PatientKey, CertificateDate)
) ENGINE = MyISAM DEFAULT CHARACTER SET = utf8;


