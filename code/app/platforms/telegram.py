import os
import logging
import httpx
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def handle_telegram(request: Request, faq_engine, llm_handler, context_mgr, speech_processor):
    if request.method == "POST":
        try:
            body = await request.json()
            if "message" not in body:
                return JSONResponse(content={"status": "ignored"}, status_code=200)
                
            message = body["message"]
            chat_id = str(message["chat"]["id"])
            
            user_msg = ""
            if "text" in message:
                user_msg = message["text"]
            elif "voice" in message:
                file_id = message["voice"]["file_id"]
                user_msg = await download_and_transcribe_telegram_audio(file_id, speech_processor)
            
            if not user_msg:
                return JSONResponse(content={"status": "success"}, status_code=200)
                
            context = await context_mgr.get_context(chat_id, "telegram")
            
            faq_match = faq_engine.get_answer(user_msg)
            if faq_match["source"] == "faq":
                bot_reply = faq_match["answer"]
            else:
                bot_reply = await llm_handler.generate(user_msg, context["history"])
                
            await context_mgr.update_context(chat_id, "telegram", user_msg, bot_reply)
            await send_telegram_message(chat_id, bot_reply)
            
            return JSONResponse(content={"status": "success"}, status_code=200)
        except Exception as e:
            logger.error(f"Telegram handling error: {e}")
            raise HTTPException(status_code=500, detail=str(e))

async def download_and_transcribe_telegram_audio(file_id, speech_processor):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/getFile?file_id={file_id}"
    
    async with httpx.AsyncClient() as client:
        res = await client.get(url)
        if res.status_code == 200:
            file_path = res.json().get("result", {}).get("file_path")
            if file_path:
                download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                audio_res = await client.get(download_url)
                if audio_res.status_code == 200:
                    return await speech_processor.transcribe_audio(audio_res.content)
    return ""

async def send_telegram_message(chat_id: str, text: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data)
        if response.status_code != 200:
            logger.error(f"Failed to send Telegram message: {response.text}")
