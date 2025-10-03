from __future__ import annotations
from abc import ABCMeta, abstractmethod
from collections.abc import Mapping
from rich import print
from pathlib import Path
from typing import TYPE_CHECKING, override
from pydantic import BaseModel, Field

from rqstr.const import DEFAULT_OUT_DIR

if TYPE_CHECKING:
    from rqstr.schema.request import RequestCollection, ResponseCollection


class OutputConf(BaseModel, metaclass=ABCMeta):
    enabled: bool = True

    @abstractmethod
    def write(
        self,
        namespace: str,
        collection: RequestCollection,
        responses: Mapping[str, ResponseCollection],
        include_output: bool = False,
    ) -> None: ...


class StdOutOutput(OutputConf):
    @override
    def write(
        self,
        namespace: str,
        collection: RequestCollection,
        responses: Mapping[str, ResponseCollection],
        include_output: bool = False,
    ):
        for i, (req_name, responses_) in enumerate(responses.items()):
            for response in responses_.responses:
                print(f" [{i + 1}/{len(responses)}] - {req_name:<30} | {response}")
                if include_output:
                    print(f"  {response.response_text}")


class FileOutput(OutputConf):
    output_dir: Path = Field(default_factory=lambda: Path(DEFAULT_OUT_DIR))

    @override
    def write(
        self,
        namespace: str,
        collection: RequestCollection,
        responses: Mapping[str, ResponseCollection],
        include_output: bool = False,
    ):
        if not self.enabled:
            return

        output_dir = self.output_dir / collection.title / namespace
        output_dir.mkdir(parents=True, exist_ok=True)
        for req_name, response in responses.items():
            file = output_dir / f"{req_name}.json"
            with open(file, "w") as f:
                _ = f.write(
                    response.model_dump_json(
                        indent=True, exclude_none=True, exclude_defaults=True
                    )
                )

        print(f"Files written to '{output_dir}'")
