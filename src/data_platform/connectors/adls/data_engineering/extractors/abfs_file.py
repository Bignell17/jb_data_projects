from extractors.base import BaseExtractor

from src.utils.config import read_adls_file

class ABFSFileExtractor(BaseExtractor):

    def extract(self, **kwargs):

        file_client = kwargs["file_client"]
        file_name = kwargs["file_name"]

        return read_adls_file(
            file_client=file_client,
            file_name=file_name
        )