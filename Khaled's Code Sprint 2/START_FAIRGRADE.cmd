@echo off
cd /d "%~dp0"
set "PORT=3000"
echo Open http://localhost:3000/ after the server starts.
echo Live Cognito sign-in requires localhost, not 127.0.0.1, on port 3000.
echo Obtain test passwords privately from Omar. Do not put them in files.
node scripts/verify-models.mjs
if errorlevel 1 (
  echo Extract all asset ZIPs into the same parent folder first.
  pause
  exit /b 1
)
node server/server.mjs
pause
