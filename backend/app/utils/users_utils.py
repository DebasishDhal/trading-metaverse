import random
import uuid
from pydantic import BaseModel, Field
#import optional
from typing import Optional, List

#Create a 6 digit random alphanumeric UUID

class UserSignupSchema(BaseModel):
    username : str
    password : str
    admin : Optional[bool] = False

class UserLoginSchema(BaseModel):
    username : str
    password : str
    admin : Optional[bool] = False


def generate_uuid():
    return str(uuid.uuid4().hex)[:8]