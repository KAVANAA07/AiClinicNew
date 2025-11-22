@echo off
cd /d "c:\Users\VITUS\AiClinicNew\ClinicProject"
call venv\Scripts\activate.bat
pip install Django==5.2.8 django-q2==1.8.0 djangorestframework==3.16.1 django-cors-headers==4.9.0 python-decouple==3.8 twilio==9.8.5
pause