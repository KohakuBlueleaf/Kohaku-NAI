# -*- coding: utf-8 -*-


from typing import Optional

from pydantic import BaseModel, ConfigDict


class TgBotSettings(BaseModel):
    url: str
    password: str
    token: str
    proxy: Optional[str]
    model_config = ConfigDict(extra="ignore")
