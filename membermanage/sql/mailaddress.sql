--- Alter the MailAddress Model to (1) index street addresses and zip codes, and (2) use InnoDB engine ---

ALTER TABLE MailAddress ADD INDEX StreetAddress (`Street`(15));
ALTER TABLE MailAddress ADD INDEX ZIPKey (`Postcode`, `PostcodeExt`);
ALTER TABLE MailAddress ENGINE='InnoDB';
