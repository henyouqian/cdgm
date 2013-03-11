# ************************************************************
# Sequel Pro SQL dump
# Version 4004
#
# http://www.sequelpro.com/
# http://code.google.com/p/sequel-pro/
#
# Host: 192.168.2.102 (MySQL 5.5.29-0ubuntu0.12.04.2)
# Database: wh_db
# Generation Time: 2013-03-11 14:12:33 +0000
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



# Dump of table card_proto
# ------------------------------------------------------------

DROP TABLE IF EXISTS `card_proto`;

CREATE TABLE `card_proto` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(11) NOT NULL DEFAULT '',
  `commet` int(11) DEFAULT NULL,
  `rarity` int(11) DEFAULT NULL,
  `card_type` int(11) DEFAULT NULL,
  `battle_exp` int(11) DEFAULT NULL,
  `price` int(11) DEFAULT NULL,
  `has_boss_image` int(11) DEFAULT NULL,
  `base_hp` int(11) DEFAULT NULL,
  `base_atk` int(11) DEFAULT NULL,
  `base_def` int(11) DEFAULT NULL,
  `base_wis` int(11) DEFAULT NULL,
  `base_agi` int(11) DEFAULT NULL,
  `max_hp` int(11) DEFAULT NULL,
  `max_atk` int(11) DEFAULT NULL,
  `max_def` int(11) DEFAULT NULL,
  `max_wis` int(11) DEFAULT NULL,
  `max_agi` int(11) DEFAULT NULL,
  `max_level` int(11) DEFAULT NULL,
  `grow_type` int(11) DEFAULT NULL,
  `skill_id1` int(11) DEFAULT NULL,
  `skill_id2` int(11) DEFAULT NULL,
  `evolution` int(11) DEFAULT NULL,
  `max_evolution` int(11) DEFAULT NULL,
  `can_trade` int(11) DEFAULT NULL,
  `material_exp` int(11) DEFAULT NULL,
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
