@echo off
setlocal EnableDelayedExpansion

set "TARGET=%~1"
if "%TARGET%"=="" set "TARGET=help"

if /I "%TARGET%"=="help" goto help
if /I "%TARGET%"=="init" goto init
if /I "%TARGET%"=="build" goto build
if /I "%TARGET%"=="start" goto start
if /I "%TARGET%"=="stop" goto stop
if /I "%TARGET%"=="destroy" goto destroy
if /I "%TARGET%"=="qabot-up" goto qabot_up
if /I "%TARGET%"=="qabot-down" goto qabot_down
if /I "%TARGET%"=="qabot-logs" goto qabot_logs
if /I "%TARGET%"=="ingauge-up" goto ingauge_up
if /I "%TARGET%"=="ingauge-down" goto ingauge_down
if /I "%TARGET%"=="ingauge-logs" goto ingauge_logs

echo Target no reconocido: %TARGET%
goto help

:init
call :require_env
if errorlevel 1 exit /b %errorlevel%
docker run --rm -v "%CD%/docker/%SERVICE_NAME%:/work" -w /work %JUPYTERHUB_IMAGE% sh -c "pip install --no-cache-dir pip-tools==%PIP_TOOLS_VERSION% && pip-compile requirements.in"
docker run --rm -v "%CD%/docker/nginx/certs:/certs" alpine/openssl req -x509 -nodes -newkey rsa:4096 -sha256 -days 365 -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" -keyout /certs/tls.key -out /certs/tls.crt
if errorlevel 1 exit /b %errorlevel%
goto end

:build
call :require_env
if errorlevel 1 exit /b %errorlevel%
docker compose build
if errorlevel 1 exit /b %errorlevel%
goto end

:start
call :require_env
if errorlevel 1 exit /b %errorlevel%
docker compose up --wait
if errorlevel 1 exit /b %errorlevel%
goto end

:stop
call :require_env
if errorlevel 1 exit /b %errorlevel%
docker compose down
if errorlevel 1 exit /b %errorlevel%
goto end

:destroy
call :require_env
if errorlevel 1 exit /b %errorlevel%
docker compose down --volumes
if errorlevel 1 exit /b %errorlevel%
goto end

:qabot_up
docker compose -f apps/qabot/docker-compose.yml up --build -d
if errorlevel 1 exit /b %errorlevel%
goto end

:qabot_down
docker compose -f apps/qabot/docker-compose.yml down
if errorlevel 1 exit /b %errorlevel%
goto end

:qabot_logs
docker compose -f apps/qabot/docker-compose.yml logs -f
if errorlevel 1 exit /b %errorlevel%
goto end

:ingauge_up
docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml up --build -d
if errorlevel 1 exit /b %errorlevel%
goto end

:ingauge_down
docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml down
if errorlevel 1 exit /b %errorlevel%
goto end

:ingauge_logs
docker compose -f apps/In-gauge-and-en-gage/docker-compose.yml logs -f
if errorlevel 1 exit /b %errorlevel%
goto end

:help
echo Uso: make.bat ^<target^>
echo.
echo Targets disponibles:
echo   init          Inicializa el proyecto generando requeriments.txt y certificados TLS
echo   build         Construye la imagen de los servicios MLOps
echo   start         Levanta todos los contenedores de todos los servicios MLOps
echo   stop          Elimina todos los contenedores manteniendo los volumenes MLOps
echo   destroy       Elimina todos los contenedores y volumenes MLOps
echo   qabot-up      Levanta QA Bot con Docker Compose
echo   qabot-down    Para los contenedores de Docker Compose de QA Bot
echo   qabot-logs    Muestra logs de QA Bot
echo   ingauge-up    Levanta In-Gauge and En-Gage con Docker Compose
echo   ingauge-down  Para los contenedores de Docker Compose de In-Gauge and En-Gage
echo   ingauge-logs  Muestra logs de In-Gauge and En-Gage

:end
endlocal
exit /b 0

:require_env
if not exist ".env" (
  echo ERROR: el fichero obligatorio ".env" no existe.
  exit /b 1
)

call :load_env_file ".env"

if "%JUPYTERHUB_IMAGE%"=="" (
  echo ERROR: la variable obligatoria "JUPYTERHUB_IMAGE" no existe o esta vacia en ".env".
  exit /b 1
)

if "%PIP_TOOLS_VERSION%"=="" (
  echo ERROR: la variable obligatoria "PIP_TOOLS_VERSION" no existe o esta vacia en ".env".
  exit /b 1
)

if not defined SERVICE_NAME set "SERVICE_NAME=jupyterhub"
exit /b 0

:load_env_file
for /f "usebackq eol=# tokens=1,* delims==" %%A in (%~1) do (
  if not "%%A"=="" (
    if not defined %%A set "%%A=%%B"
  )
)
exit /b 0
