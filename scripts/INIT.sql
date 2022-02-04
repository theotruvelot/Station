#------------------------------------------------------------
#        Script MySQL.
#------------------------------------------------------------


#------------------------------------------------------------
# Table: SONDES
#------------------------------------------------------------

CREATE TABLE SONDES(
        SON_ID          Int  Auto_increment  NOT NULL ,
        SON_STATUS      Char (1) NOT NULL ,
        SON_LAST_MESURE TimeStamp NOT NULL ,
        SON_KEY         Varchar (10) NOT NULL ,
        SON_LOCATION    Varchar (40) NOT NULL
	,CONSTRAINT SONDES_PK PRIMARY KEY (SON_ID)
)ENGINE=InnoDB;


#------------------------------------------------------------
# Table: MESURES
#------------------------------------------------------------

CREATE TABLE MESURES(
        MES_ID   Int  Auto_increment  NOT NULL ,
        MES_DATE TimeStamp NOT NULL ,
        MES_TEMP Varchar (4) NOT NULL ,
        SON_ID   Int NOT NULL
	,CONSTRAINT MESURES_PK PRIMARY KEY (MES_ID)

	,CONSTRAINT MESURES_SONDES_FK FOREIGN KEY (SON_ID) REFERENCES SONDES(SON_ID)
)ENGINE=InnoDB;


#------------------------------------------------------------
# Table: USERS
#------------------------------------------------------------

CREATE TABLE USERS(
        USE_ID     Int  Auto_increment  NOT NULL ,
        USE_ADMIN  Char (1) NOT NULL ,
        USE_NOM    Varchar (40) NOT NULL ,
        USE_PRENOM Varchar (40) NOT NULL ,
        USE_EMAIL  Varchar (50) NOT NULL ,
        USE_PASS   Varchar (50) NOT NULL
	,CONSTRAINT USERS_PK PRIMARY KEY (USE_ID)
)ENGINE=InnoDB;

