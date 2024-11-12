import os
from dotenv import load_dotenv

from utilities import get_relevant_products

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import Runnable
from langchain.schema.runnable.config import RunnableConfig
from langchain_core.runnables import RunnableLambda, RunnablePassthrough

import chainlit as cl

load_dotenv()

@cl.on_chat_start
async def on_chat_start():
    openai = AzureChatOpenAI(
        openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
        streaming=True
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "ai",
                """ 
                You are a system assistant who helps users find product recommendations, based off the products that are provided to you.
                Product recommendations will be provided in an assistant message in the format of `productname|description`. 
                You can use only the provided product list to help you answer the user's unless the users question has questions around price and quantity available.
                If the user ask a question that is not related, you can respond with a message that you can't help with that question and request user see if they need anything else.
                If the user asks more questions on the product retrieved for example price or stock, respond in a descriptive way using the information previously received.
                If user asks question about thats not specific try to use the previous information for example if the asks : how much does that cost, probably they are referring to the product they were enquiring about,
                if you still cannot get it prompt the user to ask a more specific question.
                Your answer must have the Product Name, a short summary of the product and the product category.
                """,
            ),
            (
                "human",
                """
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

    # Use an agent retriever to get relevant products
    retriever = RunnableLambda(get_relevant_products, name="GetRelevantProducts").bind() 

    runnable = {"recommendations": retriever, "question": RunnablePassthrough()} | prompt | openai | StrOutputParser()
    cl.user_session.set("runnable", runnable)    

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable
    
    msg = cl.Message(content="")

    for chunk in await cl.make_async(runnable.stream)(
        input=message.content,
        config=RunnableConfig(callbacks=[cl.LangchainCallbackHandler()]),
    ):
        await msg.stream_token(chunk)

    await msg.send()
