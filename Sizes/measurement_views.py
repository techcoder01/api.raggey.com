from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_201_CREATED, HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from .serializers import DefaultMeasurementSerializer, CustomMeasurementSerializer, CombinedMeasurementSerializer
from .models import DefaultMeasurement, CustomMeasurement
from Design.utils import hableImageUpload
from typing import Dict


# ============= DEFAULT MEASUREMENTS (Admin Only) =============

class DefaultMeasurementListAPIView(APIView):
    """
    GET: List all active default measurements (public - visible to all users)
    """
    def get(self, request, format=None):
        queryset = DefaultMeasurement.objects.filter(is_active=True)
        serializer = DefaultMeasurementSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')


class DefaultMeasurementDetailAPIView(APIView):
    """
    GET: Get a specific default measurement
    POST: Create a new default measurement (Admin only)
    PUT: Update a default measurement (Admin only)
    DELETE: Delete a default measurement (Admin only)
    """

    def get(self, request, pk=None, format=None):
        try:
            measurement = DefaultMeasurement.objects.get(id=pk)
            serializer = DefaultMeasurementSerializer(measurement, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except DefaultMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)

    def post(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied'}, status=HTTP_400_BAD_REQUEST)

        data = request.data

        # Handle image uploads
        images = {}
        image_fields = [
            'front_height_image', 'back_height_image', 'neck_size_image', 'around_legs_image',
            'full_chest_image', 'half_chest_image', 'full_belly_image', 'half_belly_image',
            'neck_to_center_belly_image', 'neck_to_chest_pocket_image', 'shoulder_width_image',
            'arm_tall_image', 'arm_width_1_image', 'arm_width_2_image', 'arm_width_3_image', 'arm_width_4_image'
        ]

        for field in image_fields:
            if data.get(field) and isinstance(data[field], Dict):
                images[field] = hableImageUpload(data[field])

        measurement = DefaultMeasurement.objects.create(
            size_name=data['size_name'],
            front_height=data['front_height'],
            back_height=data['back_height'],
            neck_size=data['neck_size'],
            around_legs=data['around_legs'],
            full_chest=data['full_chest'],
            half_chest=data['half_chest'],
            full_belly=data['full_belly'],
            half_belly=data['half_belly'],
            neck_to_center_belly=data['neck_to_center_belly'],
            neck_to_chest_pocket=data['neck_to_chest_pocket'],
            shoulder_width=data['shoulder_width'],
            arm_tall=data['arm_tall'],
            arm_width_1=data['arm_width_1'],
            arm_width_2=data['arm_width_2'],
            arm_width_3=data['arm_width_3'],
            arm_width_4=data['arm_width_4'],
            is_active=data.get('is_active', True),
            **images
        )

        serializer = DefaultMeasurementSerializer(measurement, context={'request': request})
        return Response(serializer.data, status=HTTP_201_CREATED, content_type='application/json; charset=utf-8')

    def put(self, request, pk=None, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = DefaultMeasurement.objects.get(id=pk)
        except DefaultMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)

        data = request.data

        # Update basic fields
        measurement.size_name = data.get('size_name', measurement.size_name)
        measurement.front_height = data.get('front_height', measurement.front_height)
        measurement.back_height = data.get('back_height', measurement.back_height)
        measurement.neck_size = data.get('neck_size', measurement.neck_size)
        measurement.around_legs = data.get('around_legs', measurement.around_legs)
        measurement.full_chest = data.get('full_chest', measurement.full_chest)
        measurement.half_chest = data.get('half_chest', measurement.half_chest)
        measurement.full_belly = data.get('full_belly', measurement.full_belly)
        measurement.half_belly = data.get('half_belly', measurement.half_belly)
        measurement.neck_to_center_belly = data.get('neck_to_center_belly', measurement.neck_to_center_belly)
        measurement.neck_to_chest_pocket = data.get('neck_to_chest_pocket', measurement.neck_to_chest_pocket)
        measurement.shoulder_width = data.get('shoulder_width', measurement.shoulder_width)
        measurement.arm_tall = data.get('arm_tall', measurement.arm_tall)
        measurement.arm_width_1 = data.get('arm_width_1', measurement.arm_width_1)
        measurement.arm_width_2 = data.get('arm_width_2', measurement.arm_width_2)
        measurement.arm_width_3 = data.get('arm_width_3', measurement.arm_width_3)
        measurement.arm_width_4 = data.get('arm_width_4', measurement.arm_width_4)
        measurement.is_active = data.get('is_active', measurement.is_active)

        # Handle image uploads
        image_fields = [
            'front_height_image', 'back_height_image', 'neck_size_image', 'around_legs_image',
            'full_chest_image', 'half_chest_image', 'full_belly_image', 'half_belly_image',
            'neck_to_center_belly_image', 'neck_to_chest_pocket_image', 'shoulder_width_image',
            'arm_tall_image', 'arm_width_1_image', 'arm_width_2_image', 'arm_width_3_image', 'arm_width_4_image'
        ]

        for field in image_fields:
            if field in data:
                if data[field] and isinstance(data[field], Dict):
                    setattr(measurement, field, hableImageUpload(data[field]))
                elif data[field] is None:
                    setattr(measurement, field, None)

        measurement.save()

        serializer = DefaultMeasurementSerializer(measurement, context={'request': request})
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

    def delete(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = DefaultMeasurement.objects.get(id=pk)
            measurement.delete()
            return Response({'message': 'Measurement deleted successfully'}, status=HTTP_200_OK)
        except DefaultMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)


# ============= CUSTOM MEASUREMENTS (User-specific) =============

class CustomMeasurementListAPIView(APIView):
    """
    GET: List all custom measurements for the authenticated user
    POST: Create a new custom measurement
    """

    def get(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        queryset = CustomMeasurement.objects.filter(user=user)
        serializer = CustomMeasurementSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

    def post(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        data = request.data

        # Handle image uploads
        images = {}
        image_fields = [
            'front_height_image', 'back_height_image', 'neck_size_image', 'around_legs_image',
            'full_chest_image', 'half_chest_image', 'full_belly_image', 'half_belly_image',
            'neck_to_center_belly_image', 'neck_to_chest_pocket_image', 'shoulder_width_image',
            'arm_tall_image', 'arm_width_1_image', 'arm_width_2_image', 'arm_width_3_image', 'arm_width_4_image'
        ]

        for field in image_fields:
            if data.get(field) and isinstance(data[field], Dict):
                images[field] = hableImageUpload(data[field])

        try:
            measurement = CustomMeasurement.objects.create(
                user=user,
                size_name=data['size_name'],
                front_height=data['front_height'],
                back_height=data['back_height'],
                neck_size=data['neck_size'],
                around_legs=data['around_legs'],
                full_chest=data['full_chest'],
                half_chest=data['half_chest'],
                full_belly=data['full_belly'],
                half_belly=data['half_belly'],
                neck_to_center_belly=data['neck_to_center_belly'],
                neck_to_chest_pocket=data['neck_to_chest_pocket'],
                shoulder_width=data['shoulder_width'],
                arm_tall=data['arm_tall'],
                arm_width_1=data['arm_width_1'],
                arm_width_2=data['arm_width_2'],
                arm_width_3=data['arm_width_3'],
                arm_width_4=data['arm_width_4'],
                **images
            )

            serializer = CustomMeasurementSerializer(measurement, context={'request': request})
            return Response(serializer.data, status=HTTP_201_CREATED, content_type='application/json; charset=utf-8')
        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)


class CustomMeasurementDetailAPIView(APIView):
    """
    GET: Get a specific custom measurement (user must own it)
    PUT: Update a custom measurement (user must own it)
    DELETE: Delete a custom measurement (user must own it)
    """

    def get(self, request, pk=None, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = CustomMeasurement.objects.get(id=pk, user=user)
            serializer = CustomMeasurementSerializer(measurement, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except CustomMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)

    def put(self, request, pk=None, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = CustomMeasurement.objects.get(id=pk, user=user)
        except CustomMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)

        data = request.data

        # Update basic fields
        measurement.size_name = data.get('size_name', measurement.size_name)
        measurement.front_height = data.get('front_height', measurement.front_height)
        measurement.back_height = data.get('back_height', measurement.back_height)
        measurement.neck_size = data.get('neck_size', measurement.neck_size)
        measurement.around_legs = data.get('around_legs', measurement.around_legs)
        measurement.full_chest = data.get('full_chest', measurement.full_chest)
        measurement.half_chest = data.get('half_chest', measurement.half_chest)
        measurement.full_belly = data.get('full_belly', measurement.full_belly)
        measurement.half_belly = data.get('half_belly', measurement.half_belly)
        measurement.neck_to_center_belly = data.get('neck_to_center_belly', measurement.neck_to_center_belly)
        measurement.neck_to_chest_pocket = data.get('neck_to_chest_pocket', measurement.neck_to_chest_pocket)
        measurement.shoulder_width = data.get('shoulder_width', measurement.shoulder_width)
        measurement.arm_tall = data.get('arm_tall', measurement.arm_tall)
        measurement.arm_width_1 = data.get('arm_width_1', measurement.arm_width_1)
        measurement.arm_width_2 = data.get('arm_width_2', measurement.arm_width_2)
        measurement.arm_width_3 = data.get('arm_width_3', measurement.arm_width_3)
        measurement.arm_width_4 = data.get('arm_width_4', measurement.arm_width_4)

        # Handle image uploads
        image_fields = [
            'front_height_image', 'back_height_image', 'neck_size_image', 'around_legs_image',
            'full_chest_image', 'half_chest_image', 'full_belly_image', 'half_belly_image',
            'neck_to_center_belly_image', 'neck_to_chest_pocket_image', 'shoulder_width_image',
            'arm_tall_image', 'arm_width_1_image', 'arm_width_2_image', 'arm_width_3_image', 'arm_width_4_image'
        ]

        for field in image_fields:
            if field in data:
                if data[field] and isinstance(data[field], Dict):
                    setattr(measurement, field, hableImageUpload(data[field]))
                elif data[field] is None:
                    setattr(measurement, field, None)

        measurement.save()

        serializer = CustomMeasurementSerializer(measurement, context={'request': request})
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

    def delete(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = CustomMeasurement.objects.get(id=pk, user=user)
            measurement.delete()
            return Response({'message': 'Measurement deleted successfully'}, status=HTTP_200_OK)
        except CustomMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)


# ============= COMBINED MEASUREMENTS (Default + User's Custom) =============

class AllMeasurementsListAPIView(APIView):
    """
    GET: List all measurements (default + user's custom measurements combined)
    This returns a simplified list for selection purposes
    """

    def get(self, request, format=None):
        user = request.user

        # Get all active default measurements
        default_measurements = DefaultMeasurement.objects.filter(is_active=True).values('id', 'size_name', 'timestamp')

        # Prepare response list
        measurements = []

        # Add default measurements
        for dm in default_measurements:
            measurements.append({
                'id': dm['id'],
                'size_name': dm['size_name'],
                'is_custom': False,
                'is_default': True,
                'timestamp': dm['timestamp']
            })

        # Add user's custom measurements if authenticated
        if user.is_authenticated:
            custom_measurements = CustomMeasurement.objects.filter(user=user).values('id', 'size_name', 'timestamp')
            for cm in custom_measurements:
                measurements.append({
                    'id': f"custom_{cm['id']}",  # Prefix to differentiate from default
                    'custom_id': cm['id'],  # Actual ID for fetching details
                    'size_name': cm['size_name'],
                    'is_custom': True,
                    'is_default': False,
                    'timestamp': cm['timestamp']
                })

        # Sort by timestamp (newest first)
        measurements.sort(key=lambda x: x['timestamp'], reverse=True)

        return Response(measurements, status=HTTP_200_OK, content_type='application/json; charset=utf-8')


# ============= ADMIN ENDPOINTS (View All Users' Measurements) =============

class AdminAllCustomMeasurementsAPIView(APIView):
    """
    GET: List ALL custom measurements from ALL users (Admin only)
    Admins can see all users' custom measurements
    """

    def get(self, request, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied. Admin access required.'}, status=HTTP_400_BAD_REQUEST)

        # Get all custom measurements from all users
        queryset = CustomMeasurement.objects.all().select_related('user').order_by('-timestamp')
        serializer = CustomMeasurementSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')


class AdminUserCustomMeasurementsAPIView(APIView):
    """
    GET: List all custom measurements for a specific user (Admin only)
    Admins can filter measurements by user
    """

    def get(self, request, user_id=None, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied. Admin access required.'}, status=HTTP_400_BAD_REQUEST)

        # Get custom measurements for specific user
        queryset = CustomMeasurement.objects.filter(user_id=user_id).order_by('-timestamp')
        serializer = CustomMeasurementSerializer(queryset, context={'request': request}, many=True)

        response_data = {
            'user_id': user_id,
            'measurements': serializer.data
        }

        return Response(response_data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')


class AdminCustomMeasurementDetailAPIView(APIView):
    """
    GET: Get any user's custom measurement (Admin only)
    PUT: Update any user's custom measurement (Admin only)
    DELETE: Delete any user's custom measurement (Admin only)
    """

    def get(self, request, pk=None, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied. Admin access required.'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = CustomMeasurement.objects.select_related('user').get(id=pk)
            serializer = CustomMeasurementSerializer(measurement, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except CustomMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)

    def put(self, request, pk=None, format=None):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied. Admin access required.'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = CustomMeasurement.objects.get(id=pk)
        except CustomMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)

        data = request.data

        # Update basic fields
        measurement.size_name = data.get('size_name', measurement.size_name)
        measurement.front_height = data.get('front_height', measurement.front_height)
        measurement.back_height = data.get('back_height', measurement.back_height)
        measurement.neck_size = data.get('neck_size', measurement.neck_size)
        measurement.around_legs = data.get('around_legs', measurement.around_legs)
        measurement.full_chest = data.get('full_chest', measurement.full_chest)
        measurement.half_chest = data.get('half_chest', measurement.half_chest)
        measurement.full_belly = data.get('full_belly', measurement.full_belly)
        measurement.half_belly = data.get('half_belly', measurement.half_belly)
        measurement.neck_to_center_belly = data.get('neck_to_center_belly', measurement.neck_to_center_belly)
        measurement.neck_to_chest_pocket = data.get('neck_to_chest_pocket', measurement.neck_to_chest_pocket)
        measurement.shoulder_width = data.get('shoulder_width', measurement.shoulder_width)
        measurement.arm_tall = data.get('arm_tall', measurement.arm_tall)
        measurement.arm_width_1 = data.get('arm_width_1', measurement.arm_width_1)
        measurement.arm_width_2 = data.get('arm_width_2', measurement.arm_width_2)
        measurement.arm_width_3 = data.get('arm_width_3', measurement.arm_width_3)
        measurement.arm_width_4 = data.get('arm_width_4', measurement.arm_width_4)

        # Handle image uploads
        image_fields = [
            'front_height_image', 'back_height_image', 'neck_size_image', 'around_legs_image',
            'full_chest_image', 'half_chest_image', 'full_belly_image', 'half_belly_image',
            'neck_to_center_belly_image', 'neck_to_chest_pocket_image', 'shoulder_width_image',
            'arm_tall_image', 'arm_width_1_image', 'arm_width_2_image', 'arm_width_3_image', 'arm_width_4_image'
        ]

        for field in image_fields:
            if field in data:
                if data[field] and isinstance(data[field], Dict):
                    setattr(measurement, field, hableImageUpload(data[field]))
                elif data[field] is None:
                    setattr(measurement, field, None)

        measurement.save()

        serializer = CustomMeasurementSerializer(measurement, context={'request': request})
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

    def delete(self, request, pk):
        user = request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)

        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied. Admin access required.'}, status=HTTP_400_BAD_REQUEST)

        try:
            measurement = CustomMeasurement.objects.get(id=pk)
            measurement.delete()
            return Response({'message': 'Measurement deleted successfully'}, status=HTTP_200_OK)
        except CustomMeasurement.DoesNotExist:
            return Response({'error': 'Measurement not found'}, status=HTTP_404_NOT_FOUND)
