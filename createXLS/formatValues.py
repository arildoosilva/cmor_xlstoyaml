def format(key, value):
    """ Formats the key and value for proper yaml writing later
    """
    strings = ["modeling_realm", "standard_name", "units", 
               "cell_methods", "cell_measures", "long_name",
               "comment", "out_name", "type", "valid_min",
               "valid_max", "ok_min_mean_abs", "ok_max_mean_abs",
               ""
              ]

    # First, put double quotes in strings
    if key in strings:
        value = '"{}"'.format(value)

    # Then, fix the dimensions value to a list
    if key == "dimensions":
        value = value.replace(" ", "\", \"")
        value = '["{}"]'.format(value)

    # And finally, rename some keys
    if key == "modeling_realm":
        key = "realm"

    return key, value