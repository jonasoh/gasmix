-- :name update_db_version :affected
DELETE FROM meta
INSERT INTO meta VALUES (:created, :dbver)
