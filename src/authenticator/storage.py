import json 
from pathlib import Path

class Storage:
    def __init__(self):
        self.file_path = Path.home() / ".authenticator_keys.json"
    
    def load(self):
        if not self.file_path.exists():
            return {}
        with open(self.file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save(self, data):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    def add(self, name, secret):
        data = self.load()
        data[name] = secret
        self.save(data)
        return True
    
    def rename(self, old_name, new_name):
        data = self.load()
        if old_name in data:
            data[new_name] = data.pop(old_name)
            self.save(data)
            return True
        return False
    def delete(self, name):
        data = self.load()
        if name in data:
            del data[name]
            self.save(data)
            return True
        return False
    
    def list_keys(self):
        return self.load()
    

