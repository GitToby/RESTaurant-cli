import glob
import json
import os
from pathlib import Path
from cyclopts import App
from rich import print

from loguru import logger
from rqstr.schema import HttpResultError, RequestCollection
from textwrap import dedent

app = App(
    name="restaurant",
    help="A dead simple CLI to run HTTP REST requests from a collection file.",
)


@app.command(alias="do")
async def run(
    input_: list[Path] | None = None,
    no_fail_on_error: bool = False,
    output_dir: Path | None = None,
):
    """Scan for request collections in child dirs and run the requests in them."""
    if not input_:
        glob_str = f"{os.getcwd()}/**/*.rest.yml"
        print(f"No input files provided, scanning for files in `{glob_str}`")
        input_ = [Path(p) for p in glob.glob(glob_str, recursive=True)]

    input_ = [p for p in input_ if p.is_file()]
    print(f"Found {len(input_)} collection files.", end="\n\n")

    requests = []
    for collection_file in input_:
        print(f"Loading {collection_file}...", end=" ")
        rc = RequestCollection.from_yml_file(collection_file)
        print("Done.")
        print(f"[bold]{rc.title}[/bold]")
        print(f"Running {len(rc.requests)} requests...")
        requests = await rc.collect()

        for title, request in requests.items():
            print(title, str(request))
            for k, result in enumerate(request.results):
                print(k, str(result))

            if request.benchmark:
                print("Benchmark Results:")
                print(
                    " ".join(f"{k}: {v}" for k, v in request.benchmark_results.items())
                )

        print()

        if output_dir:
            output_file = output_dir / rc.title / "out.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                _ = f.write(rc.model_dump_json(indent=2))

    # Final Status
    if any(isinstance(result, HttpResultError) for result in requests):
        print("[red]Some requests failed.")
        if no_fail_on_error:
            exit(0)
        exit(1)
    else:
        print("[green]All requests succeeded.")


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
