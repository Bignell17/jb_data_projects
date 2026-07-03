from framework.config_loader import load_config
from framework.pipeline import Pipeline

config = load_config("metadata/customer.yml")
print(config)
# pipeline = Pipeline(config)
# pipeline.run()