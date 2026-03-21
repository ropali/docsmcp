from app.core.clients.llm.models import Message, Role, LLMResponse
from app.core.clients.llm.client import LLMClient


class RAGQuery:
    def __init__(self, embedder, store, llm_client: LLMClient, top_k: int = 5):
        self.embedder = embedder
        self.store = store
        self.llm = llm_client
        self.top_k = top_k

    def query(self, user_question: str) -> LLMResponse:
        # Embed the question using the SAME model as ingestion
        query_vector = self.embedder.embed([user_question])[0]

        # Retrieve relevant chunks
        chunks = self.store.search(query_vector, top_k=self.top_k)

        # Build the prompt
        context = "\n\n---\n\n".join(
            f"[Source: {c.metadata.get('url', 'unknown')}]\n{c.content}" for c in chunks
        )
        prompt = f"""Use the following context to answer the question.
                If the answer isn't in the context, say so.

                Context:
                {context}

                Question: {user_question}
                Answer:
                """

        mesg = Message(role=Role.USER, content=prompt)
        response = self.llm.complete(model="gpt-4o-mini", messages=[mesg])
        return response
