-- :name extract_data :many
SELECT * FROM sensordata WHERE read_time >= :start_timestamp AND read_time <= :end_timestamp
