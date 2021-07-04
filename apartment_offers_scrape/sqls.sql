USE `apartments`;

DROP TABLE IF EXISTS `apartments`.`offers`;

CREATE TABLE `apartments`.`offers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `surface` decimal(5,2) DEFAULT NULL,
  `num_rooms` tinyint(4) DEFAULT NULL,
  `market` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `buiding_type` varchar(40) COLLATE utf8_unicode_ci DEFAULT NULL,
  `year_built` smallint(6) DEFAULT NULL,
  `floor_num` tinyint(4) DEFAULT NULL,
  `num_building_floors` tinyint(4) DEFAULT NULL,
  `building_material` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `heating` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `rent` decimal(6,2) DEFAULT NULL,
  `windows` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `finishing_state` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ownership` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `available_from` date DEFAULT NULL,
  `link_adress` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `district` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `borough` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `street` varchar(60) COLLATE utf8_unicode_ci DEFAULT NULL,
  `offer_title` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `price` decimal(10,2) DEFAULT '0.00',
  `upload_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx1` (`district`,`surface`,`price`,`num_rooms`),
  KEY `idx_upload_date` (`upload_date`),
  KEY `idx_link_price` (`link_adress`,`price`)
) ENGINE=InnoDB AUTO_INCREMENT=1009 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


DROP TABLE IF EXISTS `apartments`.`offers_tmp`;

CREATE TABLE `apartments`.`offers_tmp` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `surface` decimal(5,2) DEFAULT NULL,
  `num_rooms` tinyint(4) DEFAULT NULL,
  `market` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `buiding_type` varchar(40) COLLATE utf8_unicode_ci DEFAULT NULL,
  `year_built` smallint(6) DEFAULT NULL,
  `floor_num` tinyint(4) DEFAULT NULL,
  `num_building_floors` tinyint(4) DEFAULT NULL,
  `building_material` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `heating` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `rent` decimal(6,2) DEFAULT NULL,
  `windows` varchar(20) COLLATE utf8_unicode_ci DEFAULT NULL,
  `finishing_state` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `ownership` varchar(50) COLLATE utf8_unicode_ci DEFAULT NULL,
  `available_from` date DEFAULT NULL,
  `link_adress` varchar(200) COLLATE utf8_unicode_ci NOT NULL,
  `district` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `borough` varchar(30) COLLATE utf8_unicode_ci DEFAULT NULL,
  `street` varchar(60) COLLATE utf8_unicode_ci DEFAULT NULL,
  `offer_title` varchar(100) COLLATE utf8_unicode_ci DEFAULT NULL,
  `price` decimal(10,2) DEFAULT '0.00',
  `upload_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_link_adress` (`link_adress`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


DROP PROCEDURE IF EXISTS `apartments`.`sp_process_offers`;

DELIMITER $$

CREATE PROCEDURE `apartments`.`sp_process_offers`()
BEGIN

INSERT INTO `apartments`.`offers`
	(`surface`, `num_rooms`, `market`, `buiding_type`, `year_built`, `floor_num`, 
	`num_building_floors`, `building_material`, `heating`, `rent`, `windows`, 
	`finishing_state`, `ownership`, `available_from`, `link_adress`, `district`, 
	`borough`, `street`, `offer_title`, `price`, `upload_date`)
SELECT 
    TMP.`surface`, TMP.`num_rooms`, TMP.`market`, TMP.`buiding_type`,
    TMP.`year_built`, TMP.`floor_num`, TMP.`num_building_floors`, TMP.`building_material`,
    TMP.`heating`, TMP.`rent`, TMP.`windows`, TMP.`finishing_state`,
    TMP.`ownership`, TMP.`available_from`, TMP.`link_adress`, TMP.`district`,
    TMP.`borough`, TMP.`street`, TMP.`offer_title`, TMP.`price`, TMP.`upload_date`
FROM 
	`apartments`.`offers_tmp` TMP, 
    `apartments`.`offers` OFF, 
    (SELECT `link_adress`, MAX(`upload_date`) AS upload_date FROM `apartments`.`offers` GROUP BY `link_adress`) UPL
WHERE 
	OFF.`upload_date` = UPL.`upload_date`
    AND OFF.`link_adress` = UPL.`link_adress`
	AND TMP.`link_adress` = OFF.`link_adress`
    AND OFF.`price` <> TMP.`price`
    
UNION 

SELECT 
    `surface`, `num_rooms`, `market`, `buiding_type`,
    `year_built`, `floor_num`, `num_building_floors`, `building_material`,
    `heating`, `rent`, `windows`, `finishing_state`,
    `ownership`, `available_from`, `link_adress`, `district`,
    `borough`, `street`, `offer_title`, `price`, `upload_date`
FROM 
	`apartments`.`offers_tmp` 
WHERE 
	`link_adress` NOT IN (SELECT DISTINCT `link_adress` FROM `apartments`.`offers`);

END $$
DELIMITER ;

