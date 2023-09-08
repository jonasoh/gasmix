# Database structure

```
CREATE TABLE sensordata 
    (time REAL PRIMARY KEY, reactor NUM, vol NUM, h2 NUM, co2 NUM, temp NUM, pressure NUM, comment TEXT);
```
We store the sensor data here. Time is Unix timestamp.

```

CREATE TABLE meta
    (created REAL, version INT);

Meta table to indicate database integrity and support versioning.


