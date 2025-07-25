# helpers.py

import logging
import os
import random
import uuid
import requests
import boto3
from config import (
    INSTAGRAM_ACCESS_TOKEN,
    AWS_S3_ACCESS_KEY,
    AWS_S3_SECRET_KEY,
    AWS_S3_REGION,
    AWS_S3_BUCKET
)
from chat_logic import get_answer, extract_data_from_chats
from database import store_message
from Models.bots import fetch_bot, store_button_time
from controllers import documentController
from Models.errorInfo import error_info
import shutil
import json




INSTAGRAM_BUSINESS_ID = "1234567890"
INSTAGRAM_API_URL = f"https://graph.facebook.com/v17.0/{INSTAGRAM_BUSINESS_ID}/messages"




def send_mark_seen(recipient_id, message_id, wh_access_token, wh_phone_number_id):
    """
    Mark the user's message as 'read' on WhatsApp.
    """
    WH_API_URL = f"https://graph.facebook.com/v17.0/{wh_phone_number_id}/messages"

    headers = {
        "Authorization": f"Bearer {wh_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    response = requests.post(WH_API_URL, headers=headers, json=payload)
    # if response.status_code == 200:
    #     logging.info(f"Mark seen indicator sent to {recipient_id}")
    # else:
    #     logging.error(f"Failed to send mark seen: {response.status_code} - {response.text}")


def send_whatsapp_message(wh_access_token, wh_phone_number_id,recipient_id, message_text, reply_to=None):   
    WH_API_URL = f"https://graph.facebook.com/v17.0/{wh_phone_number_id}/messages"

    """
    Send a text message via WhatsApp Cloud API.
    Optionally reply to a specific message ID.
    """
    headers = {
        "Authorization": f"Bearer {wh_access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message_text
        }
    }

    # Optional: sometimes quote the message (40% chance)
    if reply_to and random.random() < 0.4:
        payload["context"] = {"message_id": reply_to}

    response = requests.post(WH_API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return {"code":response.status_code, "message":response.text}
    else:
        return {"code":response.status_code, "message":response.text}
    
    
def send_whatsapp_document(wh_access_token, wh_phone_number_id, recipient_id, document_url, document_filename=None, caption=None):
    """
    Send a document via WhatsApp Cloud API.
    """
    WH_API_URL = f"https://graph.facebook.com/v17.0/{wh_phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {wh_access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "document",
        "document": {
            "link": document_url
        }
    }
    
    if document_filename:
        payload["document"]["filename"] = document_filename
    
    if caption:
        payload["document"]["caption"] = caption
    
    response = requests.post(WH_API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return {"code": response.status_code, "message": response.json()}
    else:
        return {"code": response.status_code, "message": response.text}




def send_whatsapp_button(wh_access_token, wh_phone_number_id, recipient_id, bot_id,bot_button_text):
    """
    Send a WhatsApp interactive message with "Are these all?" and "Yes" / "No" buttons.
    """
    store_button_time(recipient_id, bot_id)
    
    WH_API_URL = f"https://graph.facebook.com/v17.0/{wh_phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {wh_access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": bot_button_text
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "yes_option",
                            "title": "Yes, I Consent" # if you are changing message also change this line in bot controller process_message 
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "no_option",
                            "title": "NO"
                        }
                    }
                ]
            }
        }
    }
    
    response = requests.post(WH_API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return {"code": response.status_code, "message": response.json()}
    else:
        return {"code": response.status_code, "message": response.text}
    

def send_options(wh_access_token, wh_phone_number_id, recipient_id, bot_id,options):
    """
    Send a WhatsApp interactive message with "Are these all?" and "Yes" / "No" buttons.
    """
    store_button_time(recipient_id, bot_id)
    
    WH_API_URL = f"https://graph.facebook.com/v17.0/{wh_phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {wh_access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {
                "text": "Please choose an option:"
            },
            "footer": {
                "text": "Pick one below"
            },
            "action": {
                "button": "View Options",
                "sections": [
                    {
                        "title": "Consent Options",
                        "rows": options
                    }
                ]
            }
        }
    }
    
    response = requests.post(WH_API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return {"code": response.status_code, "message": response.json()}
    else:
        return {"code": response.status_code, "message": response.text}
   

def send_facebook_message(access_token, recipient_id, message_text):
    url = f"https://graph.facebook.com/v18.0/me/messages"
    headers = {"Content-Type": "application/json"}
    params = {"access_token": access_token}
    data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }
    response = requests.post(url, headers=headers, params=params, json=data)
    return response.json()


    response = requests.post(WH_API_URL, headers=headers, json=payload)

