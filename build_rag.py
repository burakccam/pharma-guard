import os
import glob
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from config import CORPUS_DIR, CHROMA_DB_DIR

def extract_text_from_pdf(pdf_path):
    text_data = []
    try:
        reader = PdfReader(pdf_path)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                text_data.append({
                    "text": text,
                    "metadata": {
                        "source_file": os.path.basename(pdf_path),
                        "page_number": i + 1
                    }
                })
    except Exception as e:
        print(f"Hata okunurken {pdf_path}: {e}")
    return text_data

def build_rag():
    print("RAG Veritabanı oluşturuluyor...")
    pdf_files = glob.glob(os.path.join(CORPUS_DIR, "*.pdf"))
    
    if not pdf_files:
        print(f"Uyarı: {CORPUS_DIR} klasöründe PDF bulunamadı!")
        return False
        
    all_chunks = []
    all_metadatas = []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        length_function=len
    )
    
    for pdf_file in pdf_files:
        print(f"İşleniyor: {os.path.basename(pdf_file)}")
        pages = extract_text_from_pdf(pdf_file)
        
        for page in pages:
            chunks = text_splitter.split_text(page["text"])
            for j, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                meta = page["metadata"].copy()
                meta["chunk_id"] = j
                all_metadatas.append(meta)
                
    if not all_chunks:
        print("Çıkarılabilen metin bulunamadı.")
        return False
        
    print(f"Toplam {len(all_chunks)} chunk oluşturuldu.")
    
    # Embedding model
    print("Embedding modeli yükleniyor... (all-MiniLM-L6-v2)")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    # Chroma DB oluştur ve kaydet
    print("ChromaDB'ye kaydediliyor...")
    vectorstore = Chroma.from_texts(
        texts=all_chunks,
        embedding=embeddings,
        metadatas=all_metadatas,
        persist_directory=CHROMA_DB_DIR
    )
    
    print(f"Başarılı! ChromaDB {CHROMA_DB_DIR} dizinine kaydedildi.")
    return True

if __name__ == "__main__":
    build_rag()
