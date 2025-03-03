from functools import wraps
import threading


def singleton(cls):
    """Decorator to create a Singleton class"""
    instances = {}

    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            with threading.Lock():
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance
