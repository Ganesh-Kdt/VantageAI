import os
from edgar import Company
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title
from llama_index.core.schema import TextNode
from edgar import set_identity
from pinecone import Pinecone

# LlamaIndex Imports
from llama_index.core import VectorStoreIndex, Document, Settings, StorageContext, PromptTemplate
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator
from dotenv import load_dotenv
from llama_index.llms.openai_like import OpenAILike

load_dotenv()
set_identity("John Doe john.doe@example.com")

# --- Configuration ---
LLM_MODEL = "mistral-large-latest"
EMBEDDING_MODEL = "nomic-embed-text"
PINECONE_INDEX_NAME = "vantageai"
EMBEDDING_DIMENSION = 768 # nomic-embed-text outputs 768 dimensions


def fetch_and_chunk_10k_in_memory(ticker: str) -> list[Document]:
    """
    Fetches a 10-K directly into memory and chunks it using Unstructured.
    Zero disk I/O required.
    """
    print(f"\n[+] Fetching latest 10-K for {ticker} into memory...")
    
    # 1. Fetch the data using edgartools
    company = Company(ticker)
    # Get all 10-K filings, then grab the most recent one (index 0)
    latest_10k = company.get_filings(form="10-K")[0]
    
    # Extract the raw HTML directly into a Python string
    html_content = latest_10k.html() 
    
    if not html_content:
        raise ValueError(f"Failed to retrieve HTML content for {ticker}")

    print(f"[+] Successfully loaded {len(html_content)} characters into RAM.")
    print("[+] Initiating Unstructured semantic parsing...")

    # 2. Partitioning: Notice we use `text=` instead of `filename=`
    elements = partition_html(text=html_content)
    
    # 3. Chunking (using the same optimal parameters as before)
    chunks = chunk_by_title(
        elements,
        multipage_sections=True,
        combine_text_under_n_chars=500,
        new_after_n_chars=2000,
        max_characters=2400,
    )
    
    # 4. Convert to LlamaIndex Documents
    llama_documents = []
    for chunk in chunks:
        node = TextNode(
            text=str(chunk),
            metadata={
                "ticker": ticker,
                "document_type": "10-K",
                "element_type": type(chunk).__name__,
                "accession_number": latest_10k.accession_no, # edgartools gives us rich metadata!
                "filing_date": str(latest_10k.filing_date)
            }
        )
        llama_documents.append(node)
        
    print(f"[+] Successfully generated {len(llama_documents)} semantic chunks.")
    return llama_documents

def run_rag_pipeline(company_input, ticker):
    if not ticker:
        return "Not a public company (or not in our supported testing list)."

    # 1. Initialize LlamaIndex Settings (Global configuration)
    Settings.llm = OpenAILike(
        model="mistral-large-latest", 
        api_key=os.getenv("MISTRAL_API_KEY"),
        api_base="https://api.mistral.ai/v1",
        is_chat_model=True,
        context_window=131072 # This routes the request to Mistral instead of OpenAI
    )
    Settings.embed_model = OllamaEmbedding(model_name=EMBEDDING_MODEL)

    # 2. Setup Pinecone and Vector Store Context
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 3. JIT Cache Check directly via Pinecone
    # We query with a dummy vector of zeros to see if any chunks exist with this ticker
    dummy_vector = Settings.embed_model.get_text_embedding(ticker)
    cache_check = pinecone_index.query(
        vector=dummy_vector, 
        top_k=1, 
        filter={"ticker": ticker}
    )

    # 4. Ingestion Phase (If missing)
    if len(cache_check['matches']) == 0:
        print(f"[+] Cache miss. Initiating ingestion for {ticker}.")
        nodes=fetch_and_chunk_10k_in_memory(ticker)
        print("[+] Chunking, Embedding, and Uploading to Pinecone...")
        # This automatically handles chunking and upserting via the Settings and StorageContext
        index = VectorStoreIndex(
            nodes, 
            storage_context=storage_context,
            show_progress=True
        )
    else:
        print(f"\n[+] {ticker} found in Pinecone cache. Skipping download.")
        # Load the existing index connection
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # 5. Retrieval Phase (Enforcing Strict Metadata Filter)
    print(f"\n[+] Querying Vector Database for: '{query}'")
    
    # This guarantees zero cross-leakage by hard-filtering at the Pinecone level
    strict_filter = MetadataFilters(
    filters=[MetadataFilter(key="ticker", value=ticker, operator=FilterOperator.EQ)]
    )

    strict_financial_prompt = """\
You are a rigorous financial analyst. Answer the user's question based strictly on the provided 10-K excerpts below. 
If the context does not contain the answer, say "I cannot answer this based on the provided 10-K." Do not guess or use outside knowledge.

Context Information:
---------------------
{context_str}
---------------------

Question: {query_str}

Answer: \
"""

    qa_template = PromptTemplate(strict_financial_prompt)

    query_engine = index.as_query_engine(
        similarity_top_k=5,
        filters=strict_filter,
        response_mode="compact",
        text_qa_template=qa_template
    )
    
    print("[+] Generating Answer...\n")
    response = query_engine.query(query)
    
    return str(response)

# --- Execution ---
if __name__ == "__main__":
    # Remember to set your API key in your terminal first:
    # export PINECONE_API_KEY="your-pinecone-api-key"
    
    test_company = "google"
    test_query = "What are the primary risk factors mentioned regarding competition?"
    
    result = run_rag_pipeline(test_company, test_query)
    print("================ FINAL ANSWER ================\n")
    print(result)