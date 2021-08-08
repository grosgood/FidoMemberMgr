--- Alter the Journal table to (1) index Subject, MemberID and ---
--- Comment fields and, (2) employ the InnoDB engine ---

ALTER TABLE Journal MODIFY `Subject` ENUM ('Address', 'Correspondence', 'Deletion', 'Dues', 'EMail', 'Identity', 'Initial', 'Mailing', 'Pet', 'Preference', 'Remark', 'Telephone') NOT NULL DEFAULT 'Remark';
ALTER TABLE Journal ADD INDEX SubjectIndex (`Subject`);
ALTER TABLE Journal ADD INDEX CommentIndex (`Comment`(24));
ALTER TABLE Journal ENGINE='InnoDB';
