from django.contrib import admin
from short import admin as shorts
from . import models

shorts.register_models(models)
