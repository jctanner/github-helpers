def safe_string(data):

    if type(data) is unicode:
        try:
            data = data.encode('ascii')
        except UnicodeEncodeError:
            data = "UNICODE"

    if type(data) == int:
        data = str(data)
    if type(data) == list:
        if len(data) > 0:
            data = data[0]
        data = "%s" % str(data)

    if type(data) == str:
        if '\n' in data:
            data = str(data.split('\n')[0])

    if type(data) == dict:
        #epdb.st()
        data = "DICT"

    if type(data) == bool:
        data = str(data)

    if data is None:
        data = "None"

    if type(data) != str:
        epdb.st()

    if ':' in data and '{' in data and len(data) > 100:
        #epdb.st()
        data = "DICT"

    if data.startswith("https://"):
        pass

    data = data.replace('"', '')
    data = data.replace("'", "")

    return "\"" + data + "\""

