@echo off
SET KAFKA_PATH=C:\Kafka\bin\windows

REM Crear topic 'movimientos'
%KAFKA_PATH%\kafka-topics.bat --create --topic movimientos --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

REM Crear topic 'destinos'
%KAFKA_PATH%\kafka-topics.bat --create --topic destinos --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

REM Crear topic 'posiciones'
%KAFKA_PATH%\kafka-topics.bat --create --topic posiciones --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

echo Topics creados exitosamente.
pause
