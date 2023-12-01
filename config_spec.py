from typing import TypedDict


class GenServerAuth(TypedDict):
    password: str
    save_path: str
    free_only: bool
    custom_sub_folder: bool


class GenServerConfig(TypedDict):
    host: str
    port: int
    max_jobs: int
    min_delay: float
    save_path: str
    token: str
    always_auth: bool
    separate_metadata: bool
    # directly save image to disk without compression or metadata
    save_directly: bool
    # [0, 100]
    compression_quality: int
    # [0, 6]
    compression_method: int
    auth: list[GenServerAuth]
