from typing import Dict, List, Union, Any
import httpx
import http
from extensions.ext_database import db
from models.model import Conversation
import asyncio
import requests
import logging
import time
import os
from pydantic import BaseModel, validator
from openai import OpenAI
import json 
import re
from tenacity import retry, stop_after_attempt, wait_fixed
from core.model_manager import ModelManager
from core.model_runtime.entities.model_entities import ModelType
from core.model_runtime.entities.message_entities import UserPromptMessage, SystemPromptMessage, AssistantPromptMessage

@retry(stop=stop_after_attempt(3), wait=wait_fixed(3))
async def make_request_async(request_model: dict, query: str) -> None:
    body = {
        "response_mode": "streaming",
        "conversation_id": "", # Keep empty to create new conversation
        "query": query,
        "inputs": {} # Expects files? Might need support in the future.
    }
    
    headers = {
        "Authorization": request_model["bearer_token"],
        "Content-Type": "application/json"
    }
    logging.info(f"Chat Spawner making request to {request_model["url"]}")
    async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, read=10.0), http2=True) as client:
        response = await client.post(request_model["url"], json=body, headers=headers)
    

async def spawn_chats(request_model, queries):
    start_time = time.time() 

    for query in queries:
        task = asyncio.create_task(make_request_async(request_model, query))
        await asyncio.sleep(1)  # Lets it reach the http call
    logging.info(f"Chat Spawner Finished in {time.time() - start_time}s")


def extract_json_response(text):
    matches = re.findall(r"```json(.*?)```", text, re.DOTALL)

    if len(matches) == 0:
        matches = re.findall(r"```(.*?)```", text, re.DOTALL)
        if len(matches) == 0:
            return None 
        elif len(matches) > 1:
            raise Exception("Found more than 1 json string.")

    json_string = matches[0]
    return json_string

def str_2_json(_str: str) -> str:
    try:
        return json.loads(extract_json_response(_str))
    except:
        return json.loads(_str)

QUERY_SPLITTER_SYSTEM_PROMPT = """As a Query Request Splitter, your role is to break down a user's multiprocessing request into several task instructions, instead of processing it as a single operation. You will be given a snippet of a conversation between a User and an Assistant. 

### Instructions 
- Analyze this conversation carefully to define the multiple tasks. 
- Always prioritize the most recent instruction or request from the user, as well as the latest information provided by the user that will facilitate task performance.
- Structure each query as follows:
"Can you perform action X using the following information Y? Here are some supplementary materials that may help in performing your action: Z can be used to do A"

Your response should be a valid JSON that complies with the schema provided below.
```
{
  "queries": [list of strings - queries or tasks for parallel processing.]
}
```"""

def openai_llm_call(tenant_id: str, system_message: str, user_message: str, model: str = 'gpt-4-turbo', is_json=False) -> Union[dict, str]:
    model_manager = ModelManager()
    model_instance = model_manager.get_model_instance(
        tenant_id=tenant_id,
        model_type=ModelType.LLM,
        provider='openai',
        model=model
    )
    prompt_messages = [
        SystemPromptMessage(content=system_message),
        UserPromptMessage(content=user_message),
    ]

    result = model_instance.invoke_llm(
        prompt_messages=prompt_messages,
        stream=False
    ).message.content
    
    return str_2_json(result) if is_json else result

def split_queries(tenant_id: str, conversation_id:str, app_id:str, query: str) -> List[str]:
    _, history = get_chat_history(conversation_id, app_id)
    if len(history):
        history.append({'role': 'user', 'content' if 'content' in history[0] else 'text': query})
        user_message = json.dumps(history, indent=2)
    else:
        user_message = query
    queries = openai_llm_call(tenant_id, QUERY_SPLITTER_SYSTEM_PROMPT, user_message, is_json = True)
    return queries['queries']


def get_chat_history(conversation_id:str, app_id:str) -> List[Dict[str, Any]]:
    if not conversation_id:
        return None, []
    conversation = db.session.query(Conversation).filter(
        Conversation.app_id == app_id,
        Conversation.id == conversation_id
    ).first()

    if len(conversation.messages):
        logging.info(f"{conversation.messages[-1].message}")
        history = conversation.messages[-1].message if conversation.messages[-1].message else conversation.messages[-2].message
        history = history[1:] if history[0]['role'] == 'system' else history
        history = [{k:v for k, v in message.items() if k in ['role', 'content', 'text']} for message in history]
        return conversation.summary, history
    else:
        return conversation.summary, []

def trigger_ase(procedure: str, inputs: dict):
    API_KEY = os.environ.get("ENG_ASE_API_KEY")
    CALLBACK_SERVICE_API_KEY = os.environ.get("CALLBACK_SERVICE_API_KEY")

    ase_url = "https://wbkktudmnocpkxe35tx62majaa0tnokz.lambda-url.us-east-1.on.aws/"
    ase_request_headers = {"X-Api-Key": API_KEY}
    callback_service_endpoint = "https://48j93p3119.execute-api.us-east-1.amazonaws.com/api"
    callback_request_headers = {"Authorization": f"Basic {CALLBACK_SERVICE_API_KEY}"}

    # Generate conversation ID 
    response = requests.post(url=f"{callback_service_endpoint}/callback", headers=callback_request_headers)
    response.raise_for_status()
    callback_id = response.json()['id']
    logging.info(f"Generate callback ID is: {callback_id}")

    # Invoke the ASE
    data = {
        "procedure": procedure,
        "inputs": inputs,
        "async": True,
        "callbackUrl": f"{callback_service_endpoint}/callback/{callback_id}"
    }
    logging.info(f"Triggering ASE with data: {data}")
    response = requests.post(ase_url, headers=ase_request_headers, json=data)
    response.raise_for_status()

    # Poll the callback service for ASE response
    pending_retries = 100
    while pending_retries > 0:
        response = requests.get(url=f"{callback_service_endpoint}/callback/{callback_id}", headers=callback_request_headers)
        response.raise_for_status()
        response_dict = response.json()
        if response_dict['status'] == 'COMPLETED':
            output = response_dict['output']
            logging.info(f"Response from ASE is: {output}")
            return output.get("answer", output.get("error", "Something went wrong"))
        time.sleep(30)
        pending_retries -= 1
    return "ASE timed out"

class ASEToolModel(BaseModel):
    artifactUrls: Union[List[str], str]
    productName: str
    dryRun: bool = True

    @validator('artifactUrls', pre=True)
    def parse_artifact_urls(cls, v):
        if isinstance(v, str):
            try:
                urls_list = [e.strip() for e in v.split(',') if e.strip()]
            except:
                return v
            if len(urls_list) == 0:
              raise ValueError(f"Recieved no artifactUrls. {v}")
            return urls_list[0] if len(urls_list) == 1 else urls_list