
from langchain.tools import tool

@tool
def read_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()

@tool
def write_file(path: str, content: str) -> str:
    with open(path, "w") as f:
        f.write(content)
    return "File written"
