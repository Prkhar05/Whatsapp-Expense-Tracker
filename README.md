# WhatsApp Expense Tracker

The **WhatsApp Expense Tracker** is a Python-based application designed to help users track their expenses through WhatsApp messages. By parsing exported WhatsApp chat data, the application extracts and organizes expense information into a structured format, and provide expense-related answers based on user queries.

## Features

- **Send & Receive Messages on WhatsApp**: Connects the bot with the WhatsApp API to allow users to interact through chat messages.
- **Understanding Natural Language Messages**: The bot understands natural language, identifying whether the user wants to add an expense or inquire about their expenses.
- **Adding Expenses**: Users can send expenses in natural language, e.g., "Spent 500Rs on a latte at Starbucks." to the bot.
- **Storing Data**: The bot saves all expense into a CSV file for easy analysis.
- **Querying Expenses**: Users can ask about their spending in natural language, e.g.:
  - "How much did I spend on coffee this month?"
  - "Show me my biggest expenses this week."
  - "List all my food expenses in January."
    

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Prkhar05/Whatsapp-Expense-Tracker.git
cd Whatsapp-Expense-Tracker
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

- Rename `example.env` to `.env`.
- Update the `.env` file with the necessary configuration settings.

## Setup

### 1. Whatsapp Cloud API creation

- Follow this guide : https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/

### 2. Run the Flask Application

```bash
python run.py 
```

### 3.  Launch ngrok

  - Follow this guide :  https://ngrok.com/docs/integrations/whatsapp/webhooks/
  - Start ngrok by running the following command in a terminal on your local desktop:
```bash
ngrok http 8000 --domain your-domain.ngrok-free.app
```

### 4. Integrate Whatsapp

In the Meta App Dashboard, go to WhatsApp > Configuration, then click the Edit button.
  - In the Edit webhook's callback URL popup, enter the URL provided by the ngrok agent to expose your application to the internet in the Callback URL field, with /webhook at the end (i.e. https://myexample.ngrok-free.app/webhook).
  - Enter a verification token. This string is set up by you when you create your webhook endpoint. You can pick any string you like. Make sure to update this in your `VERIFY_TOKEN` environment variable.
  - After you add a webhook to WhatsApp, WhatsApp will submit a validation post request to your application through ngrok. Confirm your localhost app receives the validation get request and logs `WEBHOOK_VERIFIED` in the terminal.
  - Back to the Configuration page, click Manage.
  - On the Webhook fields popup, click Subscribe to the **messages** field. Tip: You can subscribe to multiple fields.
  - If your Flask app and ngrok are running, you can click on "Test" next to messages to test the subscription. You recieve a test message in upper case. If that is the case, your webhook is set up correctly.

---
#### Now you can use this chatbot to keep track of your expenses.

