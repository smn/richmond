import imp
import os.path

def load_class(module_name, class_name):
    """
    Load a class when given its module and its class name
    
    >>> load_class('richmond.workers.base','RichmondWorker')
    <class 'base.RichmondWorker'>
    >>> 
    
    """
    parts = module_name.split('.')
    module_name = parts[-1]
    module_parents = parts[:-1]
    module_parents_path = os.path.join(*module_parents)
    fp, path_name, description = imp.find_module(module_name, \
                                                    [module_parents_path])
    mod = imp.load_module(module_name, fp, path_name, description)
    return getattr(mod, class_name)

def load_class_by_string(class_path):
    """
    Load a class when given it's full name, including modules in python
    dot notation
    
    >>> load_class_by_string('richmond.workers.base.RichmondWorker')
    <class 'base.RichmondWorker'>
    >>> 
    
    """
    parts = class_path.split('.')
    module_name = '.'.join(parts[:-1])
    class_name = parts[-1]
    return load_class(module_name, class_name)


def filter_options_on_prefix(options, prefix):
    """
    splits an options dict based on key prefixes
    
    >>> filter_options_on_prefix({'foo-bar-1': 'ok'}, 'foo')
    {'bar-1': 'ok'}
    >>> 
    
    """
    return dict((key.split("-",1)[1], value) \
                for key, value in options.items() \
                if key.startswith(prefix))

