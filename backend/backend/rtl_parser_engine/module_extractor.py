from .rtl_parser import RTLParser


class ModuleExtractor:

    def __init__(self, filepath):
        self.filepath = filepath
        self.modules = []

    def extract(self):
        parser = RTLParser(self.filepath)
        parser.parse_file()
        self.modules = parser.extract_modules()
        return [module["module_name"] for module in self.modules]

    def get_full_module_data(self):
        return self.modules


if __name__ == "__main__":
    extractor = ModuleExtractor("example.v")
    modules = extractor.extract()

    print("\nDetected Modules:\n")
    for module in modules:
        print(module)
