@echo off
echo プロジェクトホーム fujixcam-api から testsのモジュールを実行する
echo 0. quick test sample      (test0.py)
echo 1. test CameraAPI() layer (test1.py)
echo 2. test Camera()    layer (test2.py)

rem question for user input
set /p choice="choice :" 

if "%choice%"=="0" cd .. & python -m tests.test0 & cd tests
if "%choice%"=="1" cd .. & python -m tests.test1 & cd tests
if "%choice%"=="2" cd .. &python -m tests.test2 & cd tests
