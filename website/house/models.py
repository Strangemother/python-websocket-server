from django.db import models
from short import shorts



class Room(models.Model):

    _short_props = ('friendly', 'owner', 'uuid')

    friendly = shorts.chars(100)
    uuid = shorts.uuid()
    owner = shorts.fk('account.Account', nil=True)

    created = shorts.dt_created()
    updated = shorts.dt_updated()
