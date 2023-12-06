REM Iniciar Zookeeper
start cmd /k "cd /d C:\Kafka\bin\windows & .\zookeeper-server-start.bat C:\Kafka\config\zookeeper.properties"

timeout /t 12 /nobreak

REM Iniciar Kafka Server
start cmd /k "cd /d C:\Kafka\bin\windows & .\kafka-server-start.bat C:\Kafka\config\server.properties"

