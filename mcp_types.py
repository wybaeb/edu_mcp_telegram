from typing import List, Dict, Any, Optional, Union, Literal
from pydantic import BaseModel
from datetime import datetime


class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]


class Resource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class PromptMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: Union[TextContent, str]


class Prompt(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


class ServerCapabilities(BaseModel):
    logging: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None


class InitializeRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str = "initialize"
    params: Dict[str, Any]


class InitializeResult(BaseModel):
    protocolVersion: str
    capabilities: ServerCapabilities
    serverInfo: Dict[str, str]


class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int, None] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None 