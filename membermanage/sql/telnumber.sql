--- Alter the TelNumber Model to (1) area, exchange and number, and (2) use InnoDB engine ---

ALTER TABLE TelNumber ADD INDEX TelIndex (`AreaCode`,`ExchCode`,`Number`);
ALTER TABLE TelNumber ENGINE='InnoDB';
