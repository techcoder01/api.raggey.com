from rest_framework import serializers
from .models import Fee, Area


class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = "__all__"
        read_only_fields = ['id']


class FeeSerializer(serializers.ModelSerializer):
    area = AreaSerializer()
    class Meta:
        model = Fee
        fields = "__all__"
        read_only_fields = ['id']
