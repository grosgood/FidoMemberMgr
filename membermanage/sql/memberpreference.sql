--- Alter the MemberPreference table to (1) establish a set ---
--- of preference choices, and (2) employ the InnoDB engine ---

ALTER TABLE MemberPreference MODIFY `Preferences` SET('MailNewsletter', 'BroadcastEmail') NOT NULL DEFAULT 'BroadcastEmail';
ALTER TABLE MemberPreference ENGINE='InnoDB';
