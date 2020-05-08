"""
Серверное приложение для соединений
"""
import asyncio
from asyncio import transports


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


        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                count_temp = 0
                login_temp = decoded.replace("login:", "").replace("\r\n", "")
                for client in self.server.clients:
                    if client.login == login_temp:
                        count_temp+=1;

                if count_temp>0:
                    self.transport.write(
                        f"Логин {login_temp} занят, попробуйте другой".encode()
                    )
                    self.transport.close()
                else:
                    self.login = login_temp
                    self.transport.write(
                    f"Привет, {self.login}!\r\n".encode()
                    )
                    self.send_history()
        else:
            self.send_message(decoded)
            if len(self.server.history) == 10:
                self.server.history.pop(0)
            self.server.history.append(f"<{self.login}> {decoded}")
            

    def send_history(self):
        for item in self.server.history:
            self.transport.write(
                f"{item}\r\n".encode()
            )

    def send_message(self, message):
        format_string = f"<{self.login}> {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Соединение установлено")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Соединение разорвано")


class Server:
    clients: list
    history: list

    def __init__(self):
        self.clients = []
        self.history = []

    def create_protocol(self):
        return ClientProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
