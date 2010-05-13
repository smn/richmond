def model_instance_to_key_values(instance, exclude=[]):
    field_names = [field.name for field in instance._meta.fields]
    key_values = [(key, getattr(instance, key)) for
                    key in field_names
                    if key not in exclude]
    return [(str(key), str(value))
                for key,value in key_values
                if value
            ]
