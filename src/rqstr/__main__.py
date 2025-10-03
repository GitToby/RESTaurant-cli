import datetime
import glob
import json
import os
from pathlib import Path
from cyclopts import App
from rich import print

from loguru import logger
from rqstr.const import APP_NAME
from textwrap import dedent
from pydantic_settings import BaseSettings
from rqstr.schema.request import RequestCollection

app = App(
    name=APP_NAME,
    help="A dead simple CLI to run HTTP REST requests from a collection file.",
)


class AppConf(BaseSettings):
    """Settings to control how the internals work"""

    ...


@app.command(alias="do")
async def run(
    input_: list[Path] | None = None,
    fail_on_error: bool = True,
    print_response: bool = True,
):
    """Scan for request collections in child dirs and run the requests in them."""
    if not input_:
        glob_str = f"{os.getcwd()}/**/*.rest.yml"
        print(f"No input files provided, scanning for files in `{glob_str}`")
        input_ = [Path(p) for p in glob.glob(glob_str, recursive=True)]

    input_ = [p for p in input_ if p.is_file()]
    print(f"Found {len(input_)} collection files.", end="\n\n")

    ns = datetime.datetime.now().isoformat()
    for collection_file in input_:
        print(f"Loading {collection_file}...", end=" ")
        rc = RequestCollection.from_yml_file(collection_file)
        print("Done.")
        print(
            f"[bold]{rc.title}[/bold] - Running {len(rc.requests)} requests...", end=" "
        )
        responses = await rc.collect()
        print("Done.")
        rc.std_output.write(ns, rc, responses)
        rc.file_output.write(ns, rc, responses)
        print()


@app.command
def gen_schema():
    """
    Generate the schema for the request collection.

    Use in the yml file to validate the request collection schema:
    `# yaml-language-server: $schema=<pathToTheSchema>/.request_collection_schema.json`
    """
    print(json.dumps(RequestCollection.model_json_schema()))


@app.command
def example_collection(name: str = "example_collection", include_schema: bool = False):
    out_file = Path(os.getcwd()) / f"{name}.rest.yml"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # make schema file
    schema_str = ""
    if include_schema:
        schema_file = out_file.parent / ".request_collection_schema.json"
        with open(schema_file, "w") as f:
            _ = json.dump(RequestCollection.model_json_schema(), f)
        schema_str = f"# yaml-language-server: $schema={schema_file}"

    # make_actual_file
    out_file.touch(exist_ok=False)
    with open(out_file, "w") as f:
        _ = f.write(
            dedent(f"""
                {schema_str}
                title: {name}
                requests:
                  example_one:
                    method: GET
                    url: "https://api.ipify.org/"
            """).strip()
        )


def main():
    logger.remove()
    _ = logger.add("restaurant_output.log")

    app()
