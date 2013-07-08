# ************************************************************
# Sequel Pro SQL dump
# Version 4096
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 127.0.0.1 (MySQL 5.5.31-0ubuntu0.12.04.2)
# Database: wh_db
# Generation Time: 2013-07-08 08:05:23 +0000
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



# Dump of table playerInfos
# ------------------------------------------------------------

DROP TABLE IF EXISTS `playerInfos`;

CREATE TABLE `playerInfos` (
  `userId` int(10) unsigned NOT NULL,
  `name` varchar(40) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `whCoin` int(10) unsigned NOT NULL DEFAULT '0',
  `warLord` bigint(20) unsigned NOT NULL COMMENT 'war lord card entity id',
  `money` int(10) unsigned NOT NULL DEFAULT '1000',
  `inZoneId` int(10) unsigned NOT NULL,
  `lastZoneId` int(10) unsigned NOT NULL,
  `maxCardNum` tinyint(5) unsigned NOT NULL,
  `maxTradeNum` tinyint(5) unsigned NOT NULL,
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
  `pvpScore` int(10) unsigned NOT NULL DEFAULT '0',
  `pvpWinNum` tinyint(3) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`userId`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;



# Dump of table wagons
# ------------------------------------------------------------

DROP TABLE IF EXISTS `wagons`;

CREATE TABLE `wagons` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `type` tinyint(4) unsigned NOT NULL COMMENT '0:general 1:temp 2:social',
  `count` int(11) NOT NULL,
  `cardEntity` bigint(11) DEFAULT NULL,
  `cardProto` int(11) DEFAULT NULL,
  `itemId` bigint(11) DEFAULT NULL,
  `descText` varchar(40) NOT NULL DEFAULT '',
  `time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;




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
