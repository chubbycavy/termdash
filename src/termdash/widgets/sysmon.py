"""CPU and memory monitor tile."""

from __future__ import annotations

import psutil
from pydantic import BaseModel, ConfigDict, Field
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import VerticalGroup
from textual.widgets import Label, Static

from termdash.widgets.common import TILE_CSS
from termdash.widgets.registry import register


class SysMonOptions(BaseModel):
    """Options for the sysmon widget."""

    model_config = ConfigDict(extra="forbid")

    interval: float = Field(default=1.0, gt=0, le=60)
    history: int = Field(default=38, ge=2, le=200)


class HistoryGraph(Static):
    """Threshold-coloured bar graph of the latest samples."""

    BARS = "▁▂▃▄▅▆▇█"

    def __init__(
        self,
        *,
        green_below: float = 60.0,
        yellow_below: float = 85.0,
        history: int = 38,
        **kwargs,
    ) -> None:
        super().__init__("", **kwargs)
        self.green_below = green_below
        self.yellow_below = yellow_below
        self.history_size = history
        self.samples: list[float] = []

    def add_sample(self, value: float) -> None:
        self.samples = [*self.samples, max(0.0, min(100.0, value))][
            -self.history_size :
        ]
        graph = Text()
        for sample in self.samples:
            index = min(len(self.BARS) - 1, int(sample / 100 * len(self.BARS)))
            graph.append(self.BARS[index], style=self.colour_for(sample))
        self.update(graph)

    def colour_for(self, value: float) -> str:
        if value < self.green_below:
            return "green"
        if value < self.yellow_below:
            return "yellow"
        return "red"


@register("sysmon", SysMonOptions)
class SysMon(VerticalGroup):
    """CPU and memory utilisation with threshold-coloured history graphs."""

    interval = 1.0
    history = 38

    DEFAULT_CSS = f"""
    SysMon {{
        {TILE_CSS}
        align: center middle;
    }}

    SysMon .metric-label,
    SysMon .caption {{
        width: 100%;
        height: 1;
        text-align: center;
    }}

    SysMon .metric-label {{
        text-style: bold;
    }}

    SysMon HistoryGraph {{
        width: 100%;
        height: 2;
        text-align: right;
    }}

    SysMon .caption {{
        color: $text-muted;
        text-style: bold;
    }}
    """

    def compose(self) -> ComposeResult:
        yield Label("", id="cpu-label", classes="metric-label", markup=False)
        yield HistoryGraph(
            id="cpu-graph", history=self.history, green_below=60, yellow_below=85
        )
        yield Label("", id="mem-label", classes="metric-label", markup=False)
        yield HistoryGraph(
            id="mem-graph", history=self.history, green_below=80, yellow_below=95
        )
        yield Label("System Monitor", classes="caption", markup=False)

    def on_mount(self) -> None:
        self.sample()
        self.set_interval(self.interval, self.sample)

    def cpu_percent(self) -> float:
        return psutil.cpu_percent(interval=None)

    def mem_percent(self) -> float:
        return psutil.virtual_memory().percent

    def sample(self) -> None:
        cpu = self.cpu_percent()
        mem = self.mem_percent()
        self.query_one("#cpu-label", Label).update(f"CPU {cpu:.0f}%")
        self.query_one("#cpu-graph", HistoryGraph).add_sample(cpu)
        self.query_one("#mem-label", Label).update(f"MEM {mem:.0f}%")
        self.query_one("#mem-graph", HistoryGraph).add_sample(mem)
