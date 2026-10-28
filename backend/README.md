# Backend - Document Copilot

This folder contains the FastAPI application for Document Copilot.

## Setup
1. Ensure `uv` is installed.
2. If working in a synced cloud directory (like OneDrive), set the link mode:
   ```powershell
   $env:UV_LINK_MODE="copy"
   ```
3. Sync dependencies:
   ```powershell
   uv sync
   ```

## Running the App
Use the following command to start the development server:
```powershell
uv run fastapi dev app/main.py
```

## Adding Dependencies
To add new packages:
```powershell
uv add <package-name>
```
To add dev dependencies:
```powershell
uv add --dev <package-name>
```
