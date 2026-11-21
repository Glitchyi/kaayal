from pydantic import BaseModel, ConfigDict, Field


class VoiceReplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utterance: str = Field(min_length=1, max_length=2000)
    interaction_id: str | None = Field(default=None, max_length=120)
    language: str | None = Field(default=None, max_length=32)


class VoiceReplyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reply_text: str
    trace_id: str
