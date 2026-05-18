import json

from pathlib import Path


##
# Retrieves filepaths for configurations and secrets.
#
# author: mjhwa@yahoo.com
##
def get_filepath(category, item): 
  # 1. Dynamically locate the project root relative to this script
  project_root = Path(__file__).resolve().parent.parent.parent

  # 2. Load configurations 
  config_path = project_root / './configs/file.json'
  with open(config_path, "r") as f:
    config = json.load(f)

  return project_root / config.get(category).get(item)