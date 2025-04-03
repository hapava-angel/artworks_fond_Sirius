import pandas as pd
import os
from tqdm import tqdm
from tika import unpack

def clean_content_pdf_docx(file_name):
    parsed_unpack = unpack.from_file(file_name, requestOptions={'timeout': None})
    content = parsed_unpack['content']
    print(content)
    return content

def texts_list(files_path):
    data = []
    for filename in tqdm(os.listdir(files_path)):
        filepath = os.path.join(files_path, filename)
        text = clean_content_pdf_docx(filepath)
        data.append({'title': filename, 'text': text})
    
    dataset = pd.DataFrame(data)
    return dataset

files_path = 'data/Slovcova/Словцова'
output_path = 'data/paintings_data_tables'

dataset = texts_list(files_path)
dataset.to_csv(os.path.join(output_path, "Slovcova.csv"), index=False)
