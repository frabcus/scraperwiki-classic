
DROP TABLE IF EXISTS `items`;
CREATE TABLE IF NOT EXISTS `items` (
  `item_id`         bigint(20)      NOT NULL,        -- should this an auto_increment? 
  `unique_hash`     varchar(32)     NOT NULL,        -- this needs deleting
  `scraper_id`      varchar(100)    NOT NULL,
--  `run_id`          varchar(255)    NOT NULL,
--  `deleted_run_id`  varchar(255)    NULL,
  `date`            datetime        NULL,            -- reconsider this one
  `latlng`          varchar(100)    NULL,            -- this will be converted to fancy object like Point
  `date_scraped`    datetime        NULL,
  KEY `item_id` (`item_id`,`unique_hash`,`scraper_id`,`date`,`latlng`)
) ENGINE=MyISAM;


DROP TABLE IF EXISTS `kv`;
CREATE TABLE IF NOT EXISTS `kv` (
  `item_id`         bigint(20)      NOT NULL,
  `key`             text            NOT NULL,
  `value`           longtext        NOT NULL,
  KEY `item_id` (`item_id`)
) ENGINE=MyISAM;


-- There is only one of these, and it sequences the item_id
DROP TABLE IF EXISTS `sequences`;
CREATE TABLE IF NOT EXISTS `sequences` (
  `id` bigint NOT NULL
  ) ENGINE=MyISAM;


-- how to add unique(scraper_id, name)?
DROP TABLE IF EXISTS `pages`;
CREATE TABLE IF NOT EXISTS `pages` (
  `scraper_id`      varchar(100)    NOT NULL,
  `date_saved`      datetime        NULL,
  `tag`             text            NULL,
  `name`            text            NULL,
  `text`            longtext        NOT NULL
) ENGINE=MyISAM;  


-- key-value row of useful data stored against each scraper that persists between runs
DROP TABLE IF EXISTS `kvmeta`;
  `scraper_id`      varchar(100)    NOT NULL,
  `key`             text            NOT NULL,
  `value`           longtext        NOT NULL,
  `type`            varchar(50)     NOT NULL,
) ENGINE=MyISAM;

  