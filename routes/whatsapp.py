from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
import json
import requests

router = APIRouter()


# ── HELPER FUNCTION ─────────────────────────────────────────
# This function sends a WhatsApp message to any phone number
# We will use this to reply to customers
# ────────────────────────────────────────────────────────────
def send_whatsapp_message(phone_number: str, message: str):
    token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

    url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    body = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code == 200:
        print(f"✅ Reply sent to {phone_number}")
    else:
        print(f"❌ Failed to send reply: {response.text}")

    return response


# ── ENDPOINT 1 ──────────────────────────────────────────────
# Meta calls this once to verify your server is real
# You MUST return hub_challenge as plain text — NOT as JSON
# ────────────────────────────────────────────────────────────
@router.get("/whatsapp/webhook")
def verify_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")

    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        print("✅ Webhook verified successfully!")
        return PlainTextResponse(content=hub_challenge)
    else:
        print("❌ Webhook verification failed")
        raise HTTPException(status_code=403, detail="Verification failed")


# ── ENDPOINT 2 ──────────────────────────────────────────────
# Every customer WhatsApp message arrives here
# ALWAYS return {"status": "ok"} — even if something breaks
# ────────────────────────────────────────────────────────────
@router.post("/whatsapp/webhook")
async def receive_message(request: Request):
    try:
        body = await request.body()
        data = json.loads(body)

        # Meta sends messages in a deeply nested structure
        entry = data.get("entry", [])
        if not entry:
            return {"status": "ok"}

        changes = entry[0].get("changes", [])
        if not changes:
            return {"status": "ok"}

        value = changes[0].get("value", {})
        messages = value.get("messages", [])

        if not messages:
            # This is normal — could be a delivery receipt
            return {"status": "ok"}

        message = messages[0]
        phone_number = message.get("from")     # Customer's phone number
        message_type = message.get("type")     # "text", "interactive", etc.

        if message_type == "text":
            text = message["text"]["body"]
            print(f"📩 Message from {phone_number}: {text}")

            # For now send a fixed reply
            # Day 3: we will replace this with Abdullah's AI response
            reply = "Hello! Thanks for messaging us. BRIO is here 24/7 to help you. 😊"
            send_whatsapp_message(phone_number, reply)

        return {"status": "ok"}

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return {"status": "ok"}


# ── ENDPOINT 3 ──────────────────────────────────────────────
# Manual send endpoint — useful for testing
# You can call this directly to send any message
# ────────────────────────────────────────────────────────────
@router.post("/whatsapp/send")
async def send_message(request: Request):
    try:
        data = await request.json()
        phone_number = data.get("phone_number")
        message = data.get("message")

        if not phone_number or not message:
            raise HTTPException(
                status_code=400,
                detail="phone_number and message are required"
            )

        response = send_whatsapp_message(phone_number, message)
        return {"status": "ok", "whatsapp_response": response.text}

    except Exception as e:
        return {"status": "error", "detail": str(e)}