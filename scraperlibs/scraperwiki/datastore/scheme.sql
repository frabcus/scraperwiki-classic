DROP TABLE IF EXISTS `items`;
CREATE TABLE IF NOT EXISTS `items` (
  `item_id`         bigint(20)      NOT NULL,
  `unique_hash`     varchar(32)     NOT NULL,
  `scraper_id`      varchar(100)    NOT NULL,
  `date`            datetime        NULL,
  `latlng`          varchar(100)    NULL,
  `date_scraped` datetime           NULL,
  KEY `item_id` (`item_id`,`unique_hash`,`scraper_id`,`date`,`latlng`)
) ENGINE=MyISAM;

-- Changes:
-- 1:
-- alter table `items` add column `date_scraped` datetime NULL;
-- 2:
-- new kv32 table

DROP TABLE IF EXISTS `kv`;
CREATE TABLE IF NOT EXISTS `kv` (
  `item_id`     bigint(20)  NOT NULL,
  `key`         text        NOT NULL,
  `value`       longtext    NOT NULL,
  KEY `item_id` (`item_id`)
) ENGINE=MyISAM;

DROP TABLE IF EXISTS `kv32`;
CREATE TABLE IF NOT EXISTS `kv32` (
  `item_id`     bigint(20)  NOT NULL,
  `key`         varchar(32) NOT NULL,
  `value`       varchar(32) NOT NULL,
  KEY `item_id` (`item_id`)
) ENGINE=MyISAM;

DROP TABLE IF EXISTS `sequences`;
CREATE TABLE IF NOT EXISTS `sequences` (
  `id` bigint NOT NULL
  ) ENGINE=MyISAM;



