import logging
from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.provider.builtin.eng_ases.tools.utils import trigger_ase, ASEToolModel
import ast
import json
from typing import Any, Dict, List, Union
import os
import requests
from pydantic import BaseModel, validator
from typing import List, Union
import traceback


class ASEToolFixQC(BuiltinTool):
    def _invoke(self, 
                user_id: str,
                tool_parameters: Dict[str, Any]
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        
        try:
            logging.info(f"Fix QC ASE Recieved {tool_parameters}")

            ase_inputs = ASEToolModel(**tool_parameters)
            response = trigger_ase("maint_fix_qc", ase_inputs.dict())
            return self.create_text_message(text=response)
        except Exception as e:
            logging.info(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed Fix QC Run. {e}")