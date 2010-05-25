
DROP TABLE IF EXISTS `items`;
CREATE TABLE IF NOT EXISTS `items` (
  `item_id`         bigint(20)      NOT NULL,        -- should this an auto_increment? 
  `unique_hash`     varchar(32)     NOT NULL,        -- this needs deleting
  `scraper_id`      varchar(100)    NOT NULL,
--  `run_id`          varchar(255)    NOT NULL,
--  `deleted_run_id`  varchar(255)    NULL,          -- if not NULL then this entry is deleted.  the run_id allows the deletion to be rolled-back
  `date`            datetime        NULL,            -- reconsider this one
  `latlng`          varchar(100)    NULL,            -- this will be converted to fancy object like Point for filtering by distance (see ScraperManager.data_dictlist)
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


DROP TABLE IF EXISTS `pages`;
CREATE TABLE IF NOT EXISTS `pages` (
  `scraper_id`      varchar(100)    NOT NULL,
  `date_saved`      datetime        NULL,
  `run_id`          varchar(255)    NOT NULL,
  `tag`             text            NULL,
  `name`            text            NULL,
  `text`            longtext        NOT NULL
  -- KEY? how to add unique(scraper_id, name)?
) ENGINE=MyISAM;  

-- global persistant variables can be implemented by (tag="variable", name="variablename", text="variablevalue")

DROP TABLE IF EXISTS `postcode_lookup`;
CREATE TABLE postcode_lookup (
    postcode varchar(10) NOT NULL,
    location POINT NOT NULL,
    country_code CHAR(2) NOT NULL
) ENGINE=MyISAM;

ALTER TABLE `postcode_lookup` ADD UNIQUE INDEX postcode_unique(`postcode`),
 ADD INDEX country_code(`country_code`),
 ADD INDEX postcode(`postcode`);
