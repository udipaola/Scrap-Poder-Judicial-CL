import json
from filelock import FileLock

def update_checkpoint(checkpoint_file, task_id, data):
    lock = FileLock(f"{checkpoint_file}.lock")
    with lock:
        try:
            with open(checkpoint_file, 'r+') as f:
                checkpoint_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            checkpoint_data = {}

        checkpoint_data[task_id] = data

        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=4)