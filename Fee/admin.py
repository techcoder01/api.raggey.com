from django.contrib import admin
from .models import Fee, Area
from import_export.admin import ImportExportModelAdmin

# Register your models here.
admin.site.register(Fee)


@admin.register(Area)
class AreaAdmin(ImportExportModelAdmin):
    pass
