class TestIdentifier:
    def __init__(self, class_name, test_name):
        if class_name is None or test_name is None:
            raise ValueError("class_name and test_name must be non-null")
        self.class_name = class_name
        self.test_name = test_name

    def get_class_name(self):
        return self.class_name

    def get_test_name(self):
        return self.test_name

    def __eq__(self, other):
        if not isinstance(other, TestIdentifier):
            return False
        return self.class_name == other.class_name and self.test_name == other.test_name

    def __hash__(self):
        return hash((self.class_name, self.test_name))

    def __str__(self):
        return f"{self.class_name}#{self.test_name}"
