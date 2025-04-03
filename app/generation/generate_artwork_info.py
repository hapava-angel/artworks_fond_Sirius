import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from process_data.load_data import clean_text
from dotenv import load_dotenv
load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

template_info = """You are a skilled museum guide specializing in personalized artwork descriptions. Make your explanations  appropriate for the user’s interests from their USER DESCRIPTION, making the information as captivating as possible.

    You will receive ARTWORK INFO. Provide a concise, engaging explanation, highlighting details that resonate most with this user.

    Instructions:
        - Respond in Russian language
        - Response consist of 4-5 sentences.
        - Split the text into readable paragraphs to make it easier to perceive.
        - Each painting is part of a sequential tour, and you guide the user through the journey. Ensure the artwork information flows logically within the tour’s narrative.
        - !!! IMPORTANT: Use NO greetings such as "Привет" or "Здравствуйте" or any similar phrases. Respond only with the main content. !!!

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

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_artwork_info(artwork, user_description):
    response =  llm_chain.invoke({ "artwork": artwork, "user_description": user_description})
    response_text = response.content
    print(f'**Generation of the artwork_info with all parametrs: {response}')

    if len(response_text) < 450:
        print("The BLACKLIST problem. Regeneration with the less number of the parametrs.")
        response =  llm_chain.invoke({ "artwork": artwork, "user_description": None})
        print(f'**Generation of the artwork info without user_description: {response}')

    response_text_new = response.content
    if len(response_text_new) < 450:
        print("The BLACKLIST problem. Send the origina artwork info.")
        response =  clean_text(artwork)
        print(f'**Responce is the original artwork info')


    if hasattr(response, 'content'):
        return response.content
    else:
        return str(response)