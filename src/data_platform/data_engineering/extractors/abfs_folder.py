from extractors.base import BaseExtractor

from src.utils.config import read_adls_folder


class ABFSFolderExtractor(BaseExtractor):

    def extract(self, **kwargs):

        service_client = kwargs["service_client"]
        container = kwargs["container"]
        folder = kwargs["folder"]

        return read_adls_folder(
            service_client=service_client,
            container_name=container,
            folder_path=folder
        )