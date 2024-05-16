import logging
from pydantic import BaseModel, validator
from typing import List, Union, Dict, Any
import traceback
import json
import asyncio
from typing import Any, Dict, List, Union
from core.tools.provider.builtin.eng_ases.tools.chat_spawner_utils import spawn_chats, split_queries
from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage

class ChatSpawnerModel(BaseModel):
    tenant_id: str
    request_info: Dict[str, Any]

    @validator('request_info', pre=True)
    def parse_request_info(cls, v):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            raise ValueError("request_info must be a valid JSON string")


class ChatSpawnerTool(BuiltinTool):
    def _invoke(self, 
                user_id: str,
                tool_parameters: Dict[str, Any]
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        try:
            logging.info(f"Chat Spawner {tool_parameters}")
            inputs = ChatSpawnerModel(**tool_parameters)

            queries = split_queries(inputs.tenant_id, 
                inputs.request_info['request_body']['conversation_id'], 
                inputs.request_info['app_id'], inputs.request_info['query'])
            logging.info(f"Query splitter result: {queries}")

            asyncio.run(spawn_chats(inputs.request_info, queries))

            return self.create_text_message(text=f"Having recieved a multiprocessing request, I created {len(queries)} chats with a unique task running in each.")
        except Exception as e:
            logging.info(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"ChatSpawner Failed. {e}")