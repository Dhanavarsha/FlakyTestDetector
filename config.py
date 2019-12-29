import yaml

class Config:

    def __init__(self, config_file):
        self.config = yaml.load(config_file, Loader=yaml.FullLoader)
    
    def __getattr__(self, key):
        return self.config[key]