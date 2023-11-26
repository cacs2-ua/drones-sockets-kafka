@echo off
cd /d "D:\Uni UA 2.0\Tercer año\Primer Cuatri\SD\Práctica\Práctica 2\mine-github\SD-prac2-mine"


REM Ejecutar AD_Engine.py
start cmd /k "python AD_Engine.py 0.0.0.0:4000 15 192.168.1.120:9092 127.0.0.2:5000"

REM Ejecutar AD_Registry.py
start cmd /k "python AD_Registry.py 0.0.0.0:65432"

REM Ejecutar AD_Weather.py
start cmd /k "python AD_Weather.py 0.0.0.0:5000"

timeout /t 1 /nobreak

REM Ejecutar AD_Drone.py en 15 terminales distintas
FOR /L %%i IN (1,1,15) DO (
    start cmd /k "Python AD_Drone.py 127.0.0.1:4000 192.168.1.120:9092 127.0.0.1:65432 -d"
    timeout /t 1 /nobreak
)

echo Script completado
