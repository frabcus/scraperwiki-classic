
DROP TABLE IF EXISTS `wikipediapages`;
CREATE TABLE IF NOT EXISTS `wikipediapages` (
  `title`         text        NOT NULL,
  `text`          longtext    NOT NULL,
  `ttag`          varchar(64) NULL
) ENGINE=MyISAM;




