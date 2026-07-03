from framework.registry import EXTRACTORS


class ExtractFactory:

    @staticmethod
    def get_extractor(source):

        return EXTRACTORS[source]()