import os
import glob
import yaml

from tinychain.utils import printd

def load_yaml_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)

def load_all_presets():
    script_directory = os.path.dirname(os.path.abspath(__file__))
    # printd(script_directory)
    example_path_pattern = os.path.join(script_directory, "examples", "*.yaml")
    example_yaml_files = glob.glob(example_path_pattern)

    all_yaml_files = example_yaml_files

    all_yaml_data = {}
    for file_path in all_yaml_files:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        data = load_yaml_file(file_path)
        all_yaml_data[base_name] = data
    return all_yaml_data

if __name__ == "__main__":
    res =  load_all_presets()
    printd(res)