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


class YUMReposException(MyException):
    def __str__(self):
        return f"Error fetching YUM repos: {str(self.msg)}"
