from typing import Annotated, Dict, Any
from pathlib import Path
import logging
import json
import os

from rich import print
from github import Github, Auth
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import typer

APP_NAME = "pen"

middleware = [Middleware(SessionMiddleware, secret_key="this_doesnt_matter")]
server = FastAPI(middleware=middleware)
app = typer.Typer()

uvicorn_error = logging.getLogger("uvicorn.error")
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_default = logging.getLogger("uvicorn")
uvicorn_error.disabled = True
uvicorn_access.disabled = True
uvicorn_default.disabled = True


def flash(request: Request, message: Any, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
        request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


templates = Jinja2Templates(directory="templates")
templates.env.globals["get_flashed_messages"] = get_flashed_messages


def check_config_file():
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"
    return config_path.is_file()


def get_config_file() -> Dict:
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"
    path_string = str(config_path)

    with open(path_string) as f:
        return json.load(f)


def get_access_token() -> str:
    config_file = get_config_file()

    return config_file["github_access_token"]


def get_config_file_path() -> str:
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"
    path_string = str(config_path)

    return path_string


@server.get("/", response_class=HTMLResponse)
def root(request: Request):
    config_file = get_config_file()

    return templates.TemplateResponse(
        "home.html", {"request": request, "repos": config_file["repos"]}
    )


@server.post("/new")
def new_content(
    request: Request,
    repo: Annotated[str, Form()],
    file_name: Annotated[str, Form()],
    content: Annotated[str, Form()],
):
    access_token = get_access_token()

    auth = Auth.Token(access_token)
    g = Github(auth=auth)

    github_repo = g.get_repo(repo)
    try:
        res = github_repo.create_file(
            path=file_name, message=f"content: {file_name}", content=content
        )
    except:
        flash(
            request=request,
            message="Failed to create and commit file",
            category="error",
        )

        return RedirectResponse("/", status_code=302)

    commit = res["commit"]
    flash(
        request=request,
        message=f"Successfully created and committed new file at {commit.html_url}",
        category="success",
    )

    print(
        f"Created and commited new file at:[link={commit.html_url}]{commit.html_url}[/link]"
    )

    return RedirectResponse("/", status_code=302)


@app.command()
def main():
    print(f"Hello")


@app.command()
def auth(github_access_token: str):
    app_dir = typer.get_app_dir(APP_NAME)
    base_path: Path = Path(app_dir)
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)

    config_path: Path = Path(app_dir) / "config.json"
    if not config_path.is_file():
        print("Config file doesn't exist yet, going to write it")
        path_string = str(config_path)
        with open(path_string, "w", encoding="utf-8") as f:
            json.dump({"github_access_token": github_access_token}, f, indent=4)


@app.command()
def setup(repo: str):
    config_file = get_config_file()

    if "repos" in config_file:
        config_file["repos"].append(repo)
    else:
        config_file["repos"] = [repo]

    path_string = get_config_file_path()
    with open(path_string, "w", encoding="utf-8") as f:
        json.dump(config_file, f, indent=4)


@app.command()
def start():
    if check_config_file():
        print(f"Starting Pen Server on port 8000")
        uvicorn.run(
            server, host="0.0.0.0", port=8000, access_log=False, log_level="error"
        )
    else:
        print(f"Cannot find config file. Run pen auth")


@app.command()
def config():
    if check_config_file():
        config_file = get_config_file()
        print(f"{config_file}")
    else:
        print(f"Cannot find config file")


@app.command()
def reset():
    if check_config_file():
        app_dir = typer.get_app_dir(APP_NAME)
        config_path: Path = Path(app_dir) / "config.json"
        path_string = str(config_path)
        os.remove(path_string)
    else:
        print(f"Cannot find config file")


if __name__ == "__main__":
    app()
