"""
Script to run FastAPI Server
Run from ai_agent_mvp directory: python run.py
Or use: uvicorn main:app --reload
"""
import uvicorn

if __name__ == "__main__":
    # Run FastAPI application
    # main:app refers to main.py file and app variable inside that file
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Auto-reload when code changes
    )
