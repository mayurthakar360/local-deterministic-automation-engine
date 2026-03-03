import os
import importlib.util


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGINS_DIR = os.path.join(BASE_DIR, "plugins")


def is_valid_tool_definition(tool_data):
    required_keys = {"risk_level", "patterns", "extractor", "executor"}

    if not isinstance(tool_data, dict):
        return False

    if not required_keys.issubset(tool_data.keys()):
        return False

    if not isinstance(tool_data["patterns"], list):
        return False

    if not callable(tool_data["extractor"]):
        return False

    if not callable(tool_data["executor"]):
        return False

    return True


def load_plugins():
    registry = {}

    if not os.path.exists(PLUGINS_DIR):
        return registry

    for plugin_folder in os.listdir(PLUGINS_DIR):

        plugin_path = os.path.join(PLUGINS_DIR, plugin_folder)
        plugin_file = os.path.join(plugin_path, "plugin.py")

        if not os.path.isdir(plugin_path):
            continue

        if not os.path.exists(plugin_file):
            continue

        try:
            spec = importlib.util.spec_from_file_location(
                f"{plugin_folder}.plugin", plugin_file
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            metadata = getattr(module, "PLUGIN_METADATA", None)
            if not metadata:
                continue

            tools = metadata.get("tools", {})

            for tool_name, tool_data in tools.items():

                if not is_valid_tool_definition(tool_data):
                    print(f"[PLUGIN WARNING] Invalid tool ignored: {tool_name}")
                    continue

                registry[tool_name] = tool_data

        except Exception as e:
            print(f"[PLUGIN ERROR] Failed loading '{plugin_folder}': {e}")
            continue

    return registry