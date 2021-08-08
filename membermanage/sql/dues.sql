--- Alter the Dues table to (1) establish an enumeration to classify --- 
--- pay types and, (2) employ the InnoDB engine ---

ALTER TABLE Dues MODIFY `PayType` ENUM ('New', 'Renew', 'Reinstate') NOT NULL DEFAULT 'New';
ALTER TABLE Dues ADD INDEX DateIndex (`PayDate`);
ALTER TABLE Dues ENGINE='InnoDB';
