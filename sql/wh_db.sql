# ************************************************************
# Sequel Pro SQL dump
# Version 4004
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.29-0ubuntu0.12.04.2)
# Database: wh_db
# Generation Time: 2013-04-02 11:25:30 +0000
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
  `cardId` int(10) unsigned NOT NULL,
  `ownerId` int(20) unsigned NOT NULL,
  `level` smallint(5) unsigned NOT NULL DEFAULT '1',
  `exp` int(10) unsigned NOT NULL DEFAULT '0',
  `skillLevel` tinyint(3) unsigned NOT NULL DEFAULT '1',
  `skillExp` smallint(5) unsigned NOT NULL DEFAULT '0',
  `hp` smallint(5) unsigned NOT NULL,
  `atk` smallint(5) unsigned NOT NULL,
  `def` smallint(5) unsigned NOT NULL,
  `wis` smallint(5) unsigned NOT NULL,
  `agi` smallint(5) unsigned NOT NULL,
  `addSkill1` tinyint(3) unsigned NOT NULL DEFAULT '0',
  `addSkill2` tinyint(3) unsigned NOT NULL DEFAULT '0',
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
  PRIMARY KEY (`id`),
  KEY `owner_id` (`ownerId`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

LOCK TABLES `cardEntities` WRITE;
/*!40000 ALTER TABLE `cardEntities` DISABLE KEYS */;

INSERT INTO `cardEntities` (`id`, `cardId`, `ownerId`, `level`, `exp`, `skillLevel`, `skillExp`, `hp`, `atk`, `def`, `wis`, `agi`, `addSkill1`, `addSkill2`, `hpCrystal`, `atkCrystal`, `defCrystal`, `wisCrystal`, `agiCrystal`, `hpExtra`, `atkExtra`, `defExtra`, `wisExtra`, `agiExtra`)
VALUES
	(63,117,12,1,0,1,0,980,1020,830,1160,1150,0,0,0,0,0,0,0,0,0,0,0,0),
	(64,117,69,17,5878,1,0,1748,1814,1473,2062,2047,0,0,0,0,0,0,0,0,0,0,0,0);

/*!40000 ALTER TABLE `cardEntities` ENABLE KEYS */;
UNLOCK TABLES;


# Dump of table playerInfos
# ------------------------------------------------------------

DROP TABLE IF EXISTS `playerInfos`;

CREATE TABLE `playerInfos` (
  `userId` int(10) unsigned NOT NULL,
  `name` varchar(40) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `warLord` bigint(20) unsigned NOT NULL COMMENT 'war lord card entity id',
  `gold` int(10) unsigned NOT NULL DEFAULT '1000',
  `isInZone` tinyint(1) NOT NULL,
  `lastZoneId` smallint(5) unsigned NOT NULL,
  `xp` smallint(5) unsigned NOT NULL,
  `maxXp` smallint(5) unsigned NOT NULL,
  `lastXpTime` timestamp NULL DEFAULT NULL,
  `ap` smallint(5) unsigned NOT NULL,
  `maxAp` smallint(5) unsigned NOT NULL,
  `lastApTime` timestamp NULL DEFAULT NULL,
  `silverCoin` int(11) NOT NULL,
  `bronzeCoin` int(11) NOT NULL,
  `lastFormation` smallint(5) unsigned NOT NULL DEFAULT '1',
  `zoneCache` text,
  `items` text,
  `bands` text,
  PRIMARY KEY (`userId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `playerInfos` WRITE;
/*!40000 ALTER TABLE `playerInfos` DISABLE KEYS */;

INSERT INTO `playerInfos` (`userId`, `name`, `warLord`, `gold`, `isInZone`, `lastZoneId`, `xp`, `maxXp`, `lastXpTime`, `ap`, `maxAp`, `lastApTime`, `silverCoin`, `bronzeCoin`, `lastFormation`, `zoneCache`, `items`, `bands`)
VALUES
	(12,'aa',63,1000,0,0,30,30,NULL,3,3,NULL,2,5,1,'{\"goldCase\": 0, \"objs\": {\"26,19\": -2, \"50,16\": 3, \"20,37\": 3, \"29,28\": -2, \"47,16\": 4, \"44,16\": 10000, \"14,28\": 1, \"14,29\": 1, \"14,27\": 2, \"14,25\": -2, \"14,22\": -1, \"32,28\": -2, \"41,16\": -2, \"14,31\": 2, \"35,25\": 0, \"26,25\": -1, \"26,22\": 10000, \"11,28\": 1, \"26,28\": -1, \"14,19\": -2, \"23,19\": 0, \"14,34\": -1, \"14,37\": 1, \"23,37\": -2, \"27,28\": 1, \"38,16\": 10000, \"35,16\": 10000, \"17,37\": 2, \"17,19\": 0, \"26,37\": -2}, \"goalPos\": {\"y\": 16, \"x\": 53}, \"band\": [1, null, [63, 980], null, null, null, null], \"monGrpId\": 1, \"currPos\": {\"y\": 28, \"x\": 8}, \"startPos\": {\"y\": 28, \"x\": 8}, \"redCase\": 0, \"zoneId\": 50101}','{\"1\": 5, \"2\": 10}','[[1, null, 63, null, null, null, null], [1, null, 63, null, null, null, null], [1, null, 63, null, null, null, null]]'),
	(69,'aaaa',64,1000,0,0,23,30,'2013-04-01 10:27:57',3,3,NULL,2,5,1,'{\"band\": [1, null, [64, 980], null, null, null, null], \"objs\": {\"26,19\": -1, \"50,16\": 0, \"20,37\": -2, \"29,28\": -2, \"47,16\": 1, \"44,16\": -2, \"14,28\": -1, \"14,29\": 0, \"14,27\": 1, \"14,25\": -1, \"32,28\": -2, \"35,28\": -2, \"35,22\": -2, \"26,25\": -2, \"26,22\": 10000, \"11,28\": 3, \"41,16\": 4, \"23,19\": -2, \"14,37\": -2, \"14,31\": -1, \"27,28\": 0, \"38,16\": -1, \"35,16\": -1, \"17,37\": -1, \"26,31\": 4, \"26,37\": -2, \"20,19\": 1}, \"goldCase\": 0, \"goalPos\": {\"y\": 16, \"x\": 53}, \"monGrpId\": 1, \"currPos\": {\"y\": 28, \"x\": 8}, \"startPos\": {\"y\": 28, \"x\": 8}, \"redCase\": 0, \"zoneId\": 50101}','{\"1\": 5, \"2\": 10}','[[1, null, 64, null, null, null, null], [1, null, 64, null, null, null, null], [1, null, 64, null, null, null, null]]');

/*!40000 ALTER TABLE `playerInfos` ENABLE KEYS */;
UNLOCK TABLES;



/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
