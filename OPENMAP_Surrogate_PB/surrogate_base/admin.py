from django.contrib import admin
from surrogate_base import models

admin.site.register(models.MiscConfig)

admin.site.register(models.Module)
admin.site.register(models.ModuleInpVar)
admin.site.register(models.ModuleOutVar)

admin.site.register(models.Experiment)
admin.site.register(models.ExpModule)
admin.site.register(models.ExpModuleInpVar)
admin.site.register(models.ExpOutVar)
