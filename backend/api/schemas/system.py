from pydantic import BaseModel


class OkResponse(BaseModel):
    msg: str = "OK"
