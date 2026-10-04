
CREATE TABLE IF NOT EXISTS `game_save` (
    `game_id` VARCHAR(40) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
    `save_name` VARCHAR(40) CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
    `state_json` LONGTEXT CHARACTER SET latin1 COLLATE latin1_swedish_ci NOT NULL,
    `saved_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`game_id`),
    UNIQUE KEY `uq_game_save_name` (`save_name`),
    CONSTRAINT `game_save_game_fk`
        FOREIGN KEY (`game_id`) REFERENCES `game` (`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;