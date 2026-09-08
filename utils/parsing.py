def command_args(
    text
):

    if not text:

        return []


    return text.split()[1:]





def parse_positive_int(
    value
):

    try:

        number = int(value)


        if number > 0:

            return number


    except:

        pass


    return None