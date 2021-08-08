--- Alter the Member Model to (1) span a 'MemberName index across two fields, (2) zerofill the MemberID field and, (3)employ the InnoDB engine ---

ALTER TABLE Member ADD INDEX MemberName (`Last`(7), `First`(5));
ALTER TABLE Member MODIFY `MemberID` SMALLINT(5) UNSIGNED ZEROFILL NOT NULL;
ALTER TABLE Member ENGINE='InnoDB';
