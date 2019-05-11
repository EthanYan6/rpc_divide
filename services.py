import socket
import struct
from io import BytesIO


class InvalidOpreation(Exception):
    def __init__(self, message=None):
        # 异常信息如果有指定则按指定输出，没有的话则输出`invalid operation`
        self.message = message or 'invalid operation'


class MethodProtocol(object):
    """
    解读方法名字
    """

    def __init__(self, connection):
        self.conn = connection

    def _read_all(self, size):
        """此处方法同3.read_all方法中实现的代码，因此不再重复书写"""
        # 当然，如果你愿意，直接用类的继承也未尝不可
        if isinstance(self.conn, BytesIO):
            # 只涉及到本地操作，未涉及网络，不需要特殊处理，因为测试代码需要，此处才进行引用
            buff = self.conn.read(size)
            return buff

        else:
            # socket类型数据如何处理
            # 因涉及到网络，获取到的数据未必是所需大小，所以需要判断
            have = 0
            buff = b''
            while have < size:
                chunk = self.conn.recv(size - have)
                buff += chunk
                l = len(chunk)
                have += l

                if l == 0:
                    # 表示客户端socket关闭了
                    raise EOFError()
            return buff

    def get_method_name(self):
        """
        提供方法名
        :return: str 方法名
        """
        # 1.读取字符串长度
        buff = self._read_all(4)
        length = struct.unpack('!I', buff)[0]

        # 2.读取字符串
        buff = self._read_all(length)
        name = buff.decode()
        return name


class DivideProtocol(object):
    """
    divide过程消息协议转换工具
    """

    def args_encode(self, num1, num2=1):
        """
        将原始的调用请求参数转换打包成二进制消息数据
        :param num1: int
        :param num2: int
        :return: bytes 二进制消息数据
        """
        name = 'divide'

        # 处理方法的名字 字符串
        # 处理字符串的长度
        buff = struct.pack('!I', 6)
        # 处理字符
        buff += name.encode()

        # 处理参数1
        # 处理序号
        buff2 = struct.pack('!B', 1)
        # 处理参数值
        buff2 += struct.pack('!i', num1)

        # 处理参数2
        if num2 != 1:
            # 处理序号
            buff2 += struct.pack('!B', 2)
            buff2 += struct.pack('!i', num2)

        # 处理消息长度，边界设定
        length = len(buff2)
        buff += struct.pack('!I', length)

        buff += buff2
        return buff

    def _read_all(self, size):
        """
        帮助我们读取二进制数据
        :param size: 想要读取的二进制数据大小
        :return: 二进制数据 bytes
        """
        # self.conn
        # 读取二进制数据
        # socket.recv(4) => ?4 判断读取的数据是否为4个，直到4个字节我们才进行处理
        # BytesIO.read
        if isinstance(self.conn, BytesIO):
            # 只涉及到本地操作，未涉及网络，不需要特殊处理，因为测试代码需要，此处才进行引用
            buff = self.conn.read(size)
            return buff

        else:
            # socket类型数据如何处理
            # 因涉及到网络，获取到的数据未必是所需大小，所以需要判断
            have = 0
            buff = b''
            while have < size:
                chunk = self.conn.recv(size - have)
                buff += chunk
                l = len(chunk)
                have += l

                if l == 0:
                    # 表示客户端socket关闭了
                    raise EOFError()
            return buff

    def args_decode(self, connection):
        """
        接收调用请求消息数据并进行解析
        :param connection: 连接对象 socket BytesIO
        :return: dict 包含了解析之后的参数
        """
        # 参数长度映射关系
        param_len_map = {
            1: 4,
            2: 4
        }
        # 参数格式映射关系
        param_fmt_map = {
            1: '!i',
            2: '!i'
        }
        # 参数名字映射关系
        param_name_map = {
            1: 'num1',
            2: 'num2'
        }
        # 保存用来返回参数的字典
        # args = {"num1": xxx, "num2": xxx}
        args = {}
        self.conn = connection
        # 处理方法的名字已经提前被处理
        # 后面我们会实现一个方法专门处理不同的调用请求的方法名解析

        # 处理消息边界
        # 读取二进制数据
        # socket.recv(4) => ?4 判断读取的数据是否为4个，直到4个字节我们才进行处理
        # BytesIO.read
        buff = self._read_all(4)
        # 将二进制数据转换为python的数据类型
        length = struct.unpack('!I', buff)[0]

        # 已经读取处理的字节数
        have = 0

        # 处理第一个参数
        # 1.处理参数序号
        buff = self._read_all(1)
        have += 1
        param_seq = struct.unpack('!B', buff)[0]

        # 2.处理参数值
        param_len = param_len_map[param_seq]
        buff = self._read_all(param_len)
        have += param_len
        param_fmt = param_fmt_map[param_seq]
        param = struct.unpack(param_fmt, buff)[0]

        param_name = param_name_map[param_seq]
        args[param_name] = param

        if have >= length:
            return args

        # 处理第二个参数
        # 1.处理参数序号
        buff = self._read_all(1)
        param_seq = struct.unpack('!B', buff)[0]

        # 2.处理参数值
        param_len = param_len_map[param_seq]
        buff = self._read_all(param_len)
        param_fmt = param_fmt_map[param_seq]
        param = struct.unpack(param_fmt, buff)[0]

        param_name = param_name_map[param_seq]
        args[param_name] = param

        return args

    def result_encode(self, result):
        """
        将原始结果数据转换为消息协议二进制数据
        :param result: 原始结果数据 float InvalidOperation
        :return: bytes 消息协议二进制数据
        """
        # 正常
        if isinstance(result, float):
            # 处理返回值类型
            buff = struct.pack('!B', 1)
            buff += struct.pack('!f', result)
            return buff

        # 异常
        else:
            # 处理返回值类型
            buff = struct.pack('!B', 2)
            # 处理返回值
            length = len(result.message)
            # 处理字符串长度
            buff += struct.pack('!I', length)
            # 处理字符
            buff += result.message.encode()
            return buff

    def result_decode(self, connection):
        """
        将返回值消息数据转换为原始返回值
        :param connection: socket BytesIO
        :return: float InvalidOperation对象
        """
        self.conn = connection
        # 处理返回值类型
        buff = self._read_all(1)
        result_type = struct.unpack('!B', buff)[0]

        if result_type == 1:
            # 正常情况
            # 读取float数据
            buff = self._read_all(4)
            val = struct.unpack('!f', buff)[0]
            return val
        else:
            # 异常情况
            # 读取字符串的长度
            buff = self._read_all(4)
            length = struct.unpack('!I', buff)[0]

            # 读取字符串
            buff = self._read_all(length)
            message = buff.decode()

            return InvalidOpreation(message)


