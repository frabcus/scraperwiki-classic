DROP TABLE IF EXISTS `items`;
CREATE TABLE IF NOT EXISTS `items` (
  `item_id` bigint(20) NOT NULL,
  `unique_hash` varchar(32) NOT NULL,
  `scraper_id` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `latlng` float NOT NULL,
  KEY `item_id` (`item_id`,`unique_hash`,`scraper_id`,`date`,`latlng`)
) ENGINE=MyISAM;


DROP TABLE IF EXISTS `kv`;
CREATE TABLE IF NOT EXISTS `kv` (
  `item_id` bigint(20) NOT NULL,
  `key` text NOT NULL,
  `value` longtext NOT NULL,
  KEY `item_id` (`item_id`)
) ENGINE=MyISAM;


DROP TABLE IF EXISTS `sequences`;
CREATE TABLE IF NOT EXISTS `sequences` (
  `id` bigint NOT NULL
  ) ENGINE=MyISAM;

