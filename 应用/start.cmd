@echo off
rem Source-checkout launcher; no device operation occurs until selected in menu.
setlocal
set "TASK_ROOT=%~dp0"
if exist "%TASK_ROOT%.venv\Scripts\python.exe" (
  set "TASK_PYTHON=%TASK_ROOT%.venv\Scripts\python.exe"
) else (
  set "TASK_PYTHON=python"
)
set "PYTHONPATH=%TASK_ROOT%src;%PYTHONPATH%"
"%TASK_PYTHON%" -X utf8 -m a6700_unlock %*
exit /b %ERRORLEVEL%
