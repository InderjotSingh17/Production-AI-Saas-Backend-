from datetime import datetime
from pydantic import BaseModel, Field,ConfigDict
class ConversationCreate(BaseModel):
    title:str=Field(default="New Conversation",min_length=1,max_length=255)

class ConversationResponse(BaseModel):
    id:int
    title:str
    user_id:int
    created_at:datetime
    model_config=ConfigDict(from_attributes=True)

class MessageCreate(BaseModel):
    content:str=Field(min_length=1,max_length=10000)

class MessageResponse(BaseModel):
    id:int
    conversation_id:int
    role:str
    content:str
    created_at:datetime
    model_config=ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    user_message:MessageResponse
    assistant_message:MessageResponse