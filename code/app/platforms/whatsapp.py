import os
import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse

logger = logging.getLogger(__name__)

async def handle_whatsapp(request: Request, faq_engine, llm_handler, context_mgr, speech_processor):
    if request.method == "GET":
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")
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
            logger.info(f"WhatsApp Webhook received: {body}")
            
            if "object" in body and body["object"] == "whatsapp_business_account":
                for entry in body.get("entry", []):
                    for change in entry.get("changes", []):
                        value = change.get("value", {})
                        if "messages" in value:
                            for message in value["messages"]:
                                sender_id = message["from"]
                                msg_type = message["type"]
                                
                                user_msg = ""
                                if msg_type == "text":
                                    user_msg = message["text"]["body"]
                                elif msg_type == "audio":
                                    audio_id = message["audio"]["id"]
                                    user_msg = await download_and_transcribe_audio(audio_id, speech_processor)
                                
                                if not user_msg:
                                    continue
                                    
                                context = await context_mgr.get_context(sender_id, "whatsapp")
                                
                                faq_match = faq_engine.get_answer(user_msg)
                                if faq_match["source"] == "faq":
                                    bot_reply = faq_match["answer"]
                                else:
                                    bot_reply = await llm_handler.generate(user_msg, context["history"])
                                
                                await context_mgr.update_context(sender_id, "whatsapp", user_msg, bot_reply)
                                await send_whatsapp_message(sender_id, bot_reply)
                                
                return JSONResponse(content={"status": "success"}, status_code=200)
            return JSONResponse(content={"status": "ignored"}, status_code=200)
        except Exception as e:
            logger.error(f"WhatsApp handling error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def download_and_transcribe_audio(audio_id, speech_processor):
    token = os.getenv("WHATSAPP_TOKEN")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        media_res = await client.get(f"https://graph.facebook.com/v17.0/{audio_id}", headers=headers)
        if media_res.status_code == 200:
            media_url = media_res.json().get("url")
            if media_url:
                audio_res = await client.get(media_url, headers=headers)
                if audio_res.status_code == 200:
                    return await speech_processor.transcribe_audio(audio_res.content)
    return ""

async def send_whatsapp_message(to: str, text: str):
    token = os.getenv("WHATSAPP_TOKEN")
    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code != 200:
            logger.error(f"Failed to send WhatsApp message: {response.text}")
