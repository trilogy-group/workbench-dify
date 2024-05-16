from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
import ast
import logging
import json
import traceback
from typing import Any, Dict, List, Union
import os
import requests
from core.tools.provider.builtin.eng_ases.tools.utils import trigger_ase, ASEToolModel
from pydantic import BaseModel, validator
from typing import List, Union


class ASEToolResearchQC(BuiltinTool):
    def _invoke(self, 
                user_id: str,
               tool_parameters: Dict[str, Any], 
        ) -> Union[ToolInvokeMessage, List[ToolInvokeMessage]]:
        """
            invoke tools
        """ 
        try:
            logging.info(f"Research QC ASE Recieved {tool_parameters}")

            ase_inputs = ASEToolModel(**tool_parameters)
            response = trigger_ase("maint_research_qc", ase_inputs.dict())
            return self.create_text_message(text=response)

        except Exception as e:
            logging.info(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Research QC ASE Failed. {e}")