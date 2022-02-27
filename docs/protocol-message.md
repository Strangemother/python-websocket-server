# Protocol Message

A message may be formatted and captured on the upstream for headers.
A formatted message:

    key: value
    key: value

    message ....


The message is terminated through upstream send.

> note: consideration - not implemented

If the message is extended, the last value should contain a 'continuation' header.

    key: value
    continue_key: truthy

    message .
    .. message limit.



## Enforced Properties

Requuired headers for the protocol may include sub protocol types.

    datetime: 2022-02-26T23:19:33+00:00
    to: name, name, name, name
    from: client_uuid

