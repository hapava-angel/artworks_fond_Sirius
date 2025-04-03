import os
from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")
exhibition_description = os.getenv("EXHIBITION_DESCRIPTION")

template_info = """I want you to interact with the user based on their USER DESCRIPTION.  
    You are an experienced museum guide who has just led an interactive tour of the exhibition по виртуальному выставочному фонду at the ОЦ «Сириус».  
    Write to the user informing them that the exhibition has concluded, thank them for choosing an AI guide, say a few words about the exhibition, and invite them to evaluate your work. Be sure to provide a link to the feedback form and upcoming events at the Museum Complex.   

   Instructions:
        - Respond in Russian language
        - !!! IMPORTANT: Use NO greetings such as "Привет" or "Здравствуйте" or any similar phrases. Respond only with the main content. !!!
        - The message should consist of 2-3 sentences, written in a style that matches the USER DESCRIPTION.  
    
    USER DESCRIPTION:  
    =====  
    {user_description}  
    =====   

    Example message:  

        Благодарю вас за участие в экскурсии по виртуальному выставочному фонду ОЦ «Сириус»! Мы надеемся, что наша прогулка по культуре и истории оставила у вас массу впечатлений.
        Если хотите поделиться мнением или оценить нашу работу, мы будем признательны за ваш отзыв: [ссылка на форму оценки].

"""  

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)        

prompt_info = PromptTemplate.from_template(template_info)

llm_chain = prompt_info | giga

def generate_goodbye_word(user_description):
    response =  llm_chain.invoke({"user_description": user_description})
    print(response)
    if hasattr(response, 'content'):
        return response.content 
    else:
        return str(response)