class Channel(object):
    """
    用于客户端建立网络连接
    """
    def __init__(self, host, port):
        """
        :param host: 服务器地址
        :param port: 服务器端口号
        """
        self.host = host
        self.port = port

    def get_connection(self):
        """
        获取连接对象
        :return: 与服务器通讯的socket
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((self.host, self.port))
        return sock


class Server(object):
    """
    RPC服务器
    """
    def __init__(self, host, port, handlers):
        # 创建socket的工具对象
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # 设置socket，重用地址
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # 绑定地址
        self.host = host
        self.port = port
        sock.bind((self.host, self.port))
        self.sock = sock
        self.handlers = handlers

    def serve(self):
        """
        开启服务器运行，提供RPC服务
        :return:
        """
        # 1.开启服务器的监听，等待客户端的连接请求
        self.sock.listen(128)

        # 2.接受客户端的连接请求
        while True:
            client_sock, client_addr = self.sock.accept()
            print('与客户端%s建立了链接' % str(client_addr))

            # 3.交给ServerStub，完成客户端的具体的RPC调用请求
            stub = ServerStub(client_sock, self.handlers)
            try:
                while True:
                    stub.process()
            except EOFError:
                # 表示客户端关闭了连接：
                print('客户端关闭了连接')
                client_sock.close()


class ClientStub(object):
    """
    用来帮助客户端完成远程过程调用 RPC调用

    stub = ClientStub()
    stub.divide(200, 100)
    框架是通用的，如果想实现加法，stub.add()类似
    """
    def __init__(self, channel):
        self.channel = channel
        self.conn = self.channel.get_connection()

    # 提供一个方法供客户端进行调用
    def divide(self, num1, num2=1):
        # 将调用的参数打包成消息协议的数据
        proto = DivideProtocol()
        args = proto.args_encode(num1, num2)

        # 将消息数据通过网络发送给服务器
        self.conn.sendall(args)

        # 接收服务器返回的返回值消息数据，并进行解析
        result = proto.result_decode(self.conn)

        # 将结果值（正常float 或 异常InvalidOperation）返回给客户端
        if isinstance(result, float):
            # 正常
            return result
        else:
            # 异常
            raise result

    def add(self):
        pass


class ServerStub(object):
    """
    帮助服务端完成远端过程调用
    """
    def __init__(self, connection, handlers):
        """
        :param connection: 与客户端的连接
        :param handlers: 真正本地被调用的方法（函数  过程）
        class Handlers:

            @staticmethod
            def divide(num1, num2=1):
                pass

            @staticmethod
            def add():
                pass
        """
        self.conn = connection
        self.method_proto = MethodProtocol(self.conn)
        self.process_map = {
            'divide': self._process_divide
        }
        self.handlers = handlers

    def process(self):
        """
        当服务端接受了一个客户端的连接，建立好连接后，完成远端调用处理
        :return:
        """
        # 1.接收消息数据，并解析方法的名字
        name = self.method_proto.get_method_name()

        # 2.根据解析获得的方法（过程）名，调用响应的过程协议，接收并解析消息数据
        # self.process_map[name]()
        _process = self.process_map[name]
        _process()

    def _process_divide(self):
        """
        处理除法过程调用
        :return:
        """
        # 1.创建用于除法过程调用参数协议数据解析的工具
        proto = DivideProtocol()
        # 2.解析调用参数消息数据
        args = proto.args_decode(self.conn)
        # args = {"num1": xxx, "num2": xxx}

        # 3.进行除法的本地过程调用
        # 将本地调用过程的返回值（包括可能的异常）打包成消息协议数据，通过网络返回给客户端
        try:
            val = self.handlers.divide(**args)
        except InvalidOpreation as e:
            ret_message = proto.result_encode(e)
        else:
            ret_message = proto.result_encode(val)

        self.conn.sendall(ret_message)


    # def _process_add(self):
    #     pass




if __name__ == '__main__':
    # 构造消息数据
    proto = DivideProtocol()
    # divide(200, 100)
    # message = proto.args_encode(200, 100)
    # divide(200)
    message = proto.args_encode(200)

    # 模拟网络连接
    conn = BytesIO()
    conn.write(message)
    conn.seek(0)

    # 解析消息数据
    method_proto = MethodProtocol(conn)
    name = method_proto.get_method_name()
    print(name)

    args = proto.args_decode(conn)
    print(args)