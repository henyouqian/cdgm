# ************************************************************
# Sequel Pro SQL dump
# Version 4004
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 192.168.0.109 (MySQL 5.5.29-0ubuntu0.12.04.2)
# Database: wh_db
# Generation Time: 2013-03-12 07:15:54 +0000
# ************************************************************


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


# Dump of table card_entity
# ------------------------------------------------------------

DROP TABLE IF EXISTS `card_entity`;

CREATE TABLE `card_entity` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `proto_id` int(10) unsigned NOT NULL,
  `owner_id` bigint(20) NOT NULL,
  `level` smallint(5) unsigned NOT NULL,
  `exp` int(10) unsigned NOT NULL,
  `skill_level` tinyint(3) unsigned NOT NULL,
  `skill_exp` smallint(5) unsigned NOT NULL,
  `hp` int(11) NOT NULL,
  `atk` int(11) NOT NULL,
  `def` int(11) NOT NULL,
  `wis` int(11) NOT NULL,
  `agi` int(11) NOT NULL,
  `add_skill1` int(11) DEFAULT NULL,
  `add_skill2` int(11) DEFAULT NULL,
  `hp_add` int(11) DEFAULT NULL,
  `atk_add` int(11) DEFAULT NULL,
  `def_add` int(11) DEFAULT NULL,
  `wis_add` int(11) DEFAULT NULL,
  `agi_add` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table cards
# ------------------------------------------------------------

DROP TABLE IF EXISTS `cards`;

CREATE TABLE `cards` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(40) NOT NULL DEFAULT '',
  `comment` varchar(80) NOT NULL DEFAULT '',
  `rarity` tinyint(4) unsigned NOT NULL,
  `cardType` tinyint(3) unsigned NOT NULL,
  `battleExp` smallint(5) unsigned NOT NULL,
  `price` smallint(5) unsigned NOT NULL,
  `hasBossImage` tinyint(1) unsigned NOT NULL,
  `baseHp` smallint(5) unsigned NOT NULL,
  `baseAtk` smallint(5) unsigned NOT NULL,
  `baseDef` smallint(5) unsigned NOT NULL,
  `baseWis` smallint(5) unsigned NOT NULL,
  `baseAgi` smallint(5) unsigned NOT NULL,
  `maxHp` smallint(5) unsigned NOT NULL,
  `maxAtk` smallint(5) unsigned NOT NULL,
  `maxDef` smallint(5) unsigned NOT NULL,
  `maxWis` smallint(5) unsigned NOT NULL,
  `maxAgi` smallint(5) unsigned NOT NULL,
  `maxLevel` tinyint(3) unsigned NOT NULL,
  `growthType` tinyint(3) unsigned NOT NULL,
  `skillId1` tinyint(3) unsigned NOT NULL,
  `skillId2` tinyint(3) unsigned NOT NULL,
  `evolution` tinyint(3) unsigned NOT NULL,
  `maxEvolution` tinyint(4) unsigned NOT NULL,
  `canTrade` tinyint(1) unsigned NOT NULL,
  `materialExp` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



# Dump of table user_info
# ------------------------------------------------------------

DROP TABLE IF EXISTS `user_info`;

CREATE TABLE `user_info` (
  `id` bigint(20) unsigned NOT NULL,
  `name` varchar(40) CHARACTER SET utf8 NOT NULL DEFAULT '',
  `current_band_id` tinyint(3) unsigned NOT NULL,
  `is_in_map` tinyint(1) NOT NULL,
  `last_map_id` smallint(5) unsigned NOT NULL,
  `ap` smallint(5) unsigned NOT NULL,
  `max_ap` smallint(5) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `user_info` WRITE;
/*!40000 ALTER TABLE `user_info` DISABLE KEYS */;

INSERT INTO `user_info` (`id`, `name`, `current_band_id`, `is_in_map`, `last_map_id`, `ap`, `max_ap`)
VALUES
	(12,'aa',0,0,0,30,30);

/*!40000 ALTER TABLE `user_info` ENABLE KEYS */;
UNLOCK TABLES;



/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
