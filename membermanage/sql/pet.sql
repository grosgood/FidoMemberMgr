--- Alter the Pet Model to (1) set the ID type to be compatible with fidomembers, (2) index the `Name` field and, (3)employ the InnoDB engine ---

ALTER TABLE Pet ADD INDEX PetIndex(`Name`(5));
ALTER TABLE Pet ENGINE='InnoDB';
