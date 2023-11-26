
REM Crear topics
.\kafka-topics.bat --create --topic destinos --bootstrap-server 192.168.186.160:9092 --partitions 1
.\kafka-topics.bat --create --topic movimientos --bootstrap-server 192.168.186.160:9092 --partitions 1
.\kafka-topics.bat --create --topic posiciones --bootstrap-server 192.168.186.160:9092 --partitions 1
