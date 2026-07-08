from typing import Dict, Optional, List
from pydantic import BaseModel

class UserFormData(BaseModel):
    user_id: int
    category_id: int
    category_name: str
    fields: Dict[str, str] = {}
    current_field_index: int = 0
    total_fields: int = 0
    form_structure: Dict = {}
    cookies_buffer: str = ''

user_forms: Dict[int, UserFormData] = {}

class UserManagementState(BaseModel):
    user_id: int
    action: str
    items: List[int] = []
    current_step: str = 'waiting_for_selection'
    value: Optional[str] = None
