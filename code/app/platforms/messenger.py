import os
import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

logger = logging.getLogger(__name__)

async def handle_messenger(request: Request, faq_engine, llm_handler, context_mgr, speech_processor):
    if request.method == "GET":
        verify_token = os.getenv("FACEBOOK_VERIFY_TOKEN")
        mode = request.query_params.get("hub.mode")
        token = request.query_params.get("hub.verify_token")
        challenge = request.query_params.get("hub.challenge")

        if mode and token:
            if mode == "subscribe" and token == verify_token:
                return PlainTextResponse(challenge)
            else:
                raise HTTPException(status_code=403, detail="Verification failed")
        raise HTTPException(status_code=400, detail="Missing parameters")

    elif request.method == "POST":
        try:
            body = await request.json()
            if body.get("object") == "page":
                for entry in body.get("entry", []):
                    for event in entry.get("messaging", []):
                        sender_id = event["sender"]["id"]
                        
                        user_msg = ""
                        if "message" in event:
                            message = event["message"]
                            if "text" in message:
                                user_msg = message["text"]
                            elif "attachments" in message:
                                for att in message["attachments"]:
                                    if att["type"] == "audio":
                                        url = att["payload"]["url"]
                                        user_msg = await speech_processor.transcribe_audio(url)
                                        break
                                        
                        if not user_msg:
                            continue
                            
                        # Send typing indicator
                        await send_messenger_action(sender_id, "typing_on")
                        
                        context = await context_mgr.get_context(sender_id, "messenger")
                        
                        faq_match = faq_engine.get_answer(user_msg)
                        if faq_match["source"] == "faq":
                            bot_reply = faq_match["answer"]
                        else:
                            bot_reply = await llm_handler.generate(user_msg, context["history"])
                            
                        await context_mgr.update_context(sender_id, "messenger", user_msg, bot_reply)
                        
                        await send_messenger_action(sender_id, "typing_off")
                        await send_messenger_message(sender_id, bot_reply)
                        
                return JSONResponse(content={"status": "success"}, status_code=200)
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        except Exception as e:
            logger.error(f"Messenger handling error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def send_messenger_action(recipient_id: str, action: str):
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={token}"
    
    data = {
        "recipient": {"id": recipient_id},
        "sender_action": action
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(url, json=data)

async def send_messenger_message(recipient_id: str, text: str):
    token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
    url = f"https://graph.facebook.com/v17.0/me/messages?access_token={token}"
    
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": text}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        if response.status_code != 200:
            logger.error(f"Failed to send Messenger message: {response.text}")
