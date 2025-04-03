import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """You must communicate with the user based on their USER DESCRIPTION.  
Your task is to provide the most accurate and engaging response to the user's QUESTION, based on their interests to make the answer as captivating as possible.  
Answer the QUESTION using the provided ARTWORK INFO.  
   Instructions:
        - Respond in Russian language
        - If the QUESTION requires additional information that is not available in the current context, inform the user that you don't have enough data to provide a precise answer. 

    QUESTION:
    =====
    {user_question}
    =====

    USER DESCRIPTION:
    =====
    {user_description}
    =====

    ARTWORK INFO:
    =====
    {artwork}
    =====
"""

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

giga_max = GigaChat(credentials=gigachat_token,
                model="GigaChat-Max", 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)


prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga
llm_chain_max = prompt_info | giga_max

def generate_answer(user_question, artwork, user_description):
    response =  llm_chain.invoke({"user_question": user_question, "artwork": artwork, "user_description": user_description})
    response_text = response.content
    print(response)
    if len(response_text) < 350:
        response =  llm_chain.invoke({ "user_question": user_question, "artwork": artwork, "user_description": None})
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)
    
def generate_answer_max(user_question, artwork, user_description):
    response =  llm_chain_max.invoke({"user_question": user_question, "artwork": artwork, "user_description": user_description})
    response_text = response.content
    print(response)
    if len(response_text) < 350:
        response =  llm_chain.invoke({ "user_question": user_question, "artwork": artwork, "user_description": None})
    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)