from requests import delete
from sdwsn_controller.routes.routes import Routes


class SimpleRouter(Routes):
    def __init__(self):
        super().__init__()

    def add_link(self, source, destination, via):
        self.add_route(source, destination, via)

    def delete_link(self, source, destination, via):
        self.remove_route(source, destination, via)

    def delete_all_routes(self):
        self.clear_routes()
