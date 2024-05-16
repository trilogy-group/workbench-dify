from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
from typing import Any, Dict, List, Union
from pydantic import BaseModel, validator
from typing import List, Union
from .ase_utils import trigger_ase

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
               tool_parameters: Dict[str, Any], 
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        """
            invoke tools
        """ 
        ase_inputs = RCAParametersModel(**tool_parameters)
        ase_inputs.dryRun = True
        response_dict = trigger_ase("maint_rca_do", ase_inputs.dict())
        text = response_dict.get("answer", response_dict.get("error", f"Found dict keys: {str(response_dict.keys())}."))
        return self.create_text_message(text=text)