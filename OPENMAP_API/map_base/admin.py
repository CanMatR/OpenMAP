from django.contrib import admin
from map_base import models

admin.site.register(models.MapBase)
admin.site.register(models.MapFacility)
admin.site.register(models.MLFacility)
admin.site.register(models.Campaign)
admin.site.register(models.Experiment)
admin.site.register(models.MapStage)
admin.site.register(models.MapInput)
admin.site.register(models.ExpInputVal)
admin.site.register(models.MapOutput)
admin.site.register(models.ExpOutputVal)
