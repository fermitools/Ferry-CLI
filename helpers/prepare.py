from typing import Any, Callable, Dict, List, Optional
from helpers.auth import Auth
from helpers.api import FerryAPI

class Queue:
    swagger_exists = None
    base_url:str = None
    authorization:'Auth' = None
    quiet:bool = None
    queued_function: List[Callable] = None
    queued_args: Optional[List[Any]] = None
        
    @staticmethod
    def authorize(decorated_function):
        def wrapper(*args, **kwargs):
            Queue.authorization = decorated_function(*args, **kwargs)
            return Queue.authorization
        Queue._launch_if_ready()
        return wrapper
    
    @staticmethod
    def ready(decorated_function):
        def wrapper(*args,**kwargs):
            if not Queue.queued_function:
                Queue.queued_function = []
            if not Queue.queued_args:
                Queue.queued_args = []
            Queue.queued_function.append(decorated_function)
            Queue.queued_args.append((args,kwargs) if args is not None or kwargs is not None else None)
            Queue._launch_if_ready()
        return wrapper
    
    @staticmethod
    def set(**kwargs):
        for key, value in kwargs.items():
            if hasattr(Queue, key):
                setattr(Queue, key, value)
        Queue._launch_if_ready()
        
    
    @staticmethod
    def _launch_if_ready()-> Any:
        if all(getattr(Queue, var) is not None for var in ["authorization","base_url", "quiet", "queued_function", "swagger_exists"]):
            api = FerryAPI(Queue.base_url, Queue.authorization, Queue.quiet)
            api.get_latest_swagger_file()
            for i in range(0, len(Queue.queued_function)):
                print(f"Running: {Queue.queued_function[i].__name__}")
                Queue.queued_function[i](Queue.queued_args[i])
       
            
            
            