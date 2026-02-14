CREATE TABLE IF NOT EXISTS `languages` (
  `language_id`   VARCHAR(2),
  `word`          VARCHAR(255),
  `weight`        NUMERIC,
  CONSTRAINT `pk_languages` PRIMARY KEY (`language_id`, `word`)
);