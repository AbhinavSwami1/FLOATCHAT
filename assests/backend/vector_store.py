from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

# Metadata read
with open("../dataset/ar_index_global_meta.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_text(text)

# HuggingFace embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Store in FAISS
db = FAISS.from_texts(docs, embeddings)
db.save_local("../dataset/faiss_index")

print("✅ Metadata saved in FAISS Vector DB")
