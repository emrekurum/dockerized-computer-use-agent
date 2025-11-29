from typing import Any, Literal

from .base import BaseAnthropicTool
from .bash import BashTool20241022
from .computer import ComputerTool20241022
from .edit import EditTool20241022

ToolVersion = Literal["computer_use_20241022"]

class ToolGroup:
    def __init__(
        self,
        name: str,
        computer_tool_class: type[BaseAnthropicTool],
        edit_tool_class: type[BaseAnthropicTool],
        bash_tool_class: type[BaseAnthropicTool],
        beta_flag: str | None = None,  # Eksik olan parametre eklendi
    ):
        self.name = name
        self.computer_tool_class = computer_tool_class
        self.edit_tool_class = edit_tool_class
        self.bash_tool_class = bash_tool_class
        self.beta_flag = beta_flag     # Eksik olan özellik eklendi

    @property  # Fonksiyon yerine özellik (property) olarak erişilmesi sağlandı
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
        beta_flag="computer-use-2024-10-22", # Beta flag değeri atandı
    ),
}