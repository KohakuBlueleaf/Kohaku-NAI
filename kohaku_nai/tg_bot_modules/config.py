# -*- coding: utf-8 -*-
# @Time    : 2023/12/22 下午11:36

from typing import Optional

from pydantic import BaseModel, ConfigDict


class TgBotSettings(BaseModel):
    url: str
    password: str
    token: str
    proxy: Optional[str]
    model_config = ConfigDict(extra="ignore")
