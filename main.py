from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.whatsapp import router as whatsapp_router
from dotenv import load_dotenv

# Load all variables from your .env file
load_dotenv()

app = FastAPI(title="BRIO Backend")

# This allows Usman's Vercel frontend to talk to your Railway backend
# Without this, his browser will block every single request
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all WhatsApp routes
app.include_router(whatsapp_router, prefix="/api")

# Health check — Hamza pings this to confirm backend is alive
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "BRIO Backend"}