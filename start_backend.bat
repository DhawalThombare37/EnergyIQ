@echo off
echo Starting EnergyIQ FastAPI Backend...
call d:\NewProject\venv\Scripts\activate
cd d:\NewProject
uvicorn backend.main:app --reload
