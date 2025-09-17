import uuid
from typing import Dict, List

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

# from langchain_core.embeddings import Embeddings
# from langchain_core.messages import get_buffer_string
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_huggingface.embeddings import HuggingFaceEmbeddings

from app.utils.model import chat_model
from app.utils.summary_prompt import SUMMARY_PROMPT

PROMPT = ChatPromptTemplate.from_messages(SUMMARY_PROMPT)


def chat_summary(chat_history: Dict) -> Dict:
    """
    Create a summary of the chat history using the provided prompt.
    """
    prompt = PROMPT.invoke({"history": chat_history})
    model = chat_model()
    response = model.invoke(prompt)
    last_messages = str(chat_history)[-500:]
    if not response.get("messages"):
        return {"response": last_messages}
    else:
        last_message = response["messages"][-1]
        return {"response": getattr(last_message, "content", last_messages)}


if __name__ == "__main__":
    chat_history = {
        {"bot": "How are you feeling today?"},
        {"user": "I'm doing very well, just so anxious about my upcoming exams."},
        {
            "bot": "I understand. It's normal to feel anxious before exams. Would you like some tips to manage your anxiety?"
        },
        {"user": "Yes, that would be helpful."},
        {
            "bot": "One technique that can help is deep breathing. Try inhaling for 4 seconds, holding for 4 seconds, and exhaling for 4 seconds. Would you like to try it now?"
        },
        {"user": "Okay, I can try that."},
        {
            "bot": "Great! Let's start. Inhale for 4 seconds... hold for 4 seconds... now exhale for 4 seconds. How do you feel?"
        },
        {"user": "I feel a little bit better, thanks!"},
        {
            "bot": "I'm glad to hear that! It's important to take breaks and breathe during stressful moments. Is there anything else you'd like to talk about?"
        },
        {"user": "I'm also feeling a bit overwhelmed with my workload."},
        {
            "bot": "It sounds like you have a lot on your plate. One way to manage this is by breaking down tasks into smaller, more manageable steps. Do you think that might help?"
        },
        {"user": "Yes, that sounds like a good idea."},
        {
            "bot": "I'm happy to help! Remember, taking things step by step can make everything seem more manageable. You're doing great!"
        },
    }
    summary = chat_summary(chat_history)
    print(summary)


recall_vector_store = InMemoryVectorStore(HuggingFaceEmbeddings())


def get_user_id(config: RunnableConfig) -> str:
    user_id = config["configurable"].get("user_id")
    if user_id is None:
        raise ValueError("User ID needs to be provided to save a memory.")

    return user_id


@tool
def save_recall_memory(memory: str, config: RunnableConfig) -> str:
    """Save memory to vectorstore for later semantic retrieval."""
    user_id = get_user_id(config)
    document = Document(
        page_content=memory, id=str(uuid.uuid4()), metadata={"user_id": user_id}
    )
    recall_vector_store.add_documents([document])
    return memory


@tool
def search_recall_memories(query: str, config: RunnableConfig) -> List[str]:
    """Search for relevant memories."""
    user_id = get_user_id(config)

    def _filter_function(doc: Document) -> bool:
        return doc.metadata.get("user_id") == user_id

    documents = recall_vector_store.similarity_search(
        query, k=3, filter=_filter_function
    )
    return [document.page_content for document in documents]
