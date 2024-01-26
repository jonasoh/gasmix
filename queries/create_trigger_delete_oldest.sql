-- :name create_trigger_delete_oldest :affected
-- Create a trigger to delete the oldest records when a new one is added
-- 4730400 means 3 years of data, if three entries are logged every minute
CREATE TRIGGER delete_oldest
AFTER INSERT ON sensordata
BEGIN
    DELETE FROM sensordata
    WHERE id <= (SELECT MAX(id) - 4730400 FROM sensordata);
END;
