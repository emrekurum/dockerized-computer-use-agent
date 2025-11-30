from typing import Any, Literal

from .base import BaseAnthropicTool
from .bash import BashTool20241022, BashTool20250124
from .computer import ComputerTool20241022, ComputerTool20250124
from .edit import EditTool20241022, EditTool20250124

# Versiyon tipini güncelledik
ToolVersion = Literal["computer_use_20241022", "computer_use_20250124"]

class ToolGroup:
    def __init__(
        self,
        name: str,
        computer_tool_class: type[BaseAnthropicTool],
        edit_tool_class: type[BaseAnthropicTool],
        bash_tool_class: type[BaseAnthropicTool],
        beta_flag: str | None = None,
    ):
        self.name = name
        self.computer_tool_class = computer_tool_class
        self.edit_tool_class = edit_tool_class
        self.bash_tool_class = bash_tool_class
        self.beta_flag = beta_flag

    @property
    def tools(self) -> list[BaseAnthropicTool]:
        return [
            self.computer_tool_class(),
            self.edit_tool_class(),
            self.bash_tool_class(),
        ]

TOOL_GROUPS_BY_VERSION = {
    "computer_use_20241022": ToolGroup(
        "computer_use_20241022",
        ComputerTool20241022,
        EditTool20241022,
        BashTool20241022,
        beta_flag="computer-use-2024-10-22",
    ),
    "computer_use_20250124": ToolGroup(
        "computer_use_20250124",
        ComputerTool20250124,
        EditTool20250124,
        BashTool20250124,
        beta_flag="computer-use-2025-01-24",
    ),
}
