"""Pydanticモデルで共有する厳格な基底クラス。"""

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """変更不可かつ未定義フィールドを拒否する値モデル。"""

    model_config = ConfigDict(frozen=True, extra="forbid")


class FrozenArbitraryModel(FrozenModel):
    """外部ライブラリの型を保持できる変更不可モデル。"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
