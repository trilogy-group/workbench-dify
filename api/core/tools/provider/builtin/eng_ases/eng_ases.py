from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError

from typing import Any, Dict

class EngineeringASEProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        try:
            print(123)
        except Exception as e:
            raise ToolProviderCredentialValidationError(str(e))