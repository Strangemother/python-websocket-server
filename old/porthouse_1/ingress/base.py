from .singleton import app

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Optional

# app = FastAPI()

from jinja2 import (Environment, PackageLoader, ChoiceLoader, FileSystemLoader,
    select_autoescape, Template)

from pathlib import Path
import sys

HERE = Path(__file__).parent
sys.path.append(HERE.as_posix())


class JinjaEnvLoaders(object):
    """
    env = loaders.gen_env()
    templ = env.get_template('index.html')
    html = templ.render({"request": request, "id": id})
    """

    def get_loaders(self):
        names = [
            (HERE / 'templates',)
        ]

        fls = tuple(FileSystemLoader(*x) for x in names)
        print('Generating', names)
        return fls

    def gen_env(self):
        fls = self.get_loaders()
        env = Environment(
            loader=ChoiceLoader(fls),
            autoescape=select_autoescape()
        )
        return env


loaders = JinjaEnvLoaders()

def mount_jinja_home(app, index_template='index.html'):
    static_path = HERE / 'static'
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    env = loaders.gen_env()

    @app.get("/", response_class=HTMLResponse)
    async def jinja_home_callback(request: Request, id: Optional[str]=None):
        templ = env.get_template(index_template)
        d = {"request": request, "id": id}
        return templ.render(d)
