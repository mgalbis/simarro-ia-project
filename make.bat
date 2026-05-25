@echo off
setlocal EnableDelayedExpansion

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

if "%~1"=="" goto help
if /I "%~1"=="help" goto help
if /I "%~1"=="requeriments" goto requeriments
if /I "%~1"=="build" goto build
if /I "%~1"=="start" goto start
if /I "%~1"=="stop" goto stop
if /I "%~1"=="destroy" goto destroy

echo Target no reconocido: %~1
goto help

:requeriments
docker run --rm -v "%CD%/docker/%SERVICE_NAME%:/work" -w /work %JUPYTERHUB_IMAGE% sh -c "pip install --no-cache-dir pip-tools==%PIP_TOOLS_VERSION% && pip-compile requirements.in"
if errorlevel 1 exit /b %errorlevel%
goto end

:build
docker compose build
if errorlevel 1 exit /b %errorlevel%
goto end

:start
docker compose up --wait
if errorlevel 1 exit /b %errorlevel%
goto end

:stop
docker compose down
if errorlevel 1 exit /b %errorlevel%
goto end

:destroy
docker compose down --volumes
if errorlevel 1 exit /b %errorlevel%
goto end

:help
echo Uso: make.bat ^<target^>
echo.
echo Targets disponibles:
echo   requeriments  Genera requirements.txt con pip-compile en Python Linux
echo   build         Construye la imagen de los servicios
echo   start         Levanta todos los contenedores de todos los servicios
echo   stop          Elimina todos los contenedores manteniendo los volúmenes
echo   destroy       Elimina todos los contenedores y volúmenes

:end
endlocal
exit /b 0

:load_env_file
for /f "usebackq eol=# tokens=1,* delims==" %%A in (%~1) do (
  if not "%%A"=="" (
    if not defined %%A set "%%A=%%B"
  )
)
exit /b 0
