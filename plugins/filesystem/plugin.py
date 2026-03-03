import os
import shutil
import re
from pathlib import Path

USER_HOME = os.path.expanduser("~")

# ---------------- PATH VALIDATION ----------------
def validate_path(relative_path: str) -> Path:

    if not relative_path:
        raise Exception("Path missing")

    if ".." in relative_path:
        raise Exception("Path traversal detected")

    if ":" in relative_path:
        raise Exception("Absolute paths not allowed")

    full_path = os.path.normpath(os.path.join(USER_HOME, relative_path))

    if not full_path.startswith(USER_HOME):
        raise Exception("Access outside user directory blocked")

    return Path(full_path)


# ---------------- EXTRACTORS ----------------
def extract_create_folder(action_text, context):
    match = re.search(r"create folder\s+(.+)", action_text)
    if match:
        folder_name = match.group(1).strip()
        return {"path": folder_name}
    return None


def extract_list_files(action_text, context):
    # Support:
    # "list files"
    # "list files in test"
    match = re.search(r"list files(?:\s+in\s+(.+))?", action_text)
    if match:
        folder_name = match.group(1)
        if folder_name:
            return {"path": folder_name.strip()}
        return {"path": "."}
    return None


def extract_delete_file(action_text, context):
    match = re.search(r"delete file\s+(.+)", action_text)
    if match:
        target = match.group(1).strip()
        return {"path": target}
    return None


# ---------------- EXECUTORS ----------------
def list_files_executor(parameters: dict):

    path_obj = validate_path(parameters.get("path"))

    if not path_obj.exists():
        raise Exception("Path does not exist")

    files = [p.name for p in path_obj.iterdir() if p.is_file()]

    return {
        "stdout": "\n".join(files) if files else "",
        "stderr": None
    }


def create_folder_executor(parameters: dict):

    path_obj = validate_path(parameters.get("path"))
    path_obj.mkdir(parents=True, exist_ok=True)

    return {
        "stdout": f"Folder created: {path_obj}",
        "stderr": None
    }


def delete_file_executor(parameters: dict):

    path_obj = validate_path(parameters.get("path"))

    if not path_obj.exists():
        raise Exception("Target does not exist")

    if path_obj.is_file():
        path_obj.unlink()
    else:
        shutil.rmtree(path_obj)

    return {
        "stdout": f"Deleted: {path_obj}",
        "stderr": None
    }


# ---------------- METADATA ----------------
PLUGIN_METADATA = {
    "tools": {
        "list_files": {
            "risk_level": "Low",
            "patterns": [r"list files"],
            "extractor": extract_list_files,
            "executor": list_files_executor
        },
        "create_folder": {
            "risk_level": "Medium",
            "patterns": [r"create folder"],
            "extractor": extract_create_folder,
            "executor": create_folder_executor
        },
        "delete_file": {
            "risk_level": "High",
            "patterns": [r"delete file"],
            "extractor": extract_delete_file,
            "executor": delete_file_executor
        }
    }
}