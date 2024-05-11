from typing import Dict, List
import httpx
from typing import Dict
import asyncio
import logging
import time
from openai import OpenAI
import json 
import re
from tenacity import retry, stop_after_attempt, wait_fixed

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
    
    async with httpx.AsyncClient(timeout=httpx.Timeout(3.0, read=10.0), http2=True) as client:
        response = await client.post(request_model["url"].replace('http', 'https'), json=body, headers=headers)
    

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

system_message = """You are a query request splitter. Your role is to divide a user's multiprocessing request into multiple task instructions, rather than treating it as a batch operation. 

You need to respond with a valid JSON that adheres to the schema provided below.

```
{
  "queries": [list of strings - queries or tasks for parallel processing.]
}
```

Each query should be structured as follows:
"Can you perform action X using the following information Y? Here are some supplementary materials that may help in performing your action: Z can be used to do A"
For your information, if supplementary material is not provided, do not mention it."""

def split_queries(query: str) -> List[str]:
    client = OpenAI()
    
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": query}
        ]
    )

    response = completion.choices[0].message.content
    return str_2_json(response)['queries']