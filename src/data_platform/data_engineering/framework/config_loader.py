from pathlib import Path

import yaml


def load_config(config_path):
    """
    Load a YAML configuration file and validate it.
    """

    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    validate_config(config)

    return config


def validate_config(config):
    """
    Validate that all required sections exist.
    """

    required_sections = [
        "pipeline",
        "source",
        "destination",
    ]

    for section in required_sections:
        if section not in config:
            raise ValueError(
                f"Missing required section '{section}' in YAML."
            )