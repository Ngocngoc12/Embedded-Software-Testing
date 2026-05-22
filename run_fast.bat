@echo off
echo ========================================================
echo SHOPEEFOOD AUTOMATION TEST - FAST EXECUTION
echo ========================================================
echo.
echo Dang chay 22 Test Cases voi 4 luong song song...
echo Vui long doi. Ket qua se duoc xuat ra file report.html
echo.

set PYTHONUTF8=1
python -m pytest ShopeeFood_Automation_Test.py -n 4 --html=report.html --self-contained-html -v

echo.
echo ========================================================
echo DA HOAN THANH! Ban hay mo file report.html de xem ket qua.
echo ========================================================
pause
