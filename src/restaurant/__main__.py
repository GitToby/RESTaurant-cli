import glob
import os
from pathlib import Path
from cyclopts import App
from rich import print

from restaurant.schema import RequestCollection

app = App(
    name="RESTaurant",
    help="A  dead simple CLI to run HTTP requests from a collection file.",
)


@app.command
async def run(
    input_: list[Path] | None = None,
    no_fail_on_error: bool = False,
):
    """Scan for request collections in child dirs and run the requests in them."""
    if not input_:
        glob_str = f"{os.getcwd()}/**/*.rest.yml"
        print(f"No input files provided, scanning for files in `{glob_str}`")
        input_ = [Path(p) for p in glob.glob(glob_str, recursive=True)]
        input_ = [p for p in input_ if p.is_file()]

    print(f"Found {len(input_)} collection files.", end="\n\n")

    failed = False
    for i, collection_file in enumerate(input_):
        count_str = f"[{i + 1}/{len(input_)}]"
        print(f"{count_str} Loading {collection_file}...", end=" ")
        rc = RequestCollection.load_from_file(collection_file)
        print("Done.")
        print(f"{count_str} [bold]{rc.title}[/bold]")
        print(f"{count_str} Running {len(rc.requests)} requests...")
        results = await rc.execute()

        for result in results:
            if not result.was_success:
                failed = True
            print(f"{count_str} {result.pretty_str}")

        print()
    # Final Status
    if failed:
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
    print(RequestCollection.model_json_schema())


def main():
    app()
