CREATE TABLE `log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `stamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `scraperid` varchar(255) DEFAULT NULL,
  `runid` varchar(255) DEFAULT NULL,
  `pytime` varchar(31) DEFAULT NULL,
  `event` varchar(255) DEFAULT NULL,
  `arg1` text,
  `arg2` text,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;
