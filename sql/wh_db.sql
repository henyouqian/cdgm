# ************************************************************
# Sequel Pro SQL dump
# Version 4004
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.29-0ubuntu0.12.04.2)
# Database: wh_db
# Generation Time: 2013-04-19 08:44:27 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table cardEntities
# ------------------------------------------------------------

DROP TABLE IF EXISTS `cardEntities`;

CREATE TABLE `cardEntities` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `protoId` int(10) unsigned NOT NULL,
  `ownerId` int(20) unsigned NOT NULL,
  `inPackage` tinyint(1) unsigned NOT NULL DEFAULT '1',
  `level` smallint(5) unsigned NOT NULL DEFAULT '1',
  `exp` int(10) unsigned NOT NULL DEFAULT '0',
  `skill1Id` smallint(5) unsigned NOT NULL DEFAULT '0',
  `skill1Level` tinyint(3) unsigned NOT NULL DEFAULT '1',
  `skill1Exp` smallint(5) unsigned NOT NULL DEFAULT '0',
  `skill2Id` smallint(5) unsigned NOT NULL DEFAULT '0',
  `skill2Level` tinyint(3) unsigned NOT NULL DEFAULT '1',
  `skill2Exp` smallint(5) unsigned NOT NULL DEFAULT '0',
  `skill3Id` smallint(5) unsigned NOT NULL DEFAULT '0',
  `skill3Level` tinyint(3) unsigned NOT NULL DEFAULT '1',
  `skill3Exp` smallint(5) unsigned NOT NULL DEFAULT '0',
  `hp` smallint(5) unsigned NOT NULL,
  `atk` smallint(5) unsigned NOT NULL,
  `def` smallint(5) unsigned NOT NULL,
  `wis` smallint(5) unsigned NOT NULL,
  `agi` smallint(5) unsigned NOT NULL,
  `hpCrystal` smallint(5) unsigned NOT NULL DEFAULT '0',
  `atkCrystal` smallint(5) unsigned NOT NULL DEFAULT '0',
  `defCrystal` smallint(5) unsigned NOT NULL DEFAULT '0',
  `wisCrystal` smallint(5) unsigned NOT NULL DEFAULT '0',
  `agiCrystal` smallint(5) unsigned NOT NULL DEFAULT '0',
  `hpExtra` smallint(5) unsigned NOT NULL DEFAULT '0',
  `atkExtra` smallint(5) unsigned NOT NULL DEFAULT '0',
  `defExtra` smallint(5) unsigned NOT NULL DEFAULT '0',
  `wisExtra` smallint(5) unsigned NOT NULL DEFAULT '0',
  `agiExtra` smallint(5) unsigned NOT NULL DEFAULT '0',
  `_newInsert` tinyint(1) unsigned NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `owner_id` (`ownerId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

LOCK TABLES `cardEntities` WRITE;
/*!40000 ALTER TABLE `cardEntities` DISABLE KEYS */;

INSERT INTO `cardEntities` (`id`, `protoId`, `ownerId`, `inPackage`, `level`, `exp`, `skill1Id`, `skill1Level`, `skill1Exp`, `skill2Id`, `skill2Level`, `skill2Exp`, `skill3Id`, `skill3Level`, `skill3Exp`, `hp`, `atk`, `def`, `wis`, `agi`, `hpCrystal`, `atkCrystal`, `defCrystal`, `wisCrystal`, `agiCrystal`, `hpExtra`, `atkExtra`, `defExtra`, `wisExtra`, `agiExtra`, `_newInsert`)
VALUES
	(119,117,12,1,21,7751,45,1,0,0,1,0,0,1,0,1927,1999,1623,2273,2257,0,0,0,0,0,0,0,0,0,0,0),
	(120,1,12,1,3,168,50,1,0,0,1,0,0,1,0,1151,910,1261,1305,1075,0,0,0,0,0,0,0,0,0,0,0),
	(127,118,19,1,1,0,34,1,0,0,1,0,0,1,0,1910,2060,1680,2420,2490,0,0,0,0,0,0,0,0,0,0,0),
	(128,1,19,1,11,1444,50,1,0,0,1,0,0,1,0,1558,1231,1707,1766,1459,0,0,0,0,0,0,0,0,0,0,0),
	(135,118,23,1,1,0,34,1,0,0,1,0,0,1,0,1910,2060,1680,2420,2490,0,0,0,0,0,0,0,0,0,0,0),
	(242,119,25,1,1,0,116,1,0,0,1,0,0,1,0,1180,890,1410,1320,1160,0,0,0,0,0,0,0,0,0,0,0),
	(251,10136,25,1,1,0,64,1,0,0,1,0,0,1,0,580,480,710,720,620,0,0,0,0,0,0,0,0,0,0,0),
	(252,94,25,1,1,0,46,1,0,0,1,0,0,1,0,890,1020,910,880,950,0,0,0,0,0,0,0,0,0,0,0),
	(253,20267,25,1,1,0,88,1,0,0,1,0,0,1,0,870,1110,740,1120,850,0,0,0,0,0,0,0,0,0,0,0),
	(254,10219,25,1,1,0,68,1,0,0,1,0,0,1,0,1080,1340,880,1320,1120,0,0,0,0,0,0,0,0,0,0,0),
	(255,118,28,1,1,0,34,1,0,0,1,0,0,1,0,1910,2060,1680,2420,2490,0,0,0,0,0,0,0,0,0,0,1),
	(332,10103,12,1,1,0,55,1,0,0,1,0,0,1,0,680,820,600,530,550,0,0,0,0,0,0,0,0,0,0,0),
	(333,118,30,1,1,0,34,1,0,0,1,0,0,1,0,1910,2060,1680,2420,2490,0,0,0,0,0,0,0,0,0,0,0),
	(337,68,12,0,1,0,45,1,0,0,1,0,0,1,0,900,1010,970,910,920,0,0,0,0,0,0,0,0,0,0,0),
	(338,7,12,1,1,0,54,1,0,0,1,0,0,1,0,440,360,500,490,420,0,0,0,0,0,0,0,0,0,0,0),
	(339,117,31,1,1,0,45,1,0,0,1,0,0,1,0,980,1020,830,1160,1150,0,0,0,0,0,0,0,0,0,0,0);

/*!40000 ALTER TABLE `cardEntities` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table playerInfos
# ------------------------------------------------------------

DROP TABLE IF EXISTS `playerInfos`;

CREATE TABLE `playerInfos` (
  `userId` int(10) unsigned NOT NULL,
  `name` varchar(40) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `whCoin` int(10) unsigned NOT NULL DEFAULT '0',
  `warLord` bigint(20) unsigned NOT NULL COMMENT 'war lord card entity id',
  `money` int(10) unsigned NOT NULL DEFAULT '1000',
  `inZoneId` smallint(5) unsigned NOT NULL,
  `lastZoneId` smallint(5) unsigned NOT NULL,
  `maxCardNum` tinyint(5) unsigned NOT NULL,
  `xp` smallint(5) unsigned NOT NULL,
  `maxXp` smallint(5) unsigned NOT NULL,
  `lastXpTime` timestamp NULL DEFAULT NULL,
  `ap` smallint(5) unsigned NOT NULL,
  `maxAp` smallint(5) unsigned NOT NULL,
  `lastApTime` timestamp NULL DEFAULT NULL,
  `lastFormation` smallint(5) unsigned NOT NULL DEFAULT '1',
  `currentBand` tinyint(3) unsigned DEFAULT '0',
  `zoneCache` text,
  `items` text NOT NULL,
  `bands` text NOT NULL,
  `wagonGeneral` text NOT NULL,
  `wagonTemp` text NOT NULL,
  `wagonSocial` text NOT NULL,
  `pvpStrength` int(10) unsigned NOT NULL DEFAULT '0',
  `pvpWinNum` tinyint(3) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`userId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `playerInfos` WRITE;
/*!40000 ALTER TABLE `playerInfos` DISABLE KEYS */;

INSERT INTO `playerInfos` (`userId`, `name`, `whCoin`, `warLord`, `money`, `inZoneId`, `lastZoneId`, `maxCardNum`, `xp`, `maxXp`, `lastXpTime`, `ap`, `maxAp`, `lastApTime`, `lastFormation`, `currentBand`, `zoneCache`, `items`, `bands`, `wagonGeneral`, `wagonTemp`, `wagonSocial`, `pvpStrength`, `pvpWinNum`)
VALUES
	(12,'aa',1000,119,93100,0,10101,5,7,30,'2013-04-17 06:32:35',3,3,NULL,1,1,NULL,'{\"10\": 1, \"19\": 1, \"18\": 1, \"1\": 5, \"3\": 1, \"2\": 10, \"7\": 2965, \"8\": 50}','[{\"formation\": 1, \"members\": [null, 119, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 120, 119, null, null, null]}, {\"formation\": 1, \"members\": [null, 119, null, null, null, null]}]','[]','[[-68, 1, \"2013-04-17 09:14:10\", 337]]','[]',0,0),
	(19,'dd',1000,127,10000,0,1,40,30,30,NULL,3,3,NULL,1,0,NULL,'{\"1\": 5, \"2\": 10, \"7\":50, \"8\":50}','[{\"formation\": 1, \"members\": [null, 127, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 127, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 127, null, null, null, null]}]','[]','[]','[]',0,0),
	(23,'xx',0,135,10000,0,1,40,30,30,NULL,3,3,NULL,1,0,NULL,'{\"1\": 5, \"8\": 50, \"2\": 10, \"7\": 9850}','[{\"formation\": 1, \"members\": [null, 135, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 135, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 135, null, null, null, null]}]','[]','[]','[]',0,0),
	(25,'gg',0,242,10000,0,1,40,30,30,NULL,3,3,NULL,1,0,NULL,'{\"1\": 5, \"8\": 50, \"2\": 10, \"7\": 42}','[{\"formation\": 1, \"members\": [null, 242, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 242, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 242, null, null, null, null]}]','[]','[]','[]',0,0),
	(28,'ggg',0,255,10000,0,1,40,30,30,NULL,3,3,NULL,1,0,NULL,'{\"8\": 50, \"1\": 5, \"2\": 10, \"7\": 50}','[{\"formation\": 1, \"members\": [null, 255, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 255, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 255, null, null, null, null]}]','[]','[]','[]',0,0),
	(30,'gggg',0,333,10000,0,1,40,30,30,NULL,3,3,NULL,1,0,NULL,'{\"8\": 50, \"1\": 5, \"2\": 10, \"7\": 50}','[{\"formation\": 1, \"members\": [null, 333, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 333, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 333, null, null, null, null]}]','[]','[]','[]',0,0),
	(31,'testaa',0,339,10000,1,1,40,30,30,NULL,3,3,NULL,1,0,'{\"band\": {\"formation\": 1, \"members\": [null, [339, 980], null, null, null, null]}, \"objs\": {\"29,45\": -10102, \"29,18\": -10102, \"29,36\": 4, \"29,42\": -10103, \"29,21\": -10102}, \"goldCase\": 0, \"goalPos\": {\"y\": 6, \"x\": 29}, \"monGrpId\": -1, \"currPos\": {\"y\": 54, \"x\": 29}, \"startPos\": {\"y\": 54, \"x\": 29}, \"redCase\": 0, \"zoneId\": 1}','{\"8\": 50, \"1\": 5, \"2\": 10, \"7\": 50}','[{\"formation\": 1, \"members\": [null, 339, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 339, null, null, null, null]}, {\"formation\": 1, \"members\": [null, 339, null, null, null, null]}]','[]','[]','[]',0,0);

/*!40000 ALTER TABLE `playerInfos` ENABLE KEYS */;
UNLOCK TABLES;



--
-- Dumping routines (PROCEDURE) for database 'wh_db'
--
DELIMITER ;;

# Dump of PROCEDURE get_new_cards
# ------------------------------------------------------------

/*!50003 DROP PROCEDURE IF EXISTS `get_new_cards` */;;
/*!50003 SET SESSION SQL_MODE=""*/;;
/*!50003 CREATE*/ /*!50020 DEFINER=`root`@`localhost`*/ /*!50003 PROCEDURE `get_new_cards`(IN user_id BIGINT, IN col_list VARCHAR(512))
BEGIN
    SET @sql = CONCAT("SELECT ", col_list, " FROM cardEntities WHERE ownerId = ", user_id, " AND _newInsert = 1;");
    PREPARE stmt from @sql;
    execute stmt;

    UPDATE cardEntities SET _newInsert = 0 WHERE ownerId = user_id AND _newInsert = 1; 
END */;;

/*!50003 SET SESSION SQL_MODE=@OLD_SQL_MODE */;;
DELIMITER ;

/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
