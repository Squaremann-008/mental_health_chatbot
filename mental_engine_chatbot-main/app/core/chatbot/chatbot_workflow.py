import logging
import os
import re

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.store.base import BaseStore
from langgraph.store.postgres.aio import AsyncPostgresStore

from app.core.chatbot.models import MessageRequest
from app.utils.model import chat_model
from app.utils.sys_prompt import SYSTEM_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

grok_api_key = os.getenv("GROQ_API_KEY")
db_url = os.getenv("DATABASE_URL")
DB_URI = os.getenv("DATABASE_URL")


def chat_model():
    model = init_chat_model(
        "meta-llama/llama-4-scout-17b-16e-instruct",
        model_provider="groq",
        api_key=grok_api_key,
    )  # / llama3-8b-8192
    return model


model = chat_model()
# store = PostgresStore.from_conn_string(db_url)
# checkpointer = PostgresSaver.from_conn_string(db_url)


def create_prompt_template(SYSTEM_PROMPT) -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )


async def call_model(
    state: MessagesState,
    config: RunnableConfig,
    *,
    store: BaseStore,
):
    user_id = config["configurable"]["user_id"]
    namespace = ("memories", user_id)
    memories = await store.asearch(namespace, query=str(state["messages"][-1].content))
    info = "\n".join([d.value["data"] for d in memories])

    system_msg = SYSTEM_PROMPT.format(info=info)
    prompt = await create_prompt_template(system_msg).ainvoke(state)

    # print(f"STATE-MESSAGES: {state['messages']}")
    # print(f"type_state: {type(state)}")
    # print(f"STATE: {state}")

    """response = await model.ainvoke(
        [{"role": "system", "content": system_msg}] + state["messages"]
    )"""

    response = await model.ainvoke(prompt)
    # print(f"RESPONSE: {response}")
    return {"messages": response.content}


async def main(config, input: MessageRequest):
    async with (
        AsyncPostgresStore.from_conn_string(DB_URI) as store,
        AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer,
    ):
        # await store.setup()
        # await checkpointer.setup()

        builder = StateGraph(MessagesState)
        builder.add_node(call_model)
        builder.add_edge(START, "call_model")

        graph = builder.compile(
            checkpointer=checkpointer,
            store=store,
        )

        user_input = input

        while True:
            async for chunk in graph.astream(
                {"messages": [{"role": "user", "content": user_input}]},
                config,
                stream_mode="values",
            ):
                return chunk["messages"][-1].content

            user_input = input


# save the relevant message to long-term memory


async def update_memory(state: MessagesState, config: RunnableConfig, store: BaseStore):

    conv_history = []
    for message in state["messages"]:
        if isinstance(message, HumanMessage):
            conv_history.append({"User": message.content})
        elif isinstance(message, AIMessage):
            conv_history.append({"Chatbot": message.content})

    prompt = f"""In a conversation between a human and an AI chatbot designed to help improve the user's mental health, the human has sent the following message. Examine the content to determine if it is significant enough to be saved in the chatbot's long-term memory for future reference, particularly to improve context for both current and future conversations.

    CONTEXT 
    - The AI chatbot is acting as a companion to the human, aiming to offer empathetic support, keep track of mental health progress, and provide personalized advice.
    
    Messages that convey personal information, emotional states, important life events, or any information that might help in understanding or supporting the user in future interactions are considered important.

    **Important Information to Store**:
    - **Personal Information**: Any details about the user (e.g., name, preferences).
    - **Emotional State**: Information on how the user is feeling, any stress or mood-related details.
    - **Significant Events**: Major life updates or changes (e.g., personal goals, relationships, milestones).
    - **Preferences & Dislikes**: Things the user likes, dislikes, or has expressed a preference for (e.g., activities, coping methods).
    - **Behavioral Patterns/Corrections**: Feedback or corrections on previous interactions.

    **Memory Storage**: 
    If the message contains relevant or important information, extract and store the key details in a structured format. This will help future interactions be more context-aware.

    Output the relevant key information if the message is important enough to be saved in long-term memory. The output should be **the key information, properly extracted and organized** in json form for future use. If not important, output empty or initialized json brackets. 

    ### EXAMPLES
    ```
    Example 1:
    message: {{"User": "I prefer to talk to you than a therapist"}},
    OUTPUT: 
    {{
      "Preference": "Prefers talking to the chatbot rather than a therapist"
    }}

    Example 2:
    message: {{"Chatbot": "That sounds like a good approach. Being organized can definitely help reduce stress. Have you ever tried using a productivity tool like a to-do list or time-blocking?",
              "User": "Actually, I don’t like using to-do lists. They just stress me out more. I feel like I’m failing when I don’t check things off. I prefer to just keep a mental note of what I need to do. I also like to use my calendar to keep track of important dates and deadlines."}},
    OUTPUT: 
    {{
      "Preference": "Dislikes to-do lists because they cause stress and feelings of failure when not completed.",
      "Coping Style": ["Prefers using mental note, other than to-do list", "Calendar Use for important reminders"]
    }}

    Example 3:
    message: {{"Chatbot": "hi, how are you",
              "User": "I am doing okay, just a little tired"}},
    OUTPUT: {{}}
    ```
    
    REMEMBER: OUTPUT EITHER IMPORTANT KEY INFORMATION OR {{}} (AN EMPTY INITIALIZED JSON). NO COMMENTS! ONLY PROVIDE THE RELEVANT KEY INFORMATION IN JSON FORMAT
    
    below is the message from the conversation:
    
 
    """

    important = await model.ainvoke(prompt + str(conv_history))
    if important.content.strip() != "":

        # Get the user id from the config
        user_id = config["configurable"]["user_id"]

        # Namespace the memory
        namespace = (user_id, "memories")

        # ... Analyze conversation and create a new memory

        # Create a new memory ID
        memory_id = config["configurable"]["thread_id"]  # str(uuid.uuid4())

        # extract the json from the response
        cleaned = re.search(r"\{.*\}", important.content, re.DOTALL).group()
        # We create a new memory
        await store.aput(namespace, memory_id, cleaned)
        logger.info(f"Message saved in long-term memory: {cleaned} ")
        return memory_id
    else:
        # If the message is not important, we do nothing
        logger.info("no Message important enough to be saved in long-term memory.")
        pass
