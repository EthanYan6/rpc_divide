class InvalidOpreation(Exception):
    def __init__(self, message=None):
        # 异常信息如果有指定则按指定输出，没有的话则输出`invalid operation`
        self.message = message or 'invalid operation'


def divide(num1, num2=1):
    """
    除法
    :param num1: int
    :param num2: int
    :return: float
    """
    # 增加判断操作，抛出自定义异常
    if num2 == 0:
        raise InvalidOpreation()
    val = num1 / num2
    return val

try:
    a = divide(200,0)
except InvalidOpreation as e:
    print(e.message)
else:
    print(a)

