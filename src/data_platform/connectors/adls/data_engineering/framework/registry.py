from extractors.abfs_file import ABFSFileExtractor
from extractors.abfs_folder import ABFSFolderExtractor
from extractors.docker import DockerExtractor


EXTRACTORS = {

    "abfs_file": ABFSFileExtractor,

    "abfs_folder": ABFSFolderExtractor,

    "docker": DockerExtractor,

}