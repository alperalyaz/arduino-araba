@echo off
title Arduino Arabasi - Claude Code
cd /d C:\ardiuno
"C:\Users\user\.local\bin\claude.exe" -c
if errorlevel 1 (
  echo.
  echo Onceki sohbet bulunamadi, yeni sohbet baslatiliyor...
  echo.
  "C:\Users\user\.local\bin\claude.exe"
)
