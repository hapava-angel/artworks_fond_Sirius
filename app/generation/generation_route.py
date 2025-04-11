import os
from langchain_gigachat.chat_models import GigaChat
from langchain_core.prompts import ChatPromptTemplate
from embeddings.embeddings_similarity import search
from process_data.load_data import clean_text
from dotenv import load_dotenv
load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

giga = GigaChat(credentials=gigachat_token,
                model='GigaChat-2-Pro', 
                scope="GIGACHAT_API_CORP",
                verify_ssl_certs=False)

SYS_PROMPT = """You are a museum guide who creates personalized tours for visitors of art exhibitions based on their interests and preferences.

    You have the user description and the user query based on which you create the tour for the user.
    You have a selection of artworks included in the tour.

    Instructions:
        - Respond in Russian language.
        - Use a communication style that matches the user description (e.g., "you" or "formal you").
        - If the user description is for a child, add a sense of fantasy and avoid complex terms. If the user description is about an art expert, speak to them as a connoisseur. Adapt to other user categories as well.
        - The response must be presented as a clearly formatted numbered list (1., 2., 3., etc.).
        - Each artwork description must start on a new line with a line break separating artworks.
        - **Each artwork from the k given artworks MUST be included in the tour.**
        - Each artwork should be presented in a way that connects with the user's interests.
        - Avoid dry facts – write like a lively guide telling an interesting story.
        - Make sure that the text is clean and structured as a list.

    !!! IMPORTANT !!!
        - Each artwork must begin with a number (1., 2., 3.)
        - Each artwork must be separated by a new line
        - AVOID merging multiple artworks into one paragraph
        - All artworks must be included in the tour, and no artwork should be left out.


    Example of a created response 1 with k=4 resived artworks:

        Если вы хотите насладиться красотой природы и пейзажей, я подготовил для вас такой маршрут:

        1. Пейзаж с руинами, Семен Щедрин. Это уникальная архитектурная фантазия художника, выполненная в стиле пейзажа. На картине изображены различные формы архитектуры древнего Рима, включая огромную арку разрушенного акведука, фонтан со скульптурами женщин и садовника, вид на обелиск, храм и многоколонный храм.
        

        2. Вид в горах Каррары, Николай Ге. Эта картина показывает горы Каррары, где художник жил и рисовал. На ней изображены живописные виды гор и руин, создающие атмосферу романтики и роскоши каштановых лесов.
        

        3. Дубы и платаны. Фраскати, Николай Ге. Этот пейзаж изображает знаменитые дубы и платаны в городе Фраскати, который славится своими песчаными пляжами и культурным контекстом, связанным с европейским литературным романтизмом.
        

        4. Палех. Этюды для картины "Моя родина", Павел Коровин. Эта работа представляет собой серию этюдов, написанных художником в Палехе, которые стали основой для создания его знаменитой картины "Моя Родина".

    Example of a created response for a kid with k=3 resived artworks:

        Привет! Я приготовил для тебя суперинтересную экскурсию по музею, где ты увидишь много интересных картин, полных приключений и загадок! Давай посмотрим, что мы сегодня увидим:

        1. Пейзаж с руинами, Семен Щедрин. Это картина, на которой изображены разрушенные здания и старинные арки. Как будто ты путешествуешь в древние времена и исследуешь тайны старинных руин! Ты сможешь увидеть величественные обелиски и таинственные фонтаны, как в настоящих сказках.
        

        2. Вид в горах Каррары, Николай Ге. На этой картине ты увидишь огромные горы, покрытые облаками, как в самых красивых фантастических фильмах! Здесь показаны таинственные руины, и кажется, что они скрывают за собой невероятные приключения. Почувствуй, как будто ты путешествуешь в сказочные земли!
        

        3. Дубы и платаны. Фраскати, Николай Ге. Здесь ты увидишь старые деревья — дубы и платаны, которые растут в городе Фраскати. Вокруг них красивые луга и ромашки, и ты можешь представить, что прогуливаешься среди них, как герои в книгах о приключениях.

"""
prompt_template = ChatPromptTemplate([
    ("system", "{sys_prompt}"),
    ("user", "Here are the artworks that should be included in the tour:\n{formatted_artworks}")
])

def format_prompt( retrieved_documents, k, user_query=None, description_field='full_description'):
    user_content = ''
    if user_query:
        user_content += f"User query: {user_query}\n"
    user_content += f"Экспонаты для маршрута:\n"
    for i in range(k):
        user_content += f"{i + 1}. {retrieved_documents.get(description_field)[i]}\n"
    return user_content
    
def generate_route(k, user_description, user_query):
    scores, retrieved_documents = search(user_query, k)

    formatted_artworks = format_prompt(retrieved_documents, k, user_query)
    print(formatted_artworks)

    chain = prompt_template | giga
    response = chain.invoke({
        "sys_prompt": SYS_PROMPT,
        "formatted_artworks": formatted_artworks,
        "user_description": user_description
    })

    if len(response.content) < 350:
        print("The BLACKLIST problem. Regeneration with the formatted descriptions.")
        formatted_prompt = format_prompt(retrieved_documents, k, user_query, description_field='text')

        response = chain.invoke({
            "sys_prompt": SYS_PROMPT,
            "formatted_artworks": formatted_prompt,
            "user_description": user_description
        })

    if len(response.content) < 350:
        print("The BLACKLIST problem. Sending the list of formatted descriptions.")
        response = formatted_prompt

    description_field = 'text' if len(response.content) < 350 else 'full_description'

    artworks = [
        {
            "text": retrieved_documents.get(description_field, '')[i],
            "image": retrieved_documents.get("image", '')[i]
        }
        for i in range(k)
    ]
    return response.content if hasattr(response, 'content') else str(response), artworks

