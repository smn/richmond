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

