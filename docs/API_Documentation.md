# API Documentation

## `GET /health`
Returns the health status of the application.
**Response:** `{"status": "ok"}`

## `POST /webhook/telegram`
Handles incoming Telegram messages.
**Request:** Telegram Update Object
**Response:** `{"status": "success"}`

## `POST /webhook/whatsapp`
Handles incoming WhatsApp Cloud API messages.
**Request:** WhatsApp Webhook Payload
**Response:** `{"status": "success"}`

## `POST /webhook/messenger`
Handles incoming Facebook Messenger events.

## `POST /webhook/instagram`
Handles incoming Instagram Direct events.
