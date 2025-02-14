import json
import logging
from groq import Groq
import os
import json
import pandas as pd
from dotenv import load_dotenv
import datetime

logging.basicConfig(level=logging.INFO)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../', 'example.env'), override=True)

# Setting up the Groq client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)


def date_filter_LLM(response, least_date, today_date):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"Given the user query: '{response}', the earliest available date in the data is '{least_date}', and today's date is '{today_date}', please return only a JSON object with the keys 'start_date' and 'end_date' representing the filtered date range. The format for the dates should be 'YYYY-MM-DD'. The response should be strictly a valid JSON without any additional explanation or text."
            }
        ],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content.strip()

# Filters the DataFrame rows by the 'date' column based on the provided date range.
def filter_expenses_by_date(df, start_date, end_date):

    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d')
    filtered_df = df[(df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))]
    return filtered_df.to_json(orient="records", date_format="iso")

# 1st Agent to get the date filtered data

def date_filter_agent(response,df):
    least_date = "2025-01-01"
    today_date = datetime.datetime.today().strftime('%Y-%m-%d')
    output = date_filter_LLM(response,least_date,today_date)
    json_output = json.loads(output)
    start_date = json_output['start_date']
    end_date = json_output['end_date']
    filtered_json = filter_expenses_by_date(df, start_date, end_date)
    return filtered_json
    
    



def filter_expenses_with_llm(filtered_expenses_json, user_query):

    filtered_expenses = json.dumps(filtered_expenses_json)
    
    prompt = (
        f"You are an AI assistant that filters expenses based on a user's request. "
        f"Here is a list of expenses in JSON format: {filtered_expenses}. "
        f"User's request: '{user_query}'. "
        f"Please filter the expenses and return only the ones that match the user's query. "
        f"Return only the filtered expenses in the same JSON format, without any extra text."
    )
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )

    filtered_expenses_response = chat_completion.choices[0].message.content.strip()

    filtered_expenses_json = json.loads(filtered_expenses_response)
    return filtered_expenses_json

    
# 2nd Agent to get the reason filtered data
def reason_filter_agent(response,filtered_json):
    return filter_expenses_with_llm(filtered_json, response)
    


def final_reponse_generator(filtered_expenses, user_query):
    
    groq_message = f"""
    You are an AI assistant specializing in expense-related queries. Below is the filtered list of expenses relevant to the user's request:

    Filtered Expenses:
    {json.dumps(filtered_expenses, indent=2)}

    User Query: "{user_query}"

    **Task:**
    1. Analyze the filtered list and perform necessary operations (e.g., summing amounts, categorizing expenses, identifying trends).
    2. Provide a direct and structured response addressing the user's query.
    3. Keep the response clear, well-organized, and concise—detailed enough to be informative but without unnecessary elaboration.

    **Response Guidelines:**
    - If the user requests the total expense, return the sum along with a category-wise breakdown and relevant dates.
    - If the user asks for specific expenses (e.g., food-related), list them with dates, amounts (in rupees), and categories in a structured format.
    - Use a clean, readable structure (e.g., bullet points, tables, or short paragraphs).
    - Avoid excessive explanations—focus on delivering the requested data efficiently.

    **Example Outputs:**
    - **Total Expenses:** ₹10,500 (Food: ₹4,200, Travel: ₹3,500, Misc: ₹2,800)  
      **Date Range:** Jan 1 - Jan 10, 2025
    - **Food Expenses Breakdown:**  
      - Jan 2: ₹1,200 (Restaurant)  
      - Jan 5: ₹1,500 (Groceries)  
      - Jan 9: ₹1,500 (Cafe)  

    Ensure clarity, accuracy, and relevance in your response.
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": groq_message
            }
        ],
        model="deepseek-r1-distill-llama-70b", 
    )

    return chat_completion.choices[0].message.content

# 3rd Agent to get the final response
def final_response_agent(user_query,filtered_expenses_json):
    final_output = final_reponse_generator(filtered_expenses_json, user_query)
    return final_output.split("</think>")[1]

# Chatbot function
def chatbot(user_query,df):
    date_filtered_data = date_filter_agent(user_query,df)
    reason_filtered_data = reason_filter_agent(user_query,date_filtered_data)
    final_response = final_response_agent(user_query,reason_filtered_data)
    return final_response

# Agent to classify the user's intent  
def classify_user_intent(user_message):
    groq_message = f"""
    Classify the user's intent based on the following message:
    "{user_message}"

    If the user is adding a new expense, return only the word: ADD
    If the user is querying existing expenses, return only the word: QUERY
    Do not return anything else.
    """

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": groq_message}],
        model="llama-3.3-70b-versatile",
    )

    return chat_completion.choices[0].message.content.strip()

# Agent to structure the user's query
def user_query_structurer(user_query):
    chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"You are an AI expense parser. Extract the expense details from the following text and "
                        f"return the information as a JSON object with the keys 'date', 'amount', and 'reason'. "
                        f"Do not include any extra text or explanation; only output valid JSON.\n\nExpense description: {user_query}"
                    ),
                }
            ],
            model="llama-3.3-70b-versatile",
        )
    return chat_completion.choices[0].message.content