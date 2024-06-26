class MyException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return str(self.msg)


class ConfigException(MyException):
    def __str__(self):
        return f"Configuration file error: {str(self.msg)}"


class PackageException(MyException):
    pass


class POEMException(MyException):
    def __str__(self):
        return f"Error fetching YUM repos: {str(self.msg)}"


class MergingException(MyException):
    def __str__(self):
        return f"Error merging POEM data: {str(self.msg)}"
