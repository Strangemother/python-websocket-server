from porthouse import exceptions

banned_set = set([
        # '127.0.0.1'
    ])


def add(ip):
    banned_set.add(ip)

async def hard_blacklist(websocket):
    return not (websocket.client.host in banned_set)


async def hard_error_blacklist(websocket):
    host = websocket.client.host
    if host in banned_set:
        raise exceptions.EntryException(f'Banned Host {host}')

    return True

