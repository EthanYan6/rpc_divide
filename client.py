from services import ClientStub
from services import Channel
from services import InvalidOpreation


# 创建与服务器的连接
channel = Channel('127.0.0.1', 8000)

# 创建用于RPC调用的工具
stub = ClientStub(channel)

for i in range(5):
    # 进行调用
    try:
        # val = stub.divide(200, 100)
        # val = stub.divide(i*100, 50)
        # val = stub.divide(i*100)
        val = stub.divide(i*100, 0)

    except InvalidOpreation as e:
        print(e.message)
    else:
        print(val)