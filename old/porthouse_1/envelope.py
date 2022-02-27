from . import conf



class Envelope(object):
    # A single plugin to read in, out
    async def initial_entry(self, owner):
        return True

    async def push_message(self, data, owner):
        # print('  Envelope', data)
        return data

    async def disconnecting_socket(self, websocket, client_id, error):
        pass


class DefaultMessage(object):
    """The message is applied early in the envelope chain.
    """
    def __getitem__(self,v):
        return self.__dict__[v]

    def __setitem__(self,k, v):
        self.__dict__[k] = v

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self._message}>'


class CustomMessage(DefaultMessage):
    pass


class MessageCast(Envelope):
    # A single plugin to read in, out
    # async def initial_entry(self, owner):
    #     return True

    async def push_message(self, data, owner):
        m = Message()
        m._message = data
        m.__dict__.update(data)
        m._owner = owner
        # print('  Envelope Response', m)

        return m


Message = conf.resolve('MESSAGE_CLASS', DefaultMessage)
# import pdb; pdb.set_trace()  # breakpoint 4533d382 //
