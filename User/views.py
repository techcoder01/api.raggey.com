from django.shortcuts import render
from .serializers import AddressSerializer, userBasicInfoSerializer, UserProfileSerializer, UpdateFCMTokenSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from .models import Address, Profile
from django.contrib.auth.models import User
from django.db import transaction
from Design.models import UserDesign, HomePageSelectionCategory, FabricColor, GholaType, SleevesType, PocketType, ButtonType, ButtonStripType, BodyType
from Sizes.models import Sizes

# Create your views here.
class AddressAPIView(APIView):
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            queryset = Address.objects.filter(user=user)
            serializer = AddressSerializer(
                queryset, context={'request': request},  many=True)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    def post(self, request):
        """Create a new address"""
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)

        # Use serializer for validation and creation
        serializer = AddressSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Set user from request
            serializer.save(user=user)
            return Response(serializer.data, status=HTTP_201_CREATED, content_type='application/json; charset=utf-8')

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None, format=None):
        """Update an existing address"""
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)

        try:
            address = Address.objects.get(id=pk, user=user)
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=HTTP_404_NOT_FOUND)

        # Use serializer for validation and update
        serializer = AddressSerializer(address, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        return Response({'error': 'Invalid data', 'details': serializer.errors}, status=HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None, format=None):
        """Delete an address"""
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)

        try:
            address = Address.objects.get(id=pk, user=user)
            address.delete()
            return Response({'message': 'Address deleted successfully'}, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=HTTP_404_NOT_FOUND)

class SelectedAddressAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """Get a specific address by ID"""
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)

        try:
            address = Address.objects.get(user=user, id=pk)
            serializer = AddressSerializer(address, context={'request': request}, many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=HTTP_404_NOT_FOUND)

class DefaultAddressAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """Get user's default address"""
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)

        try:
            queryset = Address.objects.get(user=user, isDefault=True)
            serializer = AddressSerializer(queryset, context={'request': request}, many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except Address.DoesNotExist:
            return Response({'error': 'No default address found'}, status=HTTP_404_NOT_FOUND)

    def put(self, request, pk=None, format=None):
        """Set an address as default"""
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)

        try:
            address = Address.objects.get(id=pk, user=user)

            # Remove default from all other addresses
            Address.objects.filter(user=user, isDefault=True).exclude(id=pk).update(isDefault=False)

            # Set this address as default
            address.isDefault = request.data.get('isDefault', True)
            address.save()

            serializer = AddressSerializer(address, context={'request': request}, many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except Address.DoesNotExist:
            return Response({'error': 'Address not found'}, status=HTTP_404_NOT_FOUND)


class UserInfoAPIView(APIView):
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            queryset = User.objects.get(id=user.id)
            serializer = userBasicInfoSerializer(
                queryset, context={'request': request},  many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)


class UserProfileAPIView(APIView):
    """
    GET: Get comprehensive user profile with all saved items
    Returns: user info, addresses, designs, orders, and custom measurements
    Endpoint: /user/profile/
    """
    def get(self, request):
        user = self.request.user
        if user.is_authenticated:
            serializer = UserProfileSerializer(user, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response({'error': 'Authentication required'}, status=HTTP_401_UNAUTHORIZED)


class UpdateFCMTokenAPIView(APIView):
    """
    POST: Update FCM token and device info for push notifications
    Request Body:
    {
        "fcm_token": "firebase-cloud-messaging-token",
        "device_name": "Samsung Galaxy S21" (optional),
        "device_id": "unique-device-id" (optional),
        "device_type": "android" (optional)
    }
    Endpoint: /user/update-fcm-token/
    """
    def post(self, request):
        user = self.request.user
        if not user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=HTTP_401_UNAUTHORIZED)

        serializer = UpdateFCMTokenSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.update_fcm_token(user)
            return Response(result, status=HTTP_200_OK)

        return Response({
            'success': False,
            'error': 'Invalid data',
            'details': serializer.errors
        }, status=HTTP_400_BAD_REQUEST)


class SaveDesignAPIView(APIView):
    """
    POST: Save UserDesign when user adds to cart
    This allows users to see their saved designs when adding another dishdasha

    Request Body:
    {
        "design_name": "My Design",
        "initial_size_selected_id": 1,
        "main_body_fabric_color_id": 5,
        "selected_coller_type_id": 2,
        "selected_sleeve_left_type_id": 3,
        "selected_sleeve_right_type_id": 4,
        "selected_pocket_id": 1,
        "selected_button_id": 2,
        "selected_button_strip_id": 1,
        "selected_body_type_id": 6,
        "design_total": 25.500
    }

    Endpoint: /user/save-design/
    """
    def post(self, request):
        user = self.request.user
        if not user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=HTTP_401_UNAUTHORIZED)

        try:
            data = request.data

            # Get foreign key instances
            initial_category = HomePageSelectionCategory.objects.filter(
                id=data.get('initial_size_selected_id')
            ).first()
            if not initial_category:
                initial_category = HomePageSelectionCategory.objects.filter(isHidden=False).first()

            # All components are nullable - users can save incomplete designs
            fabric_color = FabricColor.objects.filter(id=data.get('main_body_fabric_color_id')).first() if data.get('main_body_fabric_color_id') else None
            collar = GholaType.objects.filter(id=data.get('selected_coller_type_id')).first() if data.get('selected_coller_type_id') else None
            sleeve_left = SleevesType.objects.filter(id=data.get('selected_sleeve_left_type_id')).first() if data.get('selected_sleeve_left_type_id') else None
            sleeve_right = SleevesType.objects.filter(id=data.get('selected_sleeve_right_type_id')).first() if data.get('selected_sleeve_right_type_id') else None
            pocket = PocketType.objects.filter(id=data.get('selected_pocket_id')).first() if data.get('selected_pocket_id') else None
            button = ButtonType.objects.filter(id=data.get('selected_button_id')).first() if data.get('selected_button_id') else None
            button_strip = ButtonStripType.objects.filter(id=data.get('selected_button_strip_id')).first() if data.get('selected_button_strip_id') else None
            body = BodyType.objects.filter(id=data.get('selected_body_type_id')).first() if data.get('selected_body_type_id') else None

            # Check if identical design already exists
            design_filter = {
                'user': user,
                'initial_size_selected': initial_category,
                'main_body_fabric_color': fabric_color,
                'selected_coller_type': collar,
                'selected_sleeve_left_type': sleeve_left,
                'selected_sleeve_right_type': sleeve_right,
                'selected_pocket_type': pocket,
                'selected_button_type': button,
                'selected_button_strip_type': button_strip,
                'selected_body_type': body,
            }

            existing_design = UserDesign.objects.filter(**design_filter).first()

            if existing_design:
                # Reuse existing design
                return Response({
                    'success': True,
                    'message': 'Design already exists, reusing',
                    'design': {
                        'id': existing_design.id,
                        'design_name': existing_design.design_name,
                        'design_total': str(existing_design.design_Total),
                        'created': False
                    }
                }, status=HTTP_200_OK)
            else:
                # Create new design
                design = UserDesign.objects.create(
                    user=user,
                    design_name=data.get('design_name', ''),
                    initial_size_selected=initial_category,
                    main_body_fabric_color=fabric_color,
                    selected_coller_type=collar,
                    selected_sleeve_left_type=sleeve_left,
                    selected_sleeve_right_type=sleeve_right,
                    selected_pocket_type=pocket,
                    selected_button_type=button,
                    selected_button_strip_type=button_strip,
                    selected_body_type=body,
                    design_Total=data.get('design_total', 0.0)
                )

                return Response({
                    'success': True,
                    'message': 'Design saved successfully',
                    'design': {
                        'id': design.id,
                        'design_name': design.design_name,
                        'design_total': str(design.design_Total),
                        'created': True
                    }
                }, status=HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to save design',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class SaveMeasurementAPIView(APIView):
    """
    POST: Save custom measurement (Sizes) when user enters measurements
    This allows users to see their saved measurements when adding another dishdasha

    Request Body:
    {
        "size_name": "My Custom Size",
        "front_hight": "120",
        "back_hight": "115",
        "around_neck": "40",
        "around_legs": "100",
        "full_chest": "110",
        "half_chest": "55",
        "full_belly": "105",
        "half_belly": "52",
        "neck_to_center_belly": "75",
        "neck_to_chest": "30",
        "shoulders_width": "45",
        "arm_tall": "60",
        "arm_width_one": "35",
        "arm_width_two": "30",
        "arm_width_three": "25",
        "arm_width_four": "20"
    }

    Endpoint: /user/save-measurement/
    """
    def post(self, request):
        user = self.request.user
        if not user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=HTTP_401_UNAUTHORIZED)

        try:
            data = request.data

            # Check if identical measurement already exists
            measurement_filter = {
                'user': user,
                'front_hight': data.get('front_hight', ''),
                'back_hight': data.get('back_hight', ''),
                'around_neck': data.get('around_neck', ''),
                'around_legs': data.get('around_legs', ''),
                'full_chest': data.get('full_chest', ''),
                'half_chest': data.get('half_chest', ''),
                'full_belly': data.get('full_belly', ''),
                'half_belly': data.get('half_belly', ''),
                'neck_to_center_belly': data.get('neck_to_center_belly', ''),
                'neck_to_chest': data.get('neck_to_chest', ''),
                'shoulders_width': data.get('shoulders_width', ''),
                'arm_tall': data.get('arm_tall', ''),
                'arm_width_one': data.get('arm_width_one', ''),
                'arm_width_two': data.get('arm_width_two', ''),
                'arm_width_three': data.get('arm_width_three', ''),
                'arm_width_four': data.get('arm_width_four', ''),
            }

            existing_measurement = Sizes.objects.filter(**measurement_filter).first()

            if existing_measurement:
                # Reuse existing measurement
                return Response({
                    'success': True,
                    'message': 'Measurement already exists, reusing',
                    'measurement': {
                        'id': existing_measurement.id,
                        'size_name': existing_measurement.size_name,
                        'created': False
                    }
                }, status=HTTP_200_OK)
            else:
                # Create new measurement
                measurement = Sizes.objects.create(
                    user=user,
                    size_name=data.get('size_name', 'Custom Size'),
                    **measurement_filter
                )

                return Response({
                    'success': True,
                    'message': 'Measurement saved successfully',
                    'measurement': {
                        'id': measurement.id,
                        'size_name': measurement.size_name,
                        'created': True
                    }
                }, status=HTTP_201_CREATED)

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to save measurement',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class BulkSaveCartDataAPIView(APIView):
    """
    POST: Save/Update cart-related data before checkout
    - Skips measurements (saved during order creation)
    - Saves/Updates address
    - Saves cart items as UserDesign (with unique checking)

    Request Body:
    {
        "measurement": {
            "type": "custom" or "default",
            "size_name": "My Custom Size" or "XL",
            // If custom type:
            "front_hight": 120,
            "back_hight": 115,
            ... all custom measurement fields
        },
        "address": {
            "id": 5, // Optional - if updating existing
            "full_name": "John Doe",
            "phone_number": "+96512345678",
            "governorate": "Ahmadi",
            "area": "Sabahiya",
            "block": "1",
            "street": "101",
            "building": "25",
            "apartment": "3",
            "floor": "2",
            "address_type": "home",
            "isDefault": true,
            "latitude": 29.123,
            "longitude": 48.456
        },
        "cart_items": [
            {
                "id": 10, // Optional - if updating existing design
                "design_name": "My Dishdasha Design",
                "initial_size_selected_id": 1, // Optional - if not provided, uses first non-hidden category
                "main_body_fabric_color_id": 5,
                "selected_coller_type_id": 2,
                "selected_sleeve_left_type_id": 3,
                "selected_sleeve_right_type_id": 4,
                "selected_pocket_id": 1,
                "selected_button_id": 2,
                "selected_button_strip_id": 1,
                "selected_body_type_id": 6 // Optional - body type selection
            }
        ]
    }

    Endpoint: /user/bulk-save-cart-data/
    """

    def post(self, request):
        user = self.request.user
        if not user.is_authenticated:
            return Response({
                'success': False,
                'error': 'Authentication required'
            }, status=HTTP_401_UNAUTHORIZED)

        try:
            data = request.data
            response_data = {
                'success': True,
                'message': 'Cart data saved successfully',
                'saved_items': {}
            }

            # ========== 1. SAVE MEASUREMENT (Sizes) ==========
            if 'measurement' in data and data['measurement']:
                measurement_data = data['measurement']
                measurement_type = measurement_data.get('type', 'default')

                if measurement_type == 'custom':
                    # Save custom measurement to Sizes table
                    try:
                        # Check if identical measurement exists
                        measurement_filter = {
                            'user': user,
                            'front_hight': measurement_data.get('front_hight', ''),
                            'back_hight': measurement_data.get('back_hight', ''),
                            'around_neck': measurement_data.get('around_neck', ''),
                            'around_legs': measurement_data.get('around_legs', ''),
                            'full_chest': measurement_data.get('full_chest', ''),
                            'half_chest': measurement_data.get('half_chest', ''),
                            'full_belly': measurement_data.get('full_belly', ''),
                            'half_belly': measurement_data.get('half_belly', ''),
                            'neck_to_center_belly': measurement_data.get('neck_to_center_belly', ''),
                            'neck_to_chest': measurement_data.get('neck_to_chest', ''),
                            'shoulders_width': measurement_data.get('shoulders_width', ''),
                            'arm_tall': measurement_data.get('arm_tall', ''),
                            'arm_width_one': measurement_data.get('arm_width_one', ''),
                            'arm_width_two': measurement_data.get('arm_width_two', ''),
                            'arm_width_three': measurement_data.get('arm_width_three', ''),
                            'arm_width_four': measurement_data.get('arm_width_four', ''),
                        }

                        existing_measurement = Sizes.objects.filter(**measurement_filter).first()

                        if existing_measurement:
                            response_data['saved_items']['measurement'] = {
                                'id': existing_measurement.id,
                                'type': measurement_type,
                                'size_name': existing_measurement.size_name,
                                'created': False,
                                'message': 'Reusing existing measurement'
                            }
                            print(f"♻️ BulkSave: Reusing existing measurement (ID: {existing_measurement.id})")
                        else:
                            # Create new custom measurement
                            new_measurement = Sizes.objects.create(
                                user=user,
                                size_name=measurement_data.get('size_name', ''),
                                front_hight=measurement_data.get('front_hight', ''),
                                back_hight=measurement_data.get('back_hight', ''),
                                around_neck=measurement_data.get('around_neck', ''),
                                around_legs=measurement_data.get('around_legs', ''),
                                full_chest=measurement_data.get('full_chest', ''),
                                half_chest=measurement_data.get('half_chest', ''),
                                full_belly=measurement_data.get('full_belly', ''),
                                half_belly=measurement_data.get('half_belly', ''),
                                neck_to_center_belly=measurement_data.get('neck_to_center_belly', ''),
                                neck_to_chest=measurement_data.get('neck_to_chest', ''),
                                shoulders_width=measurement_data.get('shoulders_width', ''),
                                arm_tall=measurement_data.get('arm_tall', ''),
                                arm_width_one=measurement_data.get('arm_width_one', ''),
                                arm_width_two=measurement_data.get('arm_width_two', ''),
                                arm_width_three=measurement_data.get('arm_width_three', ''),
                                arm_width_four=measurement_data.get('arm_width_four', '')
                            )
                            response_data['saved_items']['measurement'] = {
                                'id': new_measurement.id,
                                'type': measurement_type,
                                'size_name': new_measurement.size_name,
                                'created': True,
                                'message': 'Custom measurement saved successfully'
                            }
                            print(f"✅ BulkSave: Created new custom measurement (ID: {new_measurement.id})")
                    except Exception as e:
                        response_data['saved_items']['measurement'] = {
                            'error': 'Failed to save custom measurement',
                            'message': str(e)
                        }
                        print(f"⚠️ BulkSave: Error saving custom measurement: {e}")
                else:
                    # Default measurement - just acknowledge
                    response_data['saved_items']['measurement'] = {
                        'type': measurement_type,
                        'size_name': measurement_data.get('size_name', ''),
                        'skipped': True,
                        'message': 'Default measurement will be used from selected size'
                    }

            # ========== 2. SAVE/UPDATE ADDRESS ==========
            if 'address' in data and data['address']:
                address_data = data['address']
                address_id = address_data.get('id')

                # Remove id from data for serializer
                address_payload = {k: v for k, v in address_data.items() if k != 'id'}

                if address_id:
                    # Update existing address
                    try:
                        address = Address.objects.get(id=address_id, user=user)
                        serializer = AddressSerializer(address, data=address_payload, partial=True, context={'request': request})
                        if serializer.is_valid():
                            serializer.save()
                            response_data['saved_items']['address'] = {
                                'id': address.id,
                                'created': False,
                                'full_name': address.full_name
                            }
                        else:
                            response_data['saved_items']['address'] = {
                                'error': 'Validation failed',
                                'details': serializer.errors
                            }
                    except Address.DoesNotExist:
                        response_data['saved_items']['address'] = {
                            'error': f'Address with id {address_id} not found'
                        }
                else:
                    # Create new address
                    serializer = AddressSerializer(data=address_payload, context={'request': request})
                    if serializer.is_valid():
                        address = serializer.save(user=user)
                        response_data['saved_items']['address'] = {
                            'id': address.id,
                            'created': True,
                            'full_name': address.full_name
                        }
                    else:
                        response_data['saved_items']['address'] = {
                            'error': 'Validation failed',
                            'details': serializer.errors
                        }

            # ========== 3. SAVE CART ITEMS (UserDesign) ==========
            if 'cart_items' in data and data['cart_items']:
                cart_items_data = data['cart_items']
                saved_designs = []

                for item_data in cart_items_data:
                    try:
                        # Get foreign key instances
                        initial_category = HomePageSelectionCategory.objects.filter(isHidden=False).first()
                        fabric_color = FabricColor.objects.filter(id=item_data.get('main_body_fabric_color_id')).first() if item_data.get('main_body_fabric_color_id') else None
                        collar = GholaType.objects.filter(id=item_data.get('selected_coller_type_id')).first() if item_data.get('selected_coller_type_id') else None
                        sleeve_left = SleevesType.objects.filter(id=item_data.get('selected_sleeve_left_type_id')).first() if item_data.get('selected_sleeve_left_type_id') else None
                        sleeve_right = SleevesType.objects.filter(id=item_data.get('selected_sleeve_right_type_id')).first() if item_data.get('selected_sleeve_right_type_id') else None
                        pocket = PocketType.objects.filter(id=item_data.get('selected_pocket_id')).first() if item_data.get('selected_pocket_id') else None
                        button = ButtonType.objects.filter(id=item_data.get('selected_button_id')).first() if item_data.get('selected_button_id') else None
                        button_strip = ButtonStripType.objects.filter(id=item_data.get('selected_button_strip_id')).first() if item_data.get('selected_button_strip_id') else None
                        body = BodyType.objects.filter(id=item_data.get('selected_body_type_id')).first() if item_data.get('selected_body_type_id') else None

                        # All components are nullable - save even incomplete designs

                        # Check if identical design already exists
                        design_filter = {
                            'user': user,
                            'initial_size_selected': initial_category,
                            'main_body_fabric_color': fabric_color,
                            'selected_coller_type': collar,
                            'selected_sleeve_left_type': sleeve_left,
                            'selected_sleeve_right_type': sleeve_right,
                            'selected_pocket_type': pocket,
                            'selected_button_type': button,
                            'selected_button_strip_type': button_strip,
                            'selected_body_type': body,
                        }

                        existing_design = UserDesign.objects.filter(**design_filter).first()

                        if existing_design:
                            saved_designs.append({
                                'id': existing_design.id,
                                'name': existing_design.design_name,
                                'created': False
                            })
                            print(f"♻️ BulkSave: Reusing existing design (ID: {existing_design.id})")
                        else:
                            # Create new design
                            design_total = item_data.get('design_total', 0.0)
                            print(f"💰 BulkSave: Saving design with design_total: {design_total}")

                            new_design = UserDesign.objects.create(
                                user=user,
                                design_name=item_data.get('design_name', ''),
                                initial_size_selected=initial_category,
                                main_body_fabric_color=fabric_color,
                                selected_coller_type=collar,
                                selected_sleeve_left_type=sleeve_left,
                                selected_sleeve_right_type=sleeve_right,
                                selected_pocket_type=pocket,
                                selected_button_type=button,
                                selected_button_strip_type=button_strip,
                                selected_body_type=body,
                                design_Total=design_total  # Read from Flutter request
                            )
                            saved_designs.append({
                                'id': new_design.id,
                                'name': new_design.design_name,
                                'created': True
                            })
                            print(f"✅ BulkSave: Created new design (ID: {new_design.id})")
                    except Exception as e:
                        print(f"⚠️ BulkSave: Error saving design '{item_data.get('design_name')}': {e}")
                        continue

                response_data['saved_items']['designs'] = {
                    'count': len(saved_designs),
                    'saved': saved_designs,
                    'message': f'Saved {len(saved_designs)} design(s) to backend'
                }

            return Response(response_data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to save cart data',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)
