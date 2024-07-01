import os

class Config:
    def __init__(self, env_file):
        self.env_file = env_file
        self.load_config()

    def load_config(self):
        from dotenv import load_dotenv
        load_dotenv(self.env_file)

        self.DEBUG = os.getenv('DEBUG')
        self.NER_MODEL_PATH = os.getenv('NER_MODEL_PATH')

class DevConfig(Config):
    def __init__(self):
        super().__init__('env.dev')

class ProdConfig(Config):
    def __init__(self):
        super().__init__('env.prod')    