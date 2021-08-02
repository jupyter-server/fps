import typer
import uvicorn


app = typer.Typer()

@app.command()
def create(
    path: str = typer.Argument(...,
        help=(
            "Some text"
        ),
    ),
):
    print(path)

@app.command()
def run(w: int = 1):
    uvicorn.run("fps.main:app", workers=w)