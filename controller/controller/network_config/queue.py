from collections import deque


class Queue:
    '''
    Thread-safe, memory-efficient, maximally-sized queue supporting queueing and
    dequeueing in worst-case O(1) time.
    '''

    def __init__(self, max_size=10):
        '''
        Initialize this queue to the empty queue.

        Parameters
        ----------
        max_size : int
            Maximum number of items contained in this queue. Defaults to 10.
        '''

        self._queue = deque(maxlen=max_size)
        self.size = max_size

    def enqueue(self, item):
        '''
        Queues the passed item (i.e., pushes this item onto the tail of this
        queue).
        '''
        if (len(self._queue) == self.size):
            print("Queue is Full!!!!")
        else:
            self._queue.append(item)

    def dequeue(self):
        '''
        Dequeues (i.e., removes) the item at the head of this queue *and*
        returns this item.

        Raises
        ----------
        IndexError
            If this queue is empty.
        '''

        return self._queue.pop()

    def clear(self):
        return self._queue.clear()

    def print_queue(self):
        print("print queue")
        print(self._queue)
