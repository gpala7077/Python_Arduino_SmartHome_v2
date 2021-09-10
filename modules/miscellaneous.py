class Queue:
    """Represents a Queue

    Attributes
    ----------
    queue : list
        Managed list
    style : str
        Style of list management, i.e. FIFO or LIFO

    """

    def __init__(self, style):
        self.queue = []
        self.style = style

    def add(self, element):
        """Adds element to the list"""

        if self.style == 'FIFO':  # If FIFO, append element to end of list
            self.queue.append(element)

        elif self.style == 'LIFO':  # If LIFO, append element to front of list
            self.queue.insert(0, element)

    def get(self):  # Get first item from list
        if len(self.queue) > 0:
            return self.queue.pop(0)

    def __bool__(self):  # Return True if list is not empty. False if empty
        return len(self.queue) > 0

    def __repr__(self):  # List of elements
        return ', '.join(self.queue)
