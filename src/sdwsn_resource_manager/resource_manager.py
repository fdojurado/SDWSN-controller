from gc import callbacks
import multiprocessing as mp
import resource


class ResourceComponent():
    def __init__(self, name, input_queue=mp.Queue(), output_queue=mp.Queue(), init_func=None, **kwargs) -> None:
        self.name = name
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.init_func = init_func
        self.kwargs = kwargs
        print(f'kwargs: {kwargs}')
        pass

    def init(self):
        self.object = self.init_func(self.input_queue, self.output_queue, **self.kwargs)
        return self.object
        


class ResourceManager():
    def __init__(self) -> None:
        self.resource = []
        pass

    def add(self, resource_component):
        self.resource.append(resource_component)
        pass

    def init(self):
        # Initialize all resources
        for resource in self.resource:
            if (resource.init() is not None):
                print(f'correct initialization of {resource.name}')
            else:
                print(f'error initializing {resource.name}')
                return 0
        return 1

    def start(self):
        if not self.init():
            print("Resources didn't start")
            return
        # Let's start all resources in their multiprocessing
        for resource in self.resource:
            resource.object.daemon = True
            resource.object.start()
        return 1

