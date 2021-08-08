--- Alter the EMailAddress Model to (1) index name and domain fields, and (2) use InnoDB engine ---

ALTER TABLE EMailAddress ADD INDEX EName (`EMailName`(10));
ALTER TABLE EMailAddress ADD INDEX EDomain (`EMailDomain`(6));
ALTER TABLE EMailAddress ENGINE='InnoDB';
