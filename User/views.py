from django.shortcuts import render
from .serializers import AddressSerializer, userBasicInfoSerializer, UserProfileSerializer, UpdateFCMTokenSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from .models import Address, Profile
from django.contrib.auth.models import User
from django.db import transaction
from Sizes.models import Sizes
from Design.models import UserDesign, HomePageSelectionCategory, FabricColor, GholaType, SleevesType, PocketType, ButtonType, ButtonStripType, BodyType

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


class BulkSaveCartDataAPIView(APIView):
    """
    POST: Save/Update all cart-related data before checkout
    - Saves measurements (custom or default)
    - Saves/Updates address
    - Saves cart items as UserDesign

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

    @transaction.atomic
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

            # ========== 1. SKIP MEASUREMENT SAVING ==========
            # NOTE: Measurements are NOT saved to Sizes table from cart screen
            # They will be saved in Item.size_details JSON field during order creation
            if 'measurement' in data and data['measurement']:
                measurement_data = data['measurement']
                measurement_type = measurement_data.get('type', 'default')
                size_name = measurement_data.get('size_name', '')

                # Just acknowledge receipt without creating Sizes entries
                response_data['saved_items']['measurement'] = {
                    'type': measurement_type,
                    'size_name': size_name,
                    'skipped': True,
                    'message': 'Measurements will be saved during order creation'
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

            # ========== 3. SAVE/UPDATE CART ITEMS (UserDesign) ==========
            if 'cart_items' in data and data['cart_items']:
                saved_designs = []

                for item in data['cart_items']:
                    design_id = item.get('id')

                    try:
                        # Get required ForeignKey objects (only if IDs are provided)
                        category = None
                        if item.get('initial_size_selected_id'):
                            try:
                                category = HomePageSelectionCategory.objects.get(id=item['initial_size_selected_id'])
                            except HomePageSelectionCategory.DoesNotExist:
                                # If category doesn't exist, try to get a default one (first non-hidden category)
                                category = HomePageSelectionCategory.objects.filter(isHidden=False).first()

                        # If no category provided or found, use first available non-hidden category as fallback
                        if not category:
                            category = HomePageSelectionCategory.objects.filter(isHidden=False).first()

                        fabric_color = None
                        if item.get('main_body_fabric_color_id'):
                            fabric_color = FabricColor.objects.get(id=item['main_body_fabric_color_id'])

                        collar = None
                        if item.get('selected_coller_type_id'):
                            collar = GholaType.objects.get(id=item['selected_coller_type_id'])

                        sleeve_left = None
                        if item.get('selected_sleeve_left_type_id'):
                            sleeve_left = SleevesType.objects.get(id=item['selected_sleeve_left_type_id'])

                        sleeve_right = None
                        if item.get('selected_sleeve_right_type_id'):
                            sleeve_right = SleevesType.objects.get(id=item['selected_sleeve_right_type_id'])

                        pocket = None
                        if item.get('selected_pocket_id'):
                            pocket = PocketType.objects.get(id=item['selected_pocket_id'])

                        button = None
                        if item.get('selected_button_id'):
                            button = ButtonType.objects.get(id=item['selected_button_id'])

                        button_strip = None
                        if item.get('selected_button_strip_id'):
                            button_strip = ButtonStripType.objects.get(id=item['selected_button_strip_id'])

                        body_type = None
                        if item.get('selected_body_type_id'):
                            body_type = BodyType.objects.get(id=item['selected_body_type_id'])

                        # Calculate total price (only add prices for non-null components)
                        total_price = 0
                        if category:
                            total_price += category.initial_price
                        if fabric_color:
                            total_price += fabric_color.total_price
                        if collar:
                            total_price += collar.initial_price
                        if sleeve_left:
                            total_price += sleeve_left.initial_price
                        if sleeve_right:
                            total_price += sleeve_right.initial_price
                        if pocket:
                            total_price += pocket.initial_price
                        if button:
                            total_price += button.initial_price
                        if button_strip:
                            total_price += button_strip.initial_price
                        if body_type:
                            total_price += body_type.initial_price

                        design_defaults = {
                            'design_name': item.get('design_name', ''),
                            'design_Total': total_price
                        }

                        # Only add non-null ForeignKey fields
                        if category:
                            design_defaults['initial_size_selected'] = category
                        if fabric_color:
                            design_defaults['main_body_fabric_color'] = fabric_color
                        if collar:
                            design_defaults['selected_coller_type'] = collar
                        if sleeve_left:
                            design_defaults['selected_sleeve_left_type'] = sleeve_left
                        if sleeve_right:
                            design_defaults['selected_sleeve_right_type'] = sleeve_right
                        if pocket:
                            design_defaults['selected_pocket_type'] = pocket
                        if button:
                            design_defaults['selected_button_type'] = button
                        if button_strip:
                            design_defaults['selected_button_strip_type'] = button_strip
                        if body_type:
                            design_defaults['selected_body_type'] = body_type

                        if design_id:
                            # EDIT MODE: Update existing design by ID
                            design = UserDesign.objects.filter(id=design_id, user=user).first()
                            if design:
                                for key, value in design_defaults.items():
                                    setattr(design, key, value)
                                design.save()
                                created = False
                            else:
                                # If design not found, create new
                                design = UserDesign.objects.create(user=user, **design_defaults)
                                created = True
                        else:
                            # NORMAL MODE: Check for duplicate design before creating
                            # Build query filter for checking duplicates
                            duplicate_filter = {'user': user}
                            if category:
                                duplicate_filter['initial_size_selected'] = category
                            if fabric_color:
                                duplicate_filter['main_body_fabric_color'] = fabric_color
                            if collar:
                                duplicate_filter['selected_coller_type'] = collar
                            if sleeve_left:
                                duplicate_filter['selected_sleeve_left_type'] = sleeve_left
                            if sleeve_right:
                                duplicate_filter['selected_sleeve_right_type'] = sleeve_right
                            if pocket:
                                duplicate_filter['selected_pocket_type'] = pocket
                            if button:
                                duplicate_filter['selected_button_type'] = button
                            if button_strip:
                                duplicate_filter['selected_button_strip_type'] = button_strip
                            if body_type:
                                duplicate_filter['selected_body_type'] = body_type

                            # Check for existing identical design
                            existing_design = UserDesign.objects.filter(**duplicate_filter).first()

                            if existing_design:
                                # Use existing design if all selections match
                                design = existing_design
                                # Update design name and total if they changed
                                design.design_name = design_defaults.get('design_name', design.design_name)
                                design.design_Total = design_defaults.get('design_Total', design.design_Total)
                                design.save()
                                created = False
                            else:
                                # Create new design
                                design = UserDesign.objects.create(user=user, **design_defaults)
                                created = True

                        saved_designs.append({
                            'id': design.id,
                            'design_name': design.design_name,
                            'total_price': str(total_price),
                            'created': created
                        })

                    except Exception as e:
                        saved_designs.append({
                            'error': f'Failed to save design: {str(e)}',
                            'item': item
                        })

                response_data['saved_items']['designs'] = saved_designs

            return Response(response_data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to save cart data',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)
