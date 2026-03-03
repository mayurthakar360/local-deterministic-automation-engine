# shared/tool_registry.py

import re


# ---------------- PARAMETER EXTRACTORS ----------------

def extract_create_folder(action_text, context):
    match_named = re.search(r"named\s+([a-zA-Z0-9_\-]+)", action_text)
    match_sub = re.search(r"subfolder\s+([a-zA-Z0-9_\-]+)", action_text)

    if match_named:
        folder_name = match_named.group(1)
    elif match_sub:
        folder_name = match_sub.group(1)
    else:
        return None

    if context.current_path:
        path = f"{context.current_path}/{folder_name}"
    else:
        path = f"Downloads/{folder_name}"

    return {"path": path}


def extract_list_files(action_text, context):
    match = re.search(r"folder\s+([a-zA-Z0-9_\-]+)", action_text)
    if not match:
        return None

    folder_name = match.group(1)

    if context.current_path:
        path = f"{context.current_path}/{folder_name}"
    else:
        path = f"Downloads/{folder_name}"

    return {"path": path}


def extract_delete_file(action_text, context):
    match = re.search(r"file\s+([a-zA-Z0-9_\-\.]+)", action_text)
    if not match:
        return None

    file_name = match.group(1)

    if context.current_path:
        path = f"{context.current_path}/{file_name}"
    else:
        path = f"Downloads/{file_name}"

    return {"path": path}


# ---------------- SHARED TOOL REGISTRY ----------------

TOOL_REGISTRY = {
    "create_folder": {
        "risk_level": "Medium",
        "patterns": [
            r"create.*folder",
            r"create.*subfolder"
        ],
        "extractor": extract_create_folder
    },
    "list_files": {
        "risk_level": "Low",
        "patterns": [
            r"list.*folder"
        ],
        "extractor": extract_list_files
    },
    "delete_file": {
        "risk_level": "High",
        "patterns": [
            r"delete.*file"
        ],
        "extractor": extract_delete_file
    }
}