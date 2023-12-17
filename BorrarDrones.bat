@echo off
cd /d "C:\Users\Nizar\Desktop\SD\SD-Practica1"

if exist 1.txt (
	del 1.txt
)

if exist 2.txt (
	del 2.txt
)

if exist 3.txt (
	del 3.txt
)

if exist 4.txt (
	del 4.txt
)

if exist 5.txt (
	del 5.txt
)

if exist 6.txt (
	del 6.txt
)

if exist 7.txt (
	del 7.txt
)

if exist 8.txt (
	del 8.txt
)

if exist 9.txt (
	del 9.txt
)

if exist 10.txt (
	del 10.txt
)

if exist 11.txt (
	del 11.txt
)

if exist 12.txt (
	del 12.txt
)

if exist 13.txt (
	del 13.txt
)

if exist 14.txt (
	del 14.txt
)

if exist 15.txt (
	del 15.txt
)


REM Ejecutar BorraDrones.py
start cmd /c "python BorraDrones.py"
