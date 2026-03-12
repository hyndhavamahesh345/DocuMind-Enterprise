import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv()

class RetrievalEngine:
    def __init__(self):
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0, streaming=True)
        self._setup_chains()

    def _setup_chains(self):
        # 1. History-Aware Retriever
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages([
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, contextualize_q_prompt
        )

        # 2. QA Chain with Citations
        qa_system_prompt = (
            "You are DocuMind, a Corporate Brain assistant. "
            "Use the retrieved context to answer the question accurately. "
            "Maintain page-level citations if provided. "
            "If the answer is not in the context, strictly say: 'This is outside my scope.'\n"
            "Context: {context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(self.history_aware_retriever, question_answer_chain)

    def get_streaming_response(self, query: str, chat_history: List[Dict[str, str]] = []):
        """
        Yields tokens for streaming and finally yields the context for citations.
        """
        # Convert dict history to LangChain messages if needed (simplified here for speed)
        history = []
        for msg in chat_history:
            role = "human" if msg["role"] == "user" else "assistant"
            history.append((role, msg["content"]))

        for chunk in self.rag_chain.stream({"input": query, "chat_history": history}):
            if "answer" in chunk:
                yield chunk["answer"]
            elif "context" in chunk:
                # Store context for citations if needed after stream
                self.last_context = chunk["context"]

    def get_query_response(self, query: str, chat_history: List = []):
        # Fallback for non-streaming
        return self.rag_chain.invoke({"input": query, "chat_history": chat_history})
