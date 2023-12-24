@echo off
cd /d "C:\Users\EPS\Music"


REM Ejecutar AD_Engine.py
start /MAX cmd /k "python AD_Engine.py 0.0.0.0:4000 15 172.21.42.19:9092"

REM Ejecutar API_Engine.py
start cmd /k "python API_Engine.py"

REM Ejecutar AD_Registry.py
start cmd /k "python AD_Registry.py 0.0.0.0:8443"

