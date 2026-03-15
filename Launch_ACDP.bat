@echo off
title ACDP Dashboard Launcher
echo ===================================================
echo Starting the ACDP Framework...
echo Powered by Investopedia Analytics Logic
echo ===================================================
echo.
echo Launching server, please wait...

python -m streamlit run app.py

echo.
echo If the dashboard did not open, check the error above.
pause