from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings  # ya HuggingFaceEmbeddings

# Metadata read karo
with open("../dataset/ar_index_global_meta.txt", "r") as f:
    text = f.read()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_text(text)

# Embeddings banao
embeddings = OpenAIEmbeddings()   # HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2") bhi use kar sakta hai

# Store in FAISS
db = FAISS.from_texts(docs, embeddings)
db.save_local("../dataset/faiss_index")

print("✅ Metadata saved in FAISS Vector DB")
