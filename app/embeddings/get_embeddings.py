import os
from sentence_transformers import SentenceTransformer
from gigachat import GigaChat
from dotenv import load_dotenv
load_dotenv()

gigachat_token = os.getenv("GIGACHAT_TOKEN")

giga = GigaChat(
    credentials=gigachat_token,
    verify_ssl_certs=False,
    scope="GIGACHAT_API_CORP",)

def get_embeddings(text_list, index=None):
    response = giga.embeddings(text_list)
    embeddings = [item.embedding for item in response.data][0]

    return embeddings