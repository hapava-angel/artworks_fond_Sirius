from langchain_gigachat.chat_models import GigaChat
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

load_dotenv() 

gigachat_token = os.getenv("GIGACHAT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

def save_to_database(context, question, answer, result):
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        insert_query = sql.SQL("""
            INSERT INTO hallucination_evaluations (context, question, answer, result)
            VALUES (%s, %s, %s, %s)
        """)
        cursor.execute(insert_query, (context, question, answer, result))

        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully!")

    except Exception as e:
        print(f"Error saving to database: {e}")

giga = GigaChat (
    credentials=gigachat_token,
    model="GigaChat-Max",
    scope="GIGACHAT_API_CORP",
    verify_ssl_certs=False
)

prompt = PromptTemplate(
    input_variables=["context", "description"],
    template="""
    A hallucination occurs if the DESCRIPTION includes information not grounded in the CONTEXT.

    Definition:
    - The DESCRIPTION is hallucinated if it contradicts the CONTEXT, adds unsupported claims, introduces fabricated,  untrue details.
    - The DESCRIPTION is faithful if it strictly adheres to the facts in the CONTEXT.

    Instructions:
    - Respond ONLY "true" if the DESCRIPTION contains hallucinations.
    - Respond ONLY "false" if the DESCRIPTION is grounded and accurate.

    CONTEXT:

    =====
    {context}
    =====

    DESCRIPTION:

    =====
    {description}
    =====
"""
)


llm_chain = prompt | giga

def evaluate_hallucinations_artworkinfo(context, answer):
    result = llm_chain.invoke({"context": context, "description": answer})
    question = "Опиши картину"
    save_to_database(context, question, answer, result.content)
    # print(f'**tokens used for validation: {result}')
    if hasattr(result, 'content'):
        return result.content
    else:
        return str(result)
