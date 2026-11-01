@echo off
REM Abre el proyecto R_LAB_HabeasData (robot.db de esta carpeta) en Rocketbot Studio.
REM Credenciales SINTETICAS del doble local (modo fixture): no son secretos reales. Deben coincidir con
REM Configuracion/ConfiguracionProceso.json (ZeusApi.Fixture.ClientIdEnv / ClientSecretEnv). Sin ellas el robot no obtiene token.
set ZEUS_DOBLE_CLIENT_ID=cliente-banco
set ZEUS_DOBLE_CLIENT_SECRET=secreto-banco-no-real
REM Carpeta de Rocketbot: declara ROCKETBOT_DIR antes de lanzar este archivo si no es la de esta maquina.
if "%ROCKETBOT_DIR%"=="" set ROCKETBOT_DIR=C:\Users\%USERNAME%\Documents\rocketbot_win_20260407\Rocketbot
cd /d "%ROCKETBOT_DIR%"
rocketbot.exe -start=R_LAB_HabeasData -db="%~dp0robot.db"
