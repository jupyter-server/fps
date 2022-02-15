import asyncio
import atexit
import json
import sys

from rich.table import Table
from textual import events
from textual.app import App
from textual.widgets import ScrollView

FPS = None


def stop_fps():
    if FPS is not None:
        FPS.terminate()


atexit.register(stop_fps)


class Dashboard(App):
    """An example of a very simple Textual App"""

    async def on_load(self, event: events.Load) -> None:
        await self.bind("q", "quit", "Quit")

    async def on_mount(self, event: events.Mount) -> None:

        self.body = body = ScrollView(auto_width=True)

        await self.view.dock(body)

        async def add_content():
            global FPS
            cmd = ["fps-uvicorn", "--fps.show_endpoints"] + sys.argv[1:]
            FPS = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            queue = asyncio.Queue()
            asyncio.create_task(get_log(queue))
            endpoint_marker = "ENDPOINT:"
            endpoints = []
            get_endpoint = False
            while True:
                line = await queue.get()
                if endpoint_marker in line:
                    get_endpoint = True
                elif get_endpoint:
                    break
                if get_endpoint:
                    i = line.find(endpoint_marker) + len(endpoint_marker)
                    line = line[i:].strip()
                    if not line:
                        break
                    endpoint = json.loads(line)
                    endpoints.append(endpoint)

            table = Table(title="API Summary")
            table.add_column("Path", justify="left", style="cyan", no_wrap=True)
            table.add_column("Methods", justify="right", style="green")
            table.add_column("Plugin", style="magenta")

            for endpoint in endpoints:
                path = endpoint["path"]
                methods = ", ".join(endpoint["methods"])
                plugin = ", ".join(endpoint["plugin"])
                if "WEBSOCKET" in methods:
                    path = f"[cyan on red]{path}[/]"
                table.add_row(path, methods, plugin)

            await body.update(table)

        await self.call_later(add_content)


async def get_log(queue):
    while True:
        line = await FPS.stderr.readline()
        if line:
            await queue.put(line.decode().strip())
        else:
            break
