from django.db import models

# Create your models here.
class Area(models.Model):
    area_name_eng = models.CharField(max_length=180, default="")
    area_name_arb = models.CharField(max_length=180, default="")

    def __str__(self):
        return self.area_name_eng


class Fee(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    fee = models.DecimalField(max_digits=9, decimal_places=3)
    availble = models.BooleanField(default=False)

    def __str__(self):
        return self.area.area_name_eng
