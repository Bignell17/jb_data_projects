class Pipeline:

    def run(self):

        extractor = ExtractFactory.get_extractor(
            self.config["source"]["type"]
        )

        data = extractor.extract(self.config["source"])

        ...