def send_instagram_message(recipient_id, message_text, access_token):

    # logging.info(f"recipient_id: {recipient_id}")
    # logging.info(f"message_text: {message_text}")
    # logging.info(f"access_token: {access_token}")
    """Send a response to the Instagram user."""
    url = "https://graph.instagram.com/v21.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    message_data = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text}
    }
    
    response = requests.post(url, headers=headers, json=message_data)
    # logging.info(f"Instagram Message Sent: {message_text}, Response: {response.json()}")
    if response.status_code == 200:
        return {"code":response.status_code, "message":response.text}
    else:
        return {"code":response.status_code, "message":response.text}
    # return response.json()


def handle_openai_request(user_message, sender_id, message_id, platform, bot_id, bot):
    """
    Call your chat logic (get_answer), store the assistant's response in the DB,
    and send the response back to the user.
    """
    # logging.info(f"here")
    # logging.info(f"Processing message bot details {bot}: {user_message}")
    if message_id is not None: 
        if platform == "whatsapp" and message_id:
            send_mark_seen(sender_id, message_id, bot.wh_access_token, bot.wh_phone_id)


    # Get the AI-generated response
    bot_response = get_answer(user_message, sender_id, bot)
    
    # extracted_data = extract_data_from_chats(sender_id, bot)


    # Send the response back to the user
    if platform == "whatsapp":
        send_whatsapp_message(
            bot.wh_access_token, 
            bot.wh_phone_id,
            recipient_id=sender_id,
            message_text=bot_response,
            reply_to=message_id,
        )   
            # Store the assistant's reply in the DB
        store_message(
            user_id=sender_id,
            role="assistant",
            content=bot_response,
            source=platform,
            bot_id=bot_id
        )
        
        # Logic for check if bot send response is "Ok I Am Filling the form please wait..." 
        # than run functionality for fill the form  
        
        if False:
        # if "ok i am filling the form please wait..." in bot_response.lower() or any(keyword in user_message.lower() for keyword in ["fill", "form"]):
            logging.info("Yes, Sent All Clicked")
            folder_path = os.path.join("downloads", sender_id)
            bot_id = bot.uuid
            # send_whatsapp_message(
            #     bot.wh_access_token,
            #     bot.wh_phone_id,
            #     recipient_id=sender_id,
            #     message_text="Ok I Am Filling the form please wait...",
            #     reply_to=message_id
            # )
            # store_message(
            #     user_id=sender_id,
            #     role="assistant",
            #     content="Ok I Am Filling the form please wait...",
            #     source=changes['messaging_product'],  
            #     bot_id=bot.uuid,
            # )
            
            chat_data = extract_data_from_chats(sender_id, bot) 
            response = documentController.process_folder(folder_path, bot_id, sender_id, chat_data, bot)

            if response.get("status_code") != 200:
                logging.info(f"Error in processing folder")
                handle_openai_request(response.get("message"), sender_id, None, "whatsapp", bot_id, bot) 
                return  
             
            logging.info(f"response: {response}")
            
            local_path =  os.path.join("downloads", sender_id) + "/" + response.get('file_name', '')
            
            details = f"local_path: {local_path} \n"
            # logging.info(f"local_path: {local_path}")
            
            s3_url = upload_file_to_s3(local_path, sender_id, bot_id)
            
            details += f"s3_url: {s3_url} \n"
            logging.info(f"s3_url: {s3_url}")
            
            new_url = s3_url.replace("https://edysorbot.s3.ap-south-1.amazonaws.com/", "")
            # logging.info(f"s3_url: {s3_url}")
            whatsapp_file_path = os.getenv("base_url") + "/public/" + new_url
            
            details += f"whatsapp_file_path: {whatsapp_file_path} \n"
            
            error_info("helpers.py", "handle_openai_request", details)
            
            # os.rmdir(folder_path)
            shutil.rmtree(folder_path)
            logging.info(f"whatsapp_file_path: {whatsapp_file_path}")
            
            send_whatsapp_document(
                bot.wh_access_token,
                bot.wh_phone_id,
                sender_id,
                whatsapp_file_path,
                "Application Form.docx"
                # "Please review and confirm if all details are correct. If any information is missing or incorrect, kindly update and resend the corrected version."
            )
            store_message(
                user_id=sender_id,
                role="assistant",
                content="Application Form",
                source=platform,  # ✅ Now passed as a parameter
                bot_id=bot_id,
                media_type="docx",
                media_path=s3_url
            )
            
        # logging.info(f"Sent response to {sender_id}: {bot_response}")
    elif platform == "instagram":
        send_instagram_message(sender_id, bot_response)


