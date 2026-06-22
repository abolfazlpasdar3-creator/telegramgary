@echo off
title نصب سرویس ربات فروش کانفیگ
color 0a
echo ========================================
echo      نصب سرویس ربات تلگرام
echo ========================================
echo.

cd /d F:\MyTelegramBot

echo در حال حذف سرویس قبلی (در صورت وجود)...
nssm.exe stop MyConfigBot 2>nul
nssm.exe remove MyConfigBot confirm 2>nul

echo.
echo در حال نصب سرویس جدید...
nssm.exe install MyConfigBot "C:\Users\pasdar.abolfazl\AppData\Local\Python\pythoncore-3.14-64\python.exe" "F:\MyTelegramBot\bot.py"

nssm.exe set MyConfigBot AppDirectory "F:\MyTelegramBot"
nssm.exe set MyConfigBot DisplayName "MyConfigBot - ربات فروش کانفیگ"
nssm.exe set MyConfigBot Description "ربات تلگرامی فروش کانفیگ - همیشه روشن"
nssm.exe set MyConfigBot Start SERVICE_AUTO_START

echo.
echo ✅ سرویس با موفقیت نصب شد!
echo.
echo در حال شروع ربات...
nssm.exe start MyConfigBot

echo.
echo وضعیت فعلی سرویس:
nssm.exe status MyConfigBot

echo.
pause