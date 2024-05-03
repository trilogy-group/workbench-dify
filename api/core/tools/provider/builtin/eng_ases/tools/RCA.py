from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage

import json
from typing import Any, Dict, List, Union
import os
import requests
API_KEY = os.environ.get("ENG_ASE_API_KEY")

class ASEToolRCA(BuiltinTool):
    def _invoke(self, 
                user_id: str,
               tool_parameters: Dict[str, Any], 
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        """
            invoke tools
        """ 
        response = trigger_ase("maint_rca_do", {
            "artifactUrls": tool_parameters.get('artifactUrls'),
            "productName": tool_parameters.get('productName'),
            "dryRun": True # tool_parameters.get('dryRun', True) 
        })
        try:
            response_dict = json.loads(response.text)
            text = response_dict.get("answer", response_dict.get("error", f"Found dict keys: {str(response_dict.keys())}."))
        except:
            text = response.text
        return self.create_text_message(text=f"Status: {response.status_code}. {text}")


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