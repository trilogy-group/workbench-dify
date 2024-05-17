import logging
from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
import ast
import json
from typing import Any, Dict, List, Union
import os
import requests
from pydantic import BaseModel, validator
from typing import List, Union
import traceback
API_KEY = os.environ.get("ENG_ASE_API_KEY")

class RCAParametersModel(BaseModel):
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


class ASEToolRCA(BuiltinTool):
    def _invoke(self, 
                user_id: str,
                tool_parameters: Dict[str, Any]
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        try:
            logging.info(f"RCA ASE {tool_parameters}")
            ase_inputs = RCAParametersModel(**tool_parameters)
            ase_inputs.dryRun = True

            response = trigger_ase("maint_rca_do", ase_inputs.dict())
            try:
                response_dict = json.loads(response.text)
                text = response_dict.get("answer", response_dict.get("error", f"Found dict keys: {str(response_dict.keys())}."))
            except:
                text = response.text
            return self.create_text_message(text=f"Status: {response.status_code}. {text}")
        except Exception as e:
            logging.info(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"FAILED RCA RUN. {e}")


def trigger_ase(procedure: str, inputs: dict):
    url = "https://wbkktudmnocpkxe35tx62majaa0tnokz.lambda-url.us-east-1.on.aws/"
    headers = {
        "X-Api-Key": API_KEY
    }
    data = {
        "procedure": procedure,
        "inputs": inputs
    }
    print(f"Triggering ASE with data: {data}")
    response = requests.post(url, headers=headers, json=data)
    print(f"Response: {response}")
    return response 