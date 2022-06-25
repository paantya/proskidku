import json

def load(file):
    with open(file, 'r') as f:
        data = json.load(f)
    return data


def save(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
