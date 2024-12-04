import pydantic


class ScheduleMessage(pydantic.BaseModel):
    id: int
    content: int


class AcknowledgeMessage(pydantic.BaseModel):
    id: int
    status: str


class ResultMessage(pydantic.BaseModel):
    id: int
    result: str


class ErrorMessage(pydantic.BaseModel):
    id: int
    error: str


class RootMessage(pydantic.RootModel):
    root: ScheduleMessage

class ReplyMessage(pydantic.RootModel):
    root: AcknowledgeMessage | ErrorMessage | ResultMessage
