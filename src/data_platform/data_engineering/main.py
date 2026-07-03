from framework.config_loader import load_config
from framework.pipeline import Pipeline

config = load_config("src/data_platform/data_engineering/metadata/abfs_folder_example.yaml")
print(config)
# pipeline = Pipeline(config)
# pipeline.run()