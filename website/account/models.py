from django.db import models
from short import shorts


class Account(models.Model):
    user = shorts.user_fk()

    created = shorts.dt_created()
    updated = shorts.dt_updated()
