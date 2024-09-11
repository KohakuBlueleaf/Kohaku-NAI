from pydantic import BaseModel


class GenerateRequest(BaseModel):
    prompt: str
    neg_prompt: str
    seed: int
    scale: float
    width: int
    height: int
    steps: int
    sampler: str
    schedule: str
    smea: bool = False
    dyn: bool = False
    dyn_threshold: bool = False
    cfg_rescale: float = 0.0
    img_sub_folder: str = ""
    extra_infos: str = ""
    priority: int = 1
