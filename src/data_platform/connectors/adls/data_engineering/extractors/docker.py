from extractors.base import BaseExtractor

from src.utils.config import read_docker_file


class DockerExtractor(BaseExtractor):

    def extract(self, **kwargs):

        bucket = kwargs["bucket"]
        file_key = kwargs["file_key"]

        return read_docker_file(
            bucket_name=bucket,
            file_key=file_key
        )