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
    input_variables=["context", "question", "answer"],
    template="""
    A hallucination occurs if the ANSWER includes information not grounded in the CONTEXT or does not directly and accurately address the QUESTION.

    Definition:
    - The ANSWER is hallucinated if it contradicts the CONTEXT, adds unsupported claims, introduces fabricated, untrue details, or fails to correctly address the QUESTION.
    - The ANSWER is faithful if it strictly adheres to the facts in the CONTEXT and:
        1. Accurately responds to the QUESTION using the provided CONTEXT, OR
        2. Clearly states that it cannot answer the QUESTION because the CONTEXT does not contain relevant information.

    Instructions:
    - Respond ONLY "true" if the ANSWER contains hallucinations.
    - Respond ONLY "false" if the ANSWER is grounded, accurate, and appropriately addresses the QUESTION.

    CONTEXT:

    =====
    {context}
    =====

    QUESTION:

    =====
    {question}
    =====

    ANSWER:

    =====
    {answer}
    =====
"""
)


llm_chain = prompt | giga

def evaluate_hallucinations(context, answer, question):
    result = llm_chain.invoke({"context": context, "answer": answer, "question": question})
    save_to_database(context, question, answer, result.content)
    # print(f'**tokens used for validation: {result}')
    if hasattr(result, 'content'):
        return result.content
    else:
        return str(result)

