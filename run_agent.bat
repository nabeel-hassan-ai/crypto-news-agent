@echo off
title Crypto News Trading AI Agent
cd /d "%~dp0"
echo ============================================================
echo      CRYPTO NEWS TRADING AI AGENT - STARTING DASHBOARD
echo ============================================================
echo.
python -m streamlit run app.py
pause
