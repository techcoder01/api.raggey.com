from rest_framework import serializers
from .models import Sizes, DefaultMeasurement, CustomMeasurement


class SizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sizes
        fields = "__all__"
        read_only_fields = ['id', 'timestamp']


class DefaultMeasurementSerializer(serializers.ModelSerializer):
    front_height_image = serializers.SerializerMethodField()
    back_height_image = serializers.SerializerMethodField()
    neck_size_image = serializers.SerializerMethodField()
    around_legs_image = serializers.SerializerMethodField()
    full_chest_image = serializers.SerializerMethodField()
    half_chest_image = serializers.SerializerMethodField()
    full_belly_image = serializers.SerializerMethodField()
    half_belly_image = serializers.SerializerMethodField()
    neck_to_center_belly_image = serializers.SerializerMethodField()
    neck_to_chest_pocket_image = serializers.SerializerMethodField()
    shoulder_width_image = serializers.SerializerMethodField()
    arm_tall_image = serializers.SerializerMethodField()
    arm_width_1_image = serializers.SerializerMethodField()
    arm_width_2_image = serializers.SerializerMethodField()
    arm_width_3_image = serializers.SerializerMethodField()
    arm_width_4_image = serializers.SerializerMethodField()

    class Meta:
        model = DefaultMeasurement
        fields = "__all__"
        read_only_fields = ['id', 'timestamp', 'updated_at']

    def get_front_height_image(self, obj):
        return obj.front_height_image.url if obj.front_height_image else None

    def get_back_height_image(self, obj):
        return obj.back_height_image.url if obj.back_height_image else None

    def get_neck_size_image(self, obj):
        return obj.neck_size_image.url if obj.neck_size_image else None

    def get_around_legs_image(self, obj):
        return obj.around_legs_image.url if obj.around_legs_image else None

    def get_full_chest_image(self, obj):
        return obj.full_chest_image.url if obj.full_chest_image else None

    def get_half_chest_image(self, obj):
        return obj.half_chest_image.url if obj.half_chest_image else None

    def get_full_belly_image(self, obj):
        return obj.full_belly_image.url if obj.full_belly_image else None

    def get_half_belly_image(self, obj):
        return obj.half_belly_image.url if obj.half_belly_image else None

    def get_neck_to_center_belly_image(self, obj):
        return obj.neck_to_center_belly_image.url if obj.neck_to_center_belly_image else None

    def get_neck_to_chest_pocket_image(self, obj):
        return obj.neck_to_chest_pocket_image.url if obj.neck_to_chest_pocket_image else None

    def get_shoulder_width_image(self, obj):
        return obj.shoulder_width_image.url if obj.shoulder_width_image else None

    def get_arm_tall_image(self, obj):
        return obj.arm_tall_image.url if obj.arm_tall_image else None

    def get_arm_width_1_image(self, obj):
        return obj.arm_width_1_image.url if obj.arm_width_1_image else None

    def get_arm_width_2_image(self, obj):
        return obj.arm_width_2_image.url if obj.arm_width_2_image else None

    def get_arm_width_3_image(self, obj):
        return obj.arm_width_3_image.url if obj.arm_width_3_image else None

    def get_arm_width_4_image(self, obj):
        return obj.arm_width_4_image.url if obj.arm_width_4_image else None


class CustomMeasurementSerializer(serializers.ModelSerializer):
    front_height_image = serializers.SerializerMethodField()
    back_height_image = serializers.SerializerMethodField()
    neck_size_image = serializers.SerializerMethodField()
    around_legs_image = serializers.SerializerMethodField()
    full_chest_image = serializers.SerializerMethodField()
    half_chest_image = serializers.SerializerMethodField()
    full_belly_image = serializers.SerializerMethodField()
    half_belly_image = serializers.SerializerMethodField()
    neck_to_center_belly_image = serializers.SerializerMethodField()
    neck_to_chest_pocket_image = serializers.SerializerMethodField()
    shoulder_width_image = serializers.SerializerMethodField()
    arm_tall_image = serializers.SerializerMethodField()
    arm_width_1_image = serializers.SerializerMethodField()
    arm_width_2_image = serializers.SerializerMethodField()
    arm_width_3_image = serializers.SerializerMethodField()
    arm_width_4_image = serializers.SerializerMethodField()
    is_custom = serializers.SerializerMethodField()

    class Meta:
        model = CustomMeasurement
        fields = "__all__"
        read_only_fields = ['id', 'user', 'timestamp', 'updated_at']

    def get_is_custom(self, obj):
        return True

    def get_front_height_image(self, obj):
        return obj.front_height_image.url if obj.front_height_image else None

    def get_back_height_image(self, obj):
        return obj.back_height_image.url if obj.back_height_image else None

    def get_neck_size_image(self, obj):
        return obj.neck_size_image.url if obj.neck_size_image else None

    def get_around_legs_image(self, obj):
        return obj.around_legs_image.url if obj.around_legs_image else None

    def get_full_chest_image(self, obj):
        return obj.full_chest_image.url if obj.full_chest_image else None

    def get_half_chest_image(self, obj):
        return obj.half_chest_image.url if obj.half_chest_image else None

    def get_full_belly_image(self, obj):
        return obj.full_belly_image.url if obj.full_belly_image else None

    def get_half_belly_image(self, obj):
        return obj.half_belly_image.url if obj.half_belly_image else None

    def get_neck_to_center_belly_image(self, obj):
        return obj.neck_to_center_belly_image.url if obj.neck_to_center_belly_image else None

    def get_neck_to_chest_pocket_image(self, obj):
        return obj.neck_to_chest_pocket_image.url if obj.neck_to_chest_pocket_image else None

    def get_shoulder_width_image(self, obj):
        return obj.shoulder_width_image.url if obj.shoulder_width_image else None

    def get_arm_tall_image(self, obj):
        return obj.arm_tall_image.url if obj.arm_tall_image else None

    def get_arm_width_1_image(self, obj):
        return obj.arm_width_1_image.url if obj.arm_width_1_image else None

    def get_arm_width_2_image(self, obj):
        return obj.arm_width_2_image.url if obj.arm_width_2_image else None

    def get_arm_width_3_image(self, obj):
        return obj.arm_width_3_image.url if obj.arm_width_3_image else None

    def get_arm_width_4_image(self, obj):
        return obj.arm_width_4_image.url if obj.arm_width_4_image else None


# Combined serializer to list both default and custom measurements
class CombinedMeasurementSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    size_name = serializers.CharField()
    is_custom = serializers.BooleanField()
    is_default = serializers.BooleanField()
    timestamp = serializers.DateTimeField()

