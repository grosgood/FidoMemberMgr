--- Alter the DogTag Model to (2) index the `Tag` field and, (2)employ the InnoDB engine ---

ALTER TABLE DogTag MODIFY `Tag` INT(11) NOT NULL UNIQUE;
ALTER TABLE DogTag ADD INDEX PetIndex(`PetID`);
ALTER TABLE DogTag  ENGINE='InnoDB';
