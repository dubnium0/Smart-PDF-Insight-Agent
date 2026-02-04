import streamlit as st
import os
import tempfile
import json
import time
import nest_asyncio
import email_api
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import RetrievalQA

nest_asyncio.apply()

# Load environment variables
load_dotenv()

st.set_page_config(page_title="PDF RAG with Gemini", layout="wide")

st.title("📄 PDF RAG System with Gemini")
st.markdown("Upload a PDF and ask questions about its content.")

# Sidebar for API Key and File Upload
with st.sidebar:
    st.header("Configuration")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        api_key = st.text_input("Enter Google API Key", type="password")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
    
    st.divider()
    st.header("Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if not os.getenv("GOOGLE_API_KEY"):
    st.warning("Please provide a Google API Key in the sidebar or .env file to proceed.")
    st.stop()

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

if uploaded_file is not None:
    if st.session_state.get("last_uploaded") != uploaded_file.name:
        with st.spinner("Processing PDF..."):
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                loader = PyPDFLoader(tmp_path)
                documents = loader.load()
                
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(documents)

                embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-exp-03-07")
                st.session_state.vectorstore = Chroma.from_documents(
                    documents=splits, 
                    embedding=embeddings
                )
                
                st.session_state.last_uploaded = uploaded_file.name
                os.remove(tmp_path)
                st.success(f"Processed {len(splits)} chunks from {uploaded_file.name}!")
                
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Chat Interface
if st.session_state.vectorstore:
    st.divider()
    
    st.divider()
    
    chat_container = st.container()

    query = st.chat_input("Ask a question specific to the PDF:")
    
    if query:
        with st.spinner("Analyzing PDF..."):
            try:
                llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
                retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 3})
                
                from langchain.prompts import PromptTemplate

                # Define custom prompt template
                prompt_template = """
                Aşağıdaki bağlamı kullanarak soruyu cevapla.
                Cevabı bir e-posta formatında hazırla ve kesinlikle şu başlıkları kullan:

                **Soru: {question}
                **Cevap: (PDF'teki net bilgiyi kullanarak cevapla) 
                **Agent Yorumu: (Konuya dair profesyonel içgörünü ekle) 
                **Öneri Aksiyonları: (Bu bilgi ışığında önerdiğin adımları madde madde yaz)

                yapıyı koru alt alta olsun istenilen çıktılar.
                bu formata ek olarak başka bir çıktı çıkarma.  
                Eğer bağlamda cevap yoksa, bunu belirt.

                Bağlam:
                {context}
                """
                
                PROMPT = PromptTemplate(
                    template=prompt_template, input_variables=["context", "question"]
                )

                chain_type_kwargs = {"prompt": PROMPT}
                
                qa_chain = RetrievalQA.from_chain_type(
                    llm=llm, 
                    chain_type="stuff", 
                    retriever=retriever,
                    return_source_documents=True,
                    chain_type_kwargs=chain_type_kwargs
                )
            
                start_time = time.time()
                result = qa_chain.invoke({"query": query})
                end_time = time.time()

                elapsed_time = end_time - start_time
                minutes, seconds = divmod(elapsed_time, 60)
                formatted_time = "{:02}:{:02}".format(int(minutes), int(seconds))

                log_data = {
                    "team_name": "alphazero",
                    "task_id": 4,
                    "input_prompts": [prompt_template],
                    "execution_time": formatted_time,
                    "result_output": {
                        "summary": "RAG query processed successfully.",
                        "data": result["result"]
                    }
                }
                
                st.session_state.chat_history.append({
                    "query": query,
                    "answer": result["result"],
                    "sources": result["source_documents"],
                    "log": log_data
                })
                
                recipient_email = "example@gmail.com"
                email_content = f"{result['result']}\n\n--- İŞLEM LOGU ---\n{json.dumps(log_data, indent=4, ensure_ascii=False)}"
                
                with st.spinner(f"Otomatik email gönderiliyor..."):
                    success, message = email_api.send_email(
                        recipient_email, 
                        f"RAG Cevabı: {query}", 
                        email_content
                    )
                    if success:
                        st.success(f"Rapor otomatik olarak {recipient_email} adresine gönderildi.")
                    else:
                        st.error(f"Email gönderim hatası: {message}")

            except Exception as e:
                st.error(f"Error generating answer: {str(e)}")

    with chat_container:
        for i, chat in enumerate(st.session_state.chat_history):
            with st.chat_message("user"):
                st.write(chat["query"])
            
            with st.chat_message("assistant"):
                st.markdown("### Agent Maili")
                st.write(chat["answer"])
                
                with st.expander("View Source Documents"):
                    for j, doc in enumerate(chat["sources"]):
                        st.markdown(f"**Source {j+1} (Page {doc.metadata.get('page', 'Unknown')}):**")
                        st.text(doc.page_content)
                
                st.divider()
                st.subheader("İşlem Logu (JSON)")
                st.code(json.dumps(chat["log"], indent=4, ensure_ascii=False), language='json')
                
                st.divider()
                st.caption(f"Bu rapor otomatik olarak example@gmail.com adresine gönderilmiştir.")
                
                if st.button("Tekrar Gönder", key=f"resend_btn_{i}"):
                    recipient_email = "example@gmail.com"
                    email_content = f"{chat['answer']}\n\n--- İŞLEM LOGU ---\n{json.dumps(chat['log'], indent=4, ensure_ascii=False)}"
                    
                    with st.spinner("Email gönderiliyor..."):
                        success, message = email_api.send_email(
                            recipient_email, 
                            f"RAG Cevabı: {chat['query']}", 
                            email_content
                        )
                        if success:
                            st.success("Email başarıyla tekrar gönderildi!")
                        else:
                            st.error(f"Hata: {message}")
                st.divider()

else:
    st.info("Please upload a PDF to start chatting.")
