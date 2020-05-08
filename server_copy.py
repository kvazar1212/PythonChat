import asyncio
from asyncio import transports
from typing import Optional


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(decoded)
        flag = False

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):

                temp_login = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == temp_login:
                        flag = True
                if flag is True:
                    self.transport.write(
                        f"Имя {temp_login} занято!".encode()
                    )
                else:
                    self.login = decoded.replace("login:", "").replace("\r\n", "")
                    self.transport.write(
                        f"Привет, {self.login}!".encode()
                    )
                    self.send_history()

        else:
            if decoded.startswith("login:"):
                self.transport.write(
                    f"Вы уже вошли пол именем: {self.login}".encode()
                )

            else:
                if flag is False:
                    self.send_message(decoded)
                    format_decoded = f"<{self.login}> {decoded}\r\n"
                    self.server.messages.append(format_decoded)

    def send_history(self):
        count = 10
        if count > len(self.server.messages):
            count = len(self.server.messages) + 1
        while count > 0:
            if len(self.server.messages) > 0:
                self.transport.write(
                    f"{self.server.messages[-count]}".encode()
                )
            count = count - 1

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        count = 10
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")
        self.send_history()
        """
        if count > len(self.server.messages):
            count = len(self.server.messages) + 1
        while count > 0:
            if len(self.server.messages)>0:
                self.transport.write(
                    f"Привет, {self.server.messages[-count]}!".encode()
                )
                count = count - 1
        """

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    messages: list

    def __init__(self):
        self.clients = []
        self.messages = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )
        print("Сервер Запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