def upload_file_to_s3(local_file_path, sender_id, bot_id):
    # Extract file extension and generate a unique file name
    _, file_extension = os.path.splitext(local_file_path)
    unique_file_name = f"{uuid.uuid4()}{file_extension}"
    
    # Create a safe version of sender_id (remove characters that may conflict)
    safe_sender_id = sender_id.replace("+", "").replace("@", "_")
    
    # Construct the S3 key with the sender_id as a folder
    s3_key = f"{bot_id}/{safe_sender_id}/{unique_file_name}"
    
    # Initialize S3 client with credentials
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_S3_ACCESS_KEY,
        aws_secret_access_key=AWS_S3_SECRET_KEY,
        region_name=AWS_S3_REGION
    )
    
    try:
        # logging.info(f"Uploading file from {local_file_path} to S3 at key: {s3_key}")
        s3_client.upload_file(local_file_path, AWS_S3_BUCKET, s3_key)
        # logging.info(f"File uploaded to S3 as {s3_key}")
        
        # Construct the S3 file URL (adjust the URL format if needed)
        s3_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_S3_REGION}.amazonaws.com/{s3_key}"
        return s3_url
    except Exception as e:
        logging.error(f"Error uploading file to S3: {e}")
        return None


def download_file_from_whatsapp(media_id, filename, sender_id, wh_access_token, bot_id):
    """
    Download a file from WhatsApp using the media_id, save it temporarily,
    then upload it to AWS S3 in a folder named after the sender.
    Returns the S3 file URL or None if there's a failure.
    """

    # logging.info(f"Downloading file {media_id} from WhatsApp for {sender_id}")
    # logging.info(f"Downloading filename {filename} from wh_access_token for {wh_access_token}")


    headers = {"Authorization": f"Bearer {wh_access_token}"}
    media_url = f"https://graph.facebook.com/v17.0/{media_id}"

    # 1. Get a short-lived download URL
    media_info_response = requests.get(media_url, headers=headers)
    if media_info_response.status_code != 200:
        # logging.error(f"Failed to retrieve media info: {media_info_response.text}")
        return None

    media_info = media_info_response.json()
    # logging.info(f"media_info: {media_info}")
    
    download_url = media_info.get("url")
    if not download_url:
        # logging.error("No 'url' found in media info")
        return None

    # 2. Download the actual file
    file_response = requests.get(download_url, headers=headers)
    if file_response.status_code != 200:
        # logging.error(f"Failed to download file: {file_response.text}")
        return None

    # 3. Save the file temporarily under downloads/<sender_id>/<filename>
    if not filename:
        filename = f"file_{media_id}"  # Fallback if no filename provided
    if media_info.get('mime_type', '') == 'image/jpeg':
        filename += ".jpg"

    # Create a safe sender ID to use as a folder name
    safe_sender_id = sender_id.replace("+", "").replace("@", "_")
    local_dir = os.path.join("downloads", safe_sender_id)
    os.makedirs(local_dir, exist_ok=True)

    local_path = os.path.join(local_dir, filename)
    
    with open(local_path, "wb") as f:
        f.write(file_response.content)
    
   

    # 4. Upload the file to AWS S3 (passing sender_id to structure the S3 key)
    s3_url = upload_file_to_s3(local_path, sender_id, bot_id)
    if s3_url:
        # Optionally remove the local file after a successful upload
        os.remove(local_path)
        # logging.info(f"Local file {local_path} removed after S3 upload.")
        return s3_url  # Return the S3 URL so it can be stored in the DB
    else:
        return None
