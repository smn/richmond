def model_instance_to_key_values(instance, exclude=[]):
    field_names = [field.name for field in instance._meta.fields]
    key_values = [(key, getattr(instance, key)) for
                    key in field_names
                    if key not in exclude]
    return [(str(key), str(value))
                for key,value in key_values
                if value
            ]

def callback(url, list_of_tuples):
    """
    HTTP POST a list of key value tuples to the given URL and 
    return the response
    """
    data = StringIO()
    ch = pycurl.Curl()
    ch.setopt(pycurl.URL, url)
    ch.setopt(pycurl.VERBOSE, 0)
    ch.setopt(pycurl.SSLVERSION, 3)
    ch.setopt(pycurl.SSL_VERIFYPEER, 1)
    ch.setopt(pycurl.SSL_VERIFYHOST, 2)
    ch.setopt(pycurl.HTTPHEADER, [
            "User-Agent: Richmond Callback Client"
            "Accept:"
        ])
    ch.setopt(pycurl.WRITEFUNCTION, data.write)
    ch.setopt(pycurl.HTTPPOST, list_of_tuples)
    ch.setopt(pycurl.FOLLOWLOCATION, 1)

    try:
        result = ch.perform()
        resp = data.getvalue()
        logging.debug("Posted %s to %s which returned %s" % (post, url, resp))
        return (url, resp)
    except pycurl.error, v:
        logging.error("Posting %s to %s resulted in error: %s" % (post, url, v))
        return (url, v)
