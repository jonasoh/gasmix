-- :name insert_sensordata :affected
INSERT INTO sensordata VALUES (:read_time, :reactor, :vol, :h2, :co2, :temp, :pressure, :humidity, :comment)
