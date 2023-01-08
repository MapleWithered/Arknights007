@echo off

if not defined TAG (
    set TAG=1
    start wt -p "Windows PowerShell" %0
    :: Windows Terminal 中 cmd 的配置名，我这里是“cmd”
    exit
)


rem 切换至 ArknightsAutoHelper 所在位置
:path
cd>nul 2>nul /D %~dp0
call venv\Scripts\activate.bat

rem 主任务
python arknights007\http_api_server.py

@REM rem 结束进程
:end
@REM echo [93m[!] 拜拜嘞您[1m
@REM rem TIMEOUT>nul 2>nul /T 3
pause
@exit

