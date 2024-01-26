-- :name create_table_sensordata :affected
CREATE TABLE sensordata (id INTEGER PRIMARY KEY AUTOINCREMENT, read_time INT, reactor NUM, vol NUM, h2 NUM, co2 NUM, temp NUM, pressure NUM, humidity NUM, comment TEXT);
