@echo off
cd /d "C:\Users\Nizar\Desktop\SD\SD-Practica1"


REM Ejecutar AD_Engine.py
start /MAX cmd /k "python AD_Engine.py 0.0.0.0:4000 15 192.168.1.8:9092"

REM Ejecutar AD_Registry.py
start cmd /k "python AD_Registry.py 0.0.0.0:5000"

timeout /t 1 /nobreak

REM Ejecutar AD_Drone.py en 15 terminales distintas
FOR /L %%i IN (1,1,15) DO (
    start cmd /k "Python AD_Drone.py 192.168.1.8:4000 192.168.1.8:9092 192.168.1.8:5000 -d"
    timeout /t 1 /nobreak
)

echo Script completado
