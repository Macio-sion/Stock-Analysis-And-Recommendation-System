"""代码生成结构化输出模型。"""
from pydantic import BaseModel, Field


class AlgorithmInput(BaseModel):
    """自定义算法的一个输入参数定义。"""

    name: str = Field(description="输入参数名，如 technical_score")
    type: str = Field(description="参数类型，如 float")
    description: str = Field(description="参数含义说明")


class AlgorithmOutput(BaseModel):
    """自定义算法的一个输出定义。"""

    name: str = Field(description="输出字段名，如 action")
    type: str = Field(description="输出类型")
    description: str = Field(description="输出含义说明")


class GeneratedCode(BaseModel):
    """LLM 生成的推荐算法代码结构。"""

    code: str = Field(min_length=10, description="完整的可执行 Python 代码")
    language: str = Field(default="python", description="代码语言，固定为 python")
    entry_point: str = Field(default="recommend", description="入口函数名")
    dependencies: list[str] = Field(default_factory=list, description="第三方依赖列表")
    description: str = Field(description="对生成算法的简要说明")
    inputs: list[AlgorithmInput] = Field(default_factory=list, description="算法的输入参数定义")
    outputs: list[AlgorithmOutput] = Field(default_factory=list, description="算法的输出定义")
