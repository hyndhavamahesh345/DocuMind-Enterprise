import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class RetrievalEngine:
    def __init__(self):
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        self.vectorstore = PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings
        )
        # Using Gemini 1.5 Flash - fast and usually free tier friendly
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0)

    def get_query_response(self, query: str):
        # Strict Prompting to prevent hallucinations
        system_prompt = (
            "You are a Corporate Brain assistant for question-answering tasks. "
            "Use the following pieces of retrieved context to answer "
            "the question. If you don't know the answer, say that you "
            "don't know. Use three sentences maximum and keep the "
            "answer concise. If the answer is not in the context, strictly "
            "say 'This is outside my scope.'\n\n"
            "Context: {context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        # LCEL Implementation
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        rag_chain = (
            {"context": self.vectorstore.as_retriever() | format_docs, "input": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )

        # To keep citations, we need the context docs
        context_docs = self.vectorstore.as_retriever().invoke(query)
        answer = rag_chain.invoke(query)
        
        return {"answer": answer, "context": context_docs}
