@echo off
cd /d "C:\Users\Nizar\Desktop\SD\SD-Practica1"


REM Ejecutar AD_Engine.py
start /MAX cmd /k "python AD_Engine.py 0.0.0.0:4000 15 192.168.1.8:9092"

REM Ejecutar API_Engine.py
start cmd /k "python API_Engine.py"

REM Ejecutar AD_Registry.py
start cmd /k "python AD_Registry.py 0.0.0.0:8443"

REM Ejecutar Front
start cmd /k "node ./Front/server.js 0.0.0.0:450 192.168.1.8:5000"

timeout /t 1 /nobreak

REM Ejecutar AD_Drone.py en 15 terminales distintas
FOR /L %%i IN (1,1,15) DO (
    start cmd /k "python AD_Drone.py 192.168.1.8:4000 192.168.1.8:9092 192.168.1.8:8443 -d"
    timeout /t 3 /nobreak
)
