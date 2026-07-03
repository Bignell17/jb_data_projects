from abc import ABC, abstractmethod


class BaseExtractor(ABC):

    @abstractmethod
    def extract(self, **kwargs):
        """Extract data from a source."""
        pass