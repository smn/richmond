import logging
from django.utils import simplejson
from richmond.utils import load_class_by_string

class Worker(object):
    """A simple worker base class"""
    
    # expose is a list of callable attribute names that
    # are exposed via the queue, if this is empty then all defined
    # functions are callable. If not, only the listed ones are
    exposed_functions = []
    
    @classmethod
    def expose(klass, fn):
        klass.exposed_functions.append(fn.func_name)
        return classmethod(fn)

# This is ugly, not sure how to fix it yet though.
expose = Worker.expose



class Job(object):
    """
    A job being processed in the background for processing by JobWorkers
    """
    def __init__(self, job_description):
        logging.debug("I should publish the following job description to "
                        "the queue for background processing: %s" % 
                        simplejson.dumps(job_description))
        self.job_description = job_description
    
    def process(self):
        """Process the job_description"""
        class_name = self.job_description['class']
        klass = load_class_by_string(class_name)
        fn = getattr(klass, self.job_description['function'])
        args = self.job_description['args']
        kwargs = self.job_description['kwargs']
        return fn(*args, **kwargs)
    
    @classmethod
    def schedule(klass, worker_class, worker_function):
        def wrapper(*args, **kwargs):
            return Job({
                'class': "%s.%s" % (worker_class.__module__, 
                                    worker_class.__class__.__name__),
                'function': worker_function.__func__.func_name,
                'args': args,
                'kwargs': kwargs
            })
        return wrapper



class BackgroundWorker(object):
    """
    Wrap a worker to trap all incoming calls & write them as a
    job description to the queue
    """
    
    def __init__(self, async, worker):
        self.worker = worker
        self.async = async
        
    def __getattr__(self, attname):
        """Get the attribute from the worker unless exposed_functions
        is defined and it isn't listed in it."""
        exposed_functions = self.worker.exposed_functions
        if exposed_functions and attname not in exposed_functions:
            raise AttributeError, "%s is not an exposed function" % attname
        scheduler = Job.schedule(self.worker, 
                                getattr(self.worker, attname))
        if self.async:
            return scheduler
        else:            
            def sync_wrapper(*args, **kwargs):
                job = scheduler(*args, **kwargs)
                return job.process()
            return sync_wrapper
    


class WorkerManager(object):
    
    default_wrapper = BackgroundWorker
    
    def __init__(self, wrapper=default_wrapper, async=True, workers={}):
        """
        All workers are specified as key word arguments, the keys
        are automatically made attributes on the WorkerManager
        """
        self.workers = workers
        self.wrapper = wrapper
        self.async = async
        for name, worker in self.workers.items():
            self.register(name, worker)
    
    def get(self, name):
        return self.workers.get(name)
    
    def register(self, name, worker):
        """Register a worker"""
        wrapped_worker = self.wrapper(async=self.async, worker=worker)
        return self.workers.setdefault(name, wrapped_worker)
