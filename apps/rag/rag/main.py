from rag.embedding.embedders import LocalEmbedder
from rag.loaders import HTMLLoader
from rag.pipeline.ingestion import IngestionPipeline, Page
from rag.splitters.text_splitter import RecursiveCharacterSplitter
from rag.store.chroma_store import ChromaVectorStore

store = ChromaVectorStore(collection_name="test-col")
embedder = LocalEmbedder()


def verify():
    query = [
        "What is the reimbursement timeline for the home office stipend?",
        "During which hours must all Acme Corp employees be available?",
        "Is an employee allowed to work remotely from a different country than where they were hired?",
    ]

    for q in query:
        vector = embedder.embed([q])[0]
        results = store.search(vector, top_k=3)
        print("Question: ", q)
        for doc in results:
            print(f"\nURL: {doc.metadata['url']}")
            print(f"Chunk: {doc.content[:250]}...")

        print("\n")


def main():

    pages = [
        Page(
            **{
                "html": "<html><body><p>Acme Corp's remote work policy was updated in January 2024. Employees are required to work from their primary residence within the country of hire. A one-time stipend of $500 is available for home office setup, reimbursed within 60 days of submitting receipts. Core collaboration hours are 10:00 AM to 3:00 PM local time, with the remaining 2 hours of the workday flexible.</p></body></html>",
                "url": "https://example.com",
                "title": "Home",
            }
        ),
    ]

    pipeline = IngestionPipeline(
        loader=HTMLLoader(),
        splitter=RecursiveCharacterSplitter(chunk_size=512, overlap=64),
        embedder=embedder,  # free, runs locally
        store=store,
    )

    pipeline.run(pages)

    verify()


if __name__ == "__main__":
    main()
