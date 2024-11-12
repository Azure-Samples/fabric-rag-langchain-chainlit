import os
from dotenv import load_dotenv

from utilities import get_relevant_products

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig

import chainlit as cl

load_dotenv()

@cl.step(type="tool", name="GetRelevantProducts")
async def GetRelevantProducts(search_text: str) -> str:
    return await cl.make_async(get_relevant_products)(search_text)

@cl.on_chat_start
async def on_chat_start():
    model = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        streaming=True
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """ 
                You are a system assistant who helps users find product recommendations, based off the products that are provided to you.
                Product recommendations will be provided in an assistant message in the format of `productname|description`. You can use only the provided product list to help you answer the user's question.
                If the user ask a question that is not related, you can respond with a message that you can't help with that question.
                Your answer must have the Product Name, a short summary of the product and the product category.
                """,
            ),
            (
                "system", """
                 The products and accessories available are the following: 
                {recommendations}                
                """
            ),
            (
                "human", 
                "{question}"
            ),
        ]
    )
    runnable = prompt | model | StrOutputParser()
    cl.user_session.set("runnable", runnable)    

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable

    # Use a chainlit tool to get product recommendations
    # as another option to langchain integration
    product_list = await GetRelevantProducts(message.content);

    msg = cl.Message(content="")
    input = {"question": message.content, "recommendations": product_list}

    for chunk in await cl.make_async(runnable.stream)(
        input = input,
        config = RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
