import logging
from flask import current_app, jsonify
import json
import requests
import os
from groq import Groq
from dotenv import load_dotenv
import datetime
from app.utils.Agents import *
import pandas as pd
import re


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../', 'example.env'), override=True)

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

file_path = 'expenses.csv'



# Function to append a row to the dataframe and save it
def append_and_save_row(df, new_row):
    df = df.append(new_row, ignore_index=True)
    df.to_csv(file_path, index=False)
    return df



def generate_response(response):
    if os.path.exists(file_path):  # Check if the file already exists, if yes, load it. If not, create an empty DataFrame.
        df = pd.read_csv(file_path)
    else:
        df = pd.DataFrame(columns=['date', 'amount', 'reason'])  # Create an empty dataframe with the required columns

    intent = classify_user_intent(response)
    if intent == "ADD":
        user_query_str = user_query_structurer(response)
        user_query_json = json.loads(user_query_str)
        new_row = {'date' : user_query_json['date'], 'amount' : user_query_json['amount'], 'reason' : user_query_json['reason']}
        df = append_and_save_row(df, new_row)
        return "Expense added successfully!"
    else:
        output = chatbot(response,df)
        return output
    


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]
    timestamp_str = message.get("timestamp")
    if timestamp_str:
        try:
            message_timestamp = datetime.datetime.fromtimestamp(int(timestamp_str))
        except Exception as e:
            logging.warning(f"Timestamp conversion failed: {e}. Using current time.")
            message_timestamp = datetime.datetime.now()
    else:
        message_timestamp = datetime.datetime.now()

    iso_timestamp = message_timestamp.isoformat()

    message_with_timestamp = f"{message_body} (Sent at: {iso_timestamp})"

    response = generate_response(message_with_timestamp)
    data = get_text_message_input(current_app.config["RECIPIENT_WAID"], response)
    send_message(data)



def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
