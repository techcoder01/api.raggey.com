from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.db import transaction


# Custom SessionAuthentication that doesn't enforce CSRF for API calls
class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check for session authentication
from .serializers import (
    FabricTypeSerializer, FabricColorSerializer, FabricColorDetailSerializer,
    GholaTypeSerializer, SleevesTypeSerializer, PocketTypeSerializer,
    ButtonTypeSerializer, ButtonStripTypeSerializer, BodyTypeSerializer,
    HomePageSelectionCategorySerializer, UserDesignSerializer
)
from django.contrib.auth.models import User
from .models import (
    FabricType, FabricColor,
    SleevesType, GholaType, PocketType, ButtonType, ButtonStripType, BodyType,
    HomePageSelectionCategory, UserDesign, InventoryTransaction
)
from .utils import hableImageUpload
from typing import Dict
from decimal import Decimal

#================== END USER SIDE ====================================================
class MainCatogeryUserSideAPIView(APIView):
    def get(self, request, pk=None, format=None):
        queryset = HomePageSelectionCategory.objects.filter(isHidden=False)
        serializer = HomePageSelectionCategorySerializer(
            queryset, context={'request': request},  many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')



class FetchFabricAPIView(APIView):
    """
    NEW: Fetch all fabric types (base fabrics without colors)
    Returns list of FabricType objects
    """
    def get(self, request, pk=None, format=None):
        queryset = FabricType.objects.filter(isHidden=False)
        serializer = FabricTypeSerializer(
            queryset, context={'request': request},  many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')


class FetchFabricDetailAPIView(APIView):
    """
    NEW: Fetch detailed information for a specific fabric (PUBLIC - no auth required)
    URL: /design/fetch/fabric/<fabric_id>/
    Returns single FabricType object with all details
    """
    def get(self, request, fabric_id=None, format=None):
        try:
            fabric = FabricType.objects.get(id=fabric_id, isHidden=False)
            serializer = FabricTypeSerializer(fabric, context={'request': request}, many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        except FabricType.DoesNotExist:
            return Response({'error': 'Fabric not found'}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)


class FetchFabricColorsAPIView_New(APIView):
    """
    NEW: Get all color variants for a specific fabric
    URL: /design/fetch/fabric/<fabric_id>/colors/
    Returns all FabricColor records for the given FabricType
    """
    def get(self, request, fabric_id=None, format=None):
        try:
            # Get the base fabric
            fabric = FabricType.objects.get(id=fabric_id, isHidden=False)

            # Get all color variants for this fabric (including out of stock)
            color_variants = FabricColor.objects.filter(
                fabric_type=fabric
            ).order_by('color_name_eng')

            serializer = FabricColorSerializer(color_variants, context={'request': request}, many=True)

            return Response({
                'fabric_id': fabric_id,
                'fabric_name_eng': fabric.fabric_name_eng,
                'fabric_name_arb': fabric.fabric_name_arb,
                'base_price': fabric.base_price,
                'available_colors': serializer.data,
                'total_colors': color_variants.count()
            }, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        except FabricType.DoesNotExist:
            return Response({'error': 'Fabric not found'}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)
    

class FetchCollerAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch collar options. Can filter by fabric_type_id (FabricType ID).
        Returns all collars for all colors of the specified fabric type.
        This allows users to mix and match colors.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = GholaType.objects.all()

        # Filter by fabric type (returns collars for all colors of this fabric)
        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = GholaTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class FetchSleevesRightAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch right sleeve options. Can filter by fabric_type_id (FabricType ID).
        Returns all right sleeves for all colors of the specified fabric type.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = SleevesType.objects.filter(is_right_side=True)

        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = SleevesTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class FetchSleevesLeftAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch left sleeve options. Can filter by fabric_type_id (FabricType ID).
        Returns all left sleeves for all colors of the specified fabric type.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = SleevesType.objects.filter(is_right_side=False)

        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = SleevesTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class FetchPocketAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch pocket options. Can filter by fabric_type_id (FabricType ID).
        Returns all pockets for all colors of the specified fabric type.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = PocketType.objects.all()

        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = PocketTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class FetchButtonAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch button options. Can filter by fabric_type_id (FabricType ID).
        Returns all buttons (including out of stock) for all colors of the specified fabric type.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = ButtonType.objects.all()

        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = ButtonTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class FetchButtonStripAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch button strip options. Can filter by fabric_type_id (FabricType ID).
        Returns all button strips for all colors of the specified fabric type.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = ButtonStripType.objects.all()

        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = ButtonStripTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class FetchBodyAPIView(APIView):
    def get(self, request, pk=None, format=None):
        """
        Fetch body options. Can filter by fabric_type_id (FabricType ID).
        Returns all body types for all colors of the specified fabric type.
        """
        fabric_type_id = request.GET.get('fabric_type_id', None)

        queryset = BodyType.objects.all()

        if fabric_type_id:
            queryset = queryset.filter(fabric_type_id=fabric_type_id)

        serializer = BodyTypeSerializer(queryset, context={'request': request}, many=True)
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

class UserDesignAPIView(APIView):  
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            queryset = UserDesign.objects.filter( user = user )
            serializer = UserDesignSerializer(
                queryset, context={'request': request},  many=True)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Create New Design
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            data = request.data

            # Existing fields
            initial_size_selected = HomePageSelectionCategory.objects.get(id=data['initial_size_selected_id'])
            main_body_fabric_color = FabricColor.objects.get(id=data['main_body_fabric_color_id'])
            selected_coller_type = GholaType.objects.get(id=data['selected_coller_type_id'])
            selected_sleeve_left_type = SleevesType.objects.get(id=data['selected_sleeve_left_type_id'])
            selected_sleeve_right_type = SleevesType.objects.get(id=data['selected_sleeve_right_type_id'])

            # FIX ISSUE 1 & 5: Add pocket, button, and button strip
            selected_pocket = PocketType.objects.get(id=data['selected_pocket_id'])
            selected_button = ButtonType.objects.get(id=data['selected_button_id'])
            selected_button_strip = ButtonStripType.objects.get(id=data['selected_button_strip_id'])

            # Get optional design name
            design_name = data.get('design_name', None)

            user_design = UserDesign.objects.create(
                user=user,
                design_name=design_name,
                initial_size_selected=initial_size_selected,
                main_body_fabric_color=main_body_fabric_color,
                selected_coller_type=selected_coller_type,
                selected_sleeve_left_type=selected_sleeve_left_type,
                selected_sleeve_right_type=selected_sleeve_right_type,
                selected_pocket_type=selected_pocket,
                selected_button_type=selected_button,
                selected_button_strip_type=selected_button_strip
            )

            # FIX ISSUE 5: Complete price calculation
            user_design.design_Total = (
                initial_size_selected.initial_price +
                main_body_fabric_color.total_price +
                selected_coller_type.initial_price +
                selected_sleeve_left_type.initial_price +
                selected_sleeve_right_type.initial_price +
                selected_pocket.initial_price +
                selected_button.initial_price +
                selected_button_strip.initial_price
            )
            user_design.save()

            serializer = UserDesignSerializer(user_design, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Update Design
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            data = request.data

            # Existing fields
            initial_size_selected = HomePageSelectionCategory.objects.get(id=data['initial_size_selected_id'])
            main_body_fabric_color = FabricColor.objects.get(id=data['main_body_fabric_color_id'])
            selected_coller_type = GholaType.objects.get(id=data['selected_coller_type_id'])
            selected_sleeve_left_type = SleevesType.objects.get(id=data['selected_sleeve_left_type_id'])
            selected_sleeve_right_type = SleevesType.objects.get(id=data['selected_sleeve_right_type_id'])

            # FIX ISSUE 1 & 5: Add pocket, button, and button strip
            selected_pocket = PocketType.objects.get(id=data['selected_pocket_id'])
            selected_button = ButtonType.objects.get(id=data['selected_button_id'])
            selected_button_strip = ButtonStripType.objects.get(id=data['selected_button_strip_id'])

            design = UserDesign.objects.get(id=pk)
            if design:
                # Update design name if provided
                if 'design_name' in data:
                    design.design_name = data['design_name']

                design.initial_size_selected = initial_size_selected
                design.main_body_fabric_color = main_body_fabric_color
                design.selected_coller_type = selected_coller_type
                design.selected_sleeve_left_type = selected_sleeve_left_type
                design.selected_sleeve_right_type = selected_sleeve_right_type
                design.selected_pocket_type = selected_pocket
                design.selected_button_type = selected_button
                design.selected_button_strip_type = selected_button_strip

                # FIX ISSUE 5: Complete price calculation
                design.design_Total = (
                    initial_size_selected.initial_price +
                    main_body_fabric.initial_price +
                    selected_coller_type.initial_price +
                    selected_sleeve_left_type.initial_price +
                    selected_sleeve_right_type.initial_price +
                    selected_pocket.initial_price +
                    selected_button.initial_price +
                    selected_button_strip.initial_price
                )

                design.save()
                serializer = UserDesignSerializer(design, context={'request': request})
                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

# ================= Admin Side (Admin,Partner,Data-Entry) =========================
#================== MAIN (HOME PAGE) CATEGORY HANDLER ===============================================
class MainCatogeryAdminSideAPIView(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication, SessionAuthentication]

    # Fetch main Category Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
            queryset = HomePageSelectionCategory.objects.get(id=pk)
            serializer = HomePageSelectionCategorySerializer(
                queryset, context={'request': request},  many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Delete Main Category 
    def delete(self, request, pk):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
                deleted_category = HomePageSelectionCategory.objects.get(id=pk)
                if deleted_category:
                    deleted_category.delete()
                    return Response('deleted', status=HTTP_200_OK)
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    
    # Create Main Category
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if not user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=HTTP_400_BAD_REQUEST)
        if not (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            return Response({'error': 'Permission denied'}, status=HTTP_400_BAD_REQUEST)

        data = request.data
        required_fields = ['main_category_name_eng', 'main_category_name_arb', 'initial_price']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            return Response({'error': f'Missing required fields: {", ".join(missing_fields)}'}, status=HTTP_400_BAD_REQUEST)

        image_obtain = None
        cover_data = data.get('cover')
        if cover_data and isinstance(cover_data, dict):
            image_obtain = hableImageUpload(cover_data)

        category = HomePageSelectionCategory.objects.create(
            main_category_name_eng=data['main_category_name_eng'],
            main_category_name_arb=data['main_category_name_arb'],
            duration_delivery_period=data.get('duration_delivery_period', ''),
            initial_price=Decimal(str(data['initial_price'])),
            isHidden=data.get('isHidden', False),
            is_comming_soon=data.get('is_comming_soon', False),
            cover=image_obtain)
        serializer = HomePageSelectionCategorySerializer(
            category, context={'request': request})
        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
    # Update Main Category 
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
                data = request.data
                category = HomePageSelectionCategory.objects.get(id=pk)
                if category:
                    category.main_category_name_eng=data['main_category_name_eng']
                    category.main_category_name_arb=data['main_category_name_arb']
                    category.duration_delivery_period=data['duration_delivery_period']
                    category.initial_price=Decimal(data['initial_price'],)
                    category.isHidden = data['isHidden']
                    category.is_comming_soon = data['is_comming_soon']
                    if data['cover']:
                        if isinstance(data['cover'], Dict):
                            image_obtain = hableImageUpload(data['cover'])
                            category.cover = image_obtain
                    else:
                        category.cover = None                                              
                    category.save()
                    serializer = HomePageSelectionCategorySerializer(
                        category, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)


#================== NEW: FABRIC TYPE HANDLER ===============================================
class FabricTypeAdminSideAPIView(APIView):
    """Admin CRUD for FabricType (base fabric without color)"""
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]

    # Fetch FabricType Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            queryset = FabricType.objects.get(id=pk)
            serializer = FabricTypeSerializer(queryset, context={'request': request}, many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete a FabricType
    def delete(self, request, pk):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                deleted_fabric = FabricType.objects.get(id=pk)
                if deleted_fabric:
                    deleted_fabric.delete()
                    return Response('deleted', status=HTTP_200_OK)
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Create a FabricType
    def post(self, request, pk=None, format=None):
        user = self.request.user

        # Check if user is authenticated
        if not user.is_authenticated:
            return Response({'error': 'User not authenticated'}, status=HTTP_401_UNAUTHORIZED)

        try:
            # Check permissions - Allow superuser/staff OR users with proper profile permission
            has_permission = False

            if user.is_superuser or user.is_staff:
                has_permission = True
            elif hasattr(user, 'profile'):
                if user.profile.premission in ["Admin", "Partner", "Data-Entry"]:
                    has_permission = True

            if not has_permission:
                error_msg = 'Insufficient permissions. '
                if hasattr(user, 'profile'):
                    error_msg += f'Your role is: {user.profile.premission}. '
                else:
                    error_msg += 'User profile not found. '
                error_msg += 'Required: Admin, Partner, or Data-Entry role, or staff/superuser status.'
                return Response({'error': error_msg}, status=HTTP_401_UNAUTHORIZED)

            # Process the request
            data = request.data

            # Create fabric without cover first
            fabric = FabricType.objects.create(
                fabric_name_eng=data['fabric_name_eng'],
                fabric_name_arb=data['fabric_name_arb'],
                base_price=data['base_price'],
                isHidden=data.get('isHidden', False)
            )

            # Upload and assign cover separately if provided
            if data.get('cover'):
                image_obtain = hableImageUpload(data['cover'])
                fabric.cover = image_obtain
                fabric.save()
                # Refresh from database to get the proper CloudinaryField object
                fabric.refresh_from_db()

            # Refresh again to ensure we have the latest state
            fabric.refresh_from_db()

            serializer = FabricTypeSerializer(fabric, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        except Exception as e:
            import traceback
            error_message = f"Error creating fabric type: {str(e)}\n{traceback.format_exc()}"
            print(error_message)
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)

    # Update a FabricType
    def put(self, request, pk=None, format=None):
        user = self.request.user

        # Check if user is authenticated
        if not user.is_authenticated:
            return Response({'error': 'User not authenticated'}, status=HTTP_401_UNAUTHORIZED)

        # Check permissions - Allow superuser/staff OR users with proper profile permission
        has_permission = False
        if user.is_superuser or user.is_staff:
            has_permission = True
        elif hasattr(user, 'profile') and user.profile.premission in ["Admin", "Partner", "Data-Entry"]:
            has_permission = True

        if has_permission:
                data = request.data
                fabric = FabricType.objects.get(id=pk)
                if fabric:
                    fabric.fabric_name_eng = data['fabric_name_eng']
                    fabric.fabric_name_arb = data['fabric_name_arb']
                    fabric.base_price = data['base_price']
                    fabric.isHidden = data.get('isHidden', False)

                    if data.get('cover'):
                        if isinstance(data['cover'], Dict):
                            image_obtain = hableImageUpload(data['cover'])
                            fabric.cover = image_obtain
                    else:
                        fabric.cover = None

                    fabric.save()
                    serializer = FabricTypeSerializer(fabric, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        error_msg = 'Insufficient permissions. '
        if hasattr(user, 'profile'):
            error_msg += f'Your role is: {user.profile.premission}. '
        else:
            error_msg += 'User profile not found. '
        error_msg += 'Required: Admin, Partner, or Data-Entry role, or staff/superuser status.'
        return Response({'error': error_msg}, status=HTTP_401_UNAUTHORIZED)


#================== NEW: FABRIC COLOR HANDLER ===============================================
class FabricColorAdminSideAPIView(APIView):
    """Admin CRUD for FabricColor (color variants of a fabric)"""
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]

    # Fetch FabricColor Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            queryset = FabricColor.objects.get(id=pk)
            serializer = FabricColorDetailSerializer(queryset, context={'request': request}, many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete a FabricColor
    def delete(self, request, pk):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                deleted_color = FabricColor.objects.get(id=pk)
                if deleted_color:
                    deleted_color.delete()
                    return Response('deleted', status=HTTP_200_OK)
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Create a FabricColor
    def post(self, request, pk=None, format=None):
        user = self.request.user

        # Check if user is authenticated
        if not user.is_authenticated:
            return Response({'error': 'User not authenticated'}, status=HTTP_401_UNAUTHORIZED)

        # Check permissions - Allow superuser/staff OR users with proper profile permission
        has_permission = False
        if user.is_superuser or user.is_staff:
            has_permission = True
        elif hasattr(user, 'profile') and user.profile.premission in ["Admin", "Partner", "Data-Entry"]:
            has_permission = True

        if has_permission:
            try:
                data = request.data

                # Get the fabric type
                fabric_type = FabricType.objects.get(id=data['fabric_type_id'])

                # Create fabric color without cover first
                fabric_color = FabricColor.objects.create(
                    fabric_type=fabric_type,
                    color_name_eng=data['color_name_eng'],
                    color_name_arb=data['color_name_arb'],
                    quantity=data.get('quantity', 0),
                    inStock=data.get('inStock', True),
                    price_adjustment=data.get('price_adjustment', 0.000)
                )

                # Upload and assign cover separately if provided
                if data.get('cover'):
                    image_obtain = hableImageUpload(data['cover'])
                    fabric_color.cover = image_obtain
                    fabric_color.save()

                serializer = FabricColorDetailSerializer(fabric_color, context={'request': request})
                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
            except Exception as e:
                import traceback
                error_message = f"Error creating fabric color: {str(e)}\n{traceback.format_exc()}"
                print(error_message)
                return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)

        error_msg = 'Insufficient permissions. '
        if hasattr(user, 'profile'):
            error_msg += f'Your role is: {user.profile.premission}. '
        else:
            error_msg += 'User profile not found. '
        error_msg += 'Required: Admin, Partner, or Data-Entry role, or staff/superuser status.'
        return Response({'error': error_msg}, status=HTTP_401_UNAUTHORIZED)

    # Update a FabricColor
    def put(self, request, pk=None, format=None):
        user = self.request.user

        # Check if user is authenticated
        if not user.is_authenticated:
            return Response({'error': 'User not authenticated'}, status=HTTP_401_UNAUTHORIZED)

        # Check permissions - Allow superuser/staff OR users with proper profile permission
        has_permission = False
        if user.is_superuser or user.is_staff:
            has_permission = True
        elif hasattr(user, 'profile') and user.profile.premission in ["Admin", "Partner", "Data-Entry"]:
            has_permission = True

        if has_permission:
            data = request.data
            fabric_color = FabricColor.objects.get(id=pk)
            if fabric_color:
                fabric_color.color_name_eng = data['color_name_eng']
                fabric_color.color_name_arb = data['color_name_arb']
                fabric_color.quantity = data.get('quantity', 0)
                fabric_color.inStock = data.get('inStock', True)
                fabric_color.price_adjustment = data.get('price_adjustment', 0.000)

                # Update fabric type if provided
                if data.get('fabric_type_id'):
                    fabric_type = FabricType.objects.get(id=data['fabric_type_id'])
                    fabric_color.fabric_type = fabric_type

                if data.get('cover'):
                    if isinstance(data['cover'], Dict):
                        image_obtain = hableImageUpload(data['cover'])
                        fabric_color.cover = image_obtain
                elif data.get('cover') is None:
                    fabric_color.cover = None

                fabric_color.save()
                serializer = FabricColorDetailSerializer(fabric_color, context={'request': request})
                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        error_msg = 'Insufficient permissions. '
        if hasattr(user, 'profile'):
            error_msg += f'Your role is: {user.profile.premission}. '
        else:
            error_msg += 'User profile not found. '
        error_msg += 'Required: Admin, Partner, or Data-Entry role, or staff/superuser status.'
        return Response({'error': error_msg}, status=HTTP_401_UNAUTHORIZED)


#================== GOLATYPE HANDLER ===============================================
class GholaTypeAdminSideAPIView(APIView):
    # Fetch Ghola Type Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
            queryset = GholaType.objects.get(id=pk)
            serializer = GholaTypeSerializer(
                queryset, context={'request': request},  many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Delete a Gola Type 
    def delete(self, request, pk):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
                deleted_ghola_type = GholaType.objects.get(id=pk)
                if deleted_ghola_type:
                    deleted_ghola_type.delete()
                    return Response('deleted', status=HTTP_200_OK)
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    
    # Create a Ghola Type
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    if data.get('cover'):
                        image_obtain = hableImageUpload(data['cover'])

                    ghola = GholaType.objects.create(
                        ghola_type_name_eng=data['ghola_type_name_eng'],
                        ghola_type_name_arb=data['ghola_type_name_arb'],
                        initial_price=Decimal(data['initial_price']),
                        cover=image_obtain,
                        fabric_type=fabric_color.fabric_type,
                        fabric_color=fabric_color
                    )

                    serializer = GholaTypeSerializer(ghola, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Update a Ghola Type
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    ghola_type = GholaType.objects.get(id=pk)
                    if ghola_type:
                        ghola_type.ghola_type_name_eng = data['ghola_type_name_eng']
                        ghola_type.ghola_type_name_arb = data['ghola_type_name_arb']
                        ghola_type.initial_price = Decimal(data['initial_price'])
                        ghola_type.fabric_type = fabric_color.fabric_type
                        ghola_type.fabric_color = fabric_color

                        if data.get('cover'):
                            if isinstance(data['cover'], Dict):
                                image_obtain = hableImageUpload(data['cover'])
                                ghola_type.cover = image_obtain
                        elif data.get('cover') is None:
                            ghola_type.cover = None

                        ghola_type.save()
                        serializer = GholaTypeSerializer(ghola_type, context={'request': request})
                        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

#================== SLEEVES TYPE HANDLER ===============================================
class SleevesTypeAdminSideAPIView(APIView):
    # Fetch Sleeve Type Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
            queryset = SleevesType.objects.get(id=pk)
            serializer = SleevesTypeSerializer(
                queryset, context={'request': request},  many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Delete a Sleeve Type 
    def delete(self, request, pk):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry" ):
                deleted_sleeves_type = SleevesType.objects.get(id=pk)
                if deleted_sleeves_type:
                    deleted_sleeves_type.delete()
                    return Response('deleted', status=HTTP_200_OK)
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    
    # Create a Sleeve Type
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    if data.get('cover'):
                        image_obtain = hableImageUpload(data['cover'])

                    sleeve = SleevesType.objects.create(
                        sleeves_type_name_eng=data['sleeves_type_name_eng'],
                        sleeves_type_name_arb=data['sleeves_type_name_arb'],
                        initial_price=Decimal(data['initial_price']),
                        cover=image_obtain,
                        fabric_type=fabric_color.fabric_type,
                        fabric_color=fabric_color,
                        is_right_side=data.get('is_right_side', False)
                    )
                    serializer = SleevesTypeSerializer(sleeve, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Update a Sleeve Type
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    sleeve_type = SleevesType.objects.get(id=pk)
                    if sleeve_type:
                        sleeve_type.sleeves_type_name_eng = data['sleeves_type_name_eng']
                        sleeve_type.sleeves_type_name_arb = data['sleeves_type_name_arb']
                        sleeve_type.initial_price = Decimal(data['initial_price'])
                        sleeve_type.fabric_type = fabric_color.fabric_type
                        sleeve_type.fabric_color = fabric_color
                        sleeve_type.is_right_side = data.get('is_right_side', False)

                        if data.get('cover'):
                            if isinstance(data['cover'], Dict):
                                image_obtain = hableImageUpload(data['cover'])
                                sleeve_type.cover = image_obtain
                        elif data.get('cover') is None:
                            sleeve_type.cover = None
                        sleeve_type.save()
                        serializer = SleevesTypeSerializer(sleeve_type, context={'request': request})
                        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

#================== ADMIN SIDE POCKET TYPE ====================================================
class PocketTypeAdminSideAPIView(APIView):
    # Get Pocket Type Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                pocket_type = PocketType.objects.get(id=pk)
                if pocket_type:
                    serializer = PocketTypeSerializer(
                        pocket_type, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Create a Pocket Type
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    if data.get('cover'):
                        image_obtain = hableImageUpload(data['cover'])

                    pocket = PocketType.objects.create(
                        pocket_type_name_eng=data['pocket_type_name_eng'],
                        pocket_type_name_arb=data['pocket_type_name_arb'],
                        initial_price=Decimal(data['initial_price']),
                        cover=image_obtain,
                        fabric_type=fabric_color.fabric_type,
                        fabric_color=fabric_color
                    )
                    serializer = PocketTypeSerializer(pocket, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Update a Pocket Type
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    pocket_type = PocketType.objects.get(id=pk)
                    if pocket_type:
                        pocket_type.pocket_type_name_eng = data['pocket_type_name_eng']
                        pocket_type.pocket_type_name_arb = data['pocket_type_name_arb']
                        pocket_type.initial_price = Decimal(data['initial_price'])
                        pocket_type.fabric_type = fabric_color.fabric_type
                        pocket_type.fabric_color = fabric_color

                        if data.get('cover'):
                            if isinstance(data['cover'], Dict):
                                image_obtain = hableImageUpload(data['cover'])
                                pocket_type.cover = image_obtain
                        elif data.get('cover') is None:
                            pocket_type.cover = None
                        pocket_type.save()
                        serializer = PocketTypeSerializer(pocket_type, context={'request': request})
                        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete Pocket Type
    def delete(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                pocket_type = PocketType.objects.get(id=pk)
                if pocket_type:
                    pocket_type.delete()
                    return Response('Pocket Type Deleted', status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

#================== ADMIN SIDE BUTTON TYPE ====================================================
class ButtonTypeAdminSideAPIView(APIView):
    # Get Button Type Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                button_type = ButtonType.objects.get(id=pk)
                if button_type:
                    serializer = ButtonTypeSerializer(
                        button_type, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Create a Button Type
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    if data.get('cover'):
                        image_obtain = hableImageUpload(data['cover'])

                    button = ButtonType.objects.create(
                        button_type_name_eng=data['button_type_name_eng'],
                        button_type_name_arb=data['button_type_name_arb'],
                        initial_price=Decimal(data['initial_price']),
                        cover=image_obtain,
                        inStock=data.get('inStock', True),
                        fabric_type=fabric_color.fabric_type,
                        fabric_color=fabric_color
                    )
                    serializer = ButtonTypeSerializer(button, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Update a Button Type
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    button_type = ButtonType.objects.get(id=pk)
                    if button_type:
                        button_type.button_type_name_eng = data['button_type_name_eng']
                        button_type.button_type_name_arb = data['button_type_name_arb']
                        button_type.inStock = data.get('inStock', True)
                        button_type.initial_price = Decimal(data['initial_price'])
                        button_type.fabric_type = fabric_color.fabric_type
                        button_type.fabric_color = fabric_color

                        if data.get('cover'):
                            if isinstance(data['cover'], Dict):
                                image_obtain = hableImageUpload(data['cover'])
                                button_type.cover = image_obtain
                        elif data.get('cover') is None:
                            button_type.cover = None
                        button_type.save()
                        serializer = ButtonTypeSerializer(button_type, context={'request': request})
                        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete Button Type
    def delete(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                button_type = ButtonType.objects.get(id=pk)
                if button_type:
                    button_type.delete()
                    return Response('Button Type Deleted', status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

#================== ADMIN SIDE BUTTON STRIP TYPE ====================================================
class ButtonStripTypeAdminSideAPIView(APIView):
    # Get Button Strip Type Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                button_strip_type = ButtonStripType.objects.get(id=pk)
                if button_strip_type:
                    serializer = ButtonStripTypeSerializer(
                        button_strip_type, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Create a Button Strip Type
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    if data.get('cover'):
                        image_obtain = hableImageUpload(data['cover'])

                    button_strip = ButtonStripType.objects.create(
                        button_strip_type_name_eng=data['button_strip_type_name_eng'],
                        button_strip_type_name_arb=data['button_strip_type_name_arb'],
                        initial_price=Decimal(data['initial_price']),
                        cover=image_obtain,
                        fabric_type=fabric_color.fabric_type,
                        fabric_color=fabric_color
                    )
                    serializer = ButtonStripTypeSerializer(button_strip, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Update a Button Strip Type
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    button_strip_type = ButtonStripType.objects.get(id=pk)
                    if button_strip_type:
                        button_strip_type.button_strip_type_name_eng = data['button_strip_type_name_eng']
                        button_strip_type.button_strip_type_name_arb = data['button_strip_type_name_arb']
                        button_strip_type.initial_price = Decimal(data['initial_price'])
                        button_strip_type.fabric_type = fabric_color.fabric_type
                        button_strip_type.fabric_color = fabric_color

                        if data.get('cover'):
                            if isinstance(data['cover'], Dict):
                                image_obtain = hableImageUpload(data['cover'])
                                button_strip_type.cover = image_obtain
                        elif data.get('cover') is None:
                            button_strip_type.cover = None
                        button_strip_type.save()
                        serializer = ButtonStripTypeSerializer(button_strip_type, context={'request': request})
                        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete Button Strip Type
    def delete(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                button_strip_type = ButtonStripType.objects.get(id=pk)
                if button_strip_type:
                    button_strip_type.delete()
                    return Response('Button Strip Type Deleted', status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

#================== BODY TYPE ADMIN SIDE API ====================================================
class BodyTypeAdminSideAPIView(APIView):
    # Get Body Type Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                body_type = BodyType.objects.get(id=pk)
                if body_type:
                    serializer = BodyTypeSerializer(
                        body_type, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Create a Body Type
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    if data.get('cover'):
                        image_obtain = hableImageUpload(data['cover'])

                    body = BodyType.objects.create(
                        body_type_name_eng=data['body_type_name_eng'],
                        body_type_name_arb=data['body_type_name_arb'],
                        initial_price=Decimal(data['initial_price']),
                        cover=image_obtain,
                        fabric_type=fabric_color.fabric_type,
                        fabric_color=fabric_color
                    )
                    serializer = BodyTypeSerializer(body, context={'request': request})
                    return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Update a Body Type
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                data = request.data
                image_obtain = None

                # Get FabricColor
                fabric_color = FabricColor.objects.get(id=int(data['fabric_color_id']))

                if fabric_color:
                    body_type = BodyType.objects.get(id=pk)
                    if body_type:
                        body_type.body_type_name_eng = data['body_type_name_eng']
                        body_type.body_type_name_arb = data['body_type_name_arb']
                        body_type.initial_price = Decimal(data['initial_price'])
                        body_type.fabric_type = fabric_color.fabric_type
                        body_type.fabric_color = fabric_color

                        if data.get('cover'):
                            if isinstance(data['cover'], Dict):
                                image_obtain = hableImageUpload(data['cover'])
                                body_type.cover = image_obtain
                        elif data.get('cover') is None:
                            body_type.cover = None
                        body_type.save()
                        serializer = BodyTypeSerializer(body_type, context={'request': request})
                        return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete Body Type
    def delete(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            if (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
                body_type = BodyType.objects.get(id=pk)
                if body_type:
                    body_type.delete()
                    return Response('Body Type Deleted', status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)


#================== CALCULATE DESIGN PRICE API ====================================================
class CalculateDesignPriceAPIView(APIView):
    """
    Calculate total price for selected design components.
    POST endpoint that accepts component IDs and returns calculated total price.
    Endpoint: /design/calculate-price/
    """
    permission_classes = []  # Public endpoint

    def post(self, request, format=None):
        try:
            data = request.data
            total_price = Decimal('0.000')

            # Add category price (initial size) if provided
            if data.get('category_id'):
                try:
                    category = HomePageSelectionCategory.objects.get(id=data['category_id'])
                    total_price += category.initial_price
                except HomePageSelectionCategory.DoesNotExist:
                    return Response({
                        'error': 'Category not found',
                        'message': f"Category with ID {data['category_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add fabric color price if provided
            if data.get('fabric_color_id'):
                try:
                    fabric_color = FabricColor.objects.get(id=data['fabric_color_id'])
                    total_price += fabric_color.total_price
                except FabricColor.DoesNotExist:
                    return Response({
                        'error': 'Fabric color not found',
                        'message': f"Fabric color with ID {data['fabric_color_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add collar price if provided
            if data.get('collar_id'):
                try:
                    collar = GholaType.objects.get(id=data['collar_id'])
                    total_price += collar.initial_price
                except GholaType.DoesNotExist:
                    return Response({
                        'error': 'Collar not found',
                        'message': f"Collar with ID {data['collar_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add sleeve left price if provided
            if data.get('sleeve_left_id'):
                try:
                    sleeve_left = SleevesType.objects.get(id=data['sleeve_left_id'])
                    total_price += sleeve_left.initial_price
                except SleevesType.DoesNotExist:
                    return Response({
                        'error': 'Left sleeve not found',
                        'message': f"Left sleeve with ID {data['sleeve_left_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add sleeve right price if provided
            if data.get('sleeve_right_id'):
                try:
                    sleeve_right = SleevesType.objects.get(id=data['sleeve_right_id'])
                    total_price += sleeve_right.initial_price
                except SleevesType.DoesNotExist:
                    return Response({
                        'error': 'Right sleeve not found',
                        'message': f"Right sleeve with ID {data['sleeve_right_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add pocket price if provided
            if data.get('pocket_id'):
                try:
                    pocket = PocketType.objects.get(id=data['pocket_id'])
                    total_price += pocket.initial_price
                except PocketType.DoesNotExist:
                    return Response({
                        'error': 'Pocket not found',
                        'message': f"Pocket with ID {data['pocket_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add button price if provided
            if data.get('button_id'):
                try:
                    button = ButtonType.objects.get(id=data['button_id'])
                    total_price += button.initial_price
                except ButtonType.DoesNotExist:
                    return Response({
                        'error': 'Button not found',
                        'message': f"Button with ID {data['button_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add button strip price if provided
            if data.get('button_strip_id'):
                try:
                    button_strip = ButtonStripType.objects.get(id=data['button_strip_id'])
                    total_price += button_strip.initial_price
                except ButtonStripType.DoesNotExist:
                    return Response({
                        'error': 'Button strip not found',
                        'message': f"Button strip with ID {data['button_strip_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            # Add body price if provided
            if data.get('body_id'):
                try:
                    body = BodyType.objects.get(id=data['body_id'])
                    total_price += body.initial_price
                except BodyType.DoesNotExist:
                    return Response({
                        'error': 'Body not found',
                        'message': f"Body with ID {data['body_id']} does not exist"
                    }, status=HTTP_400_BAD_REQUEST)

            return Response({
                'total_price': str(total_price)
            }, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        except Exception as e:
            return Response({
                'error': 'Price calculation failed',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


#================== FIX ISSUE 4: DESIGN SUMMARY PREVIEW API ====================================================
class DesignSummaryPreviewAPIView(APIView):
    """
    Preview complete design summary with all selections and total price.
    This endpoint shows the summary before user saves the design.
    """
    def post(self, request, format=None):
        try:
            data = request.data

            # Fetch all selected components
            category = HomePageSelectionCategory.objects.get(id=data['category_id'])
            fabric_color = FabricColor.objects.get(id=data['fabric_color_id'])
            collar = GholaType.objects.get(id=data['collar_id'])
            sleeve_left = SleevesType.objects.get(id=data['sleeve_left_id'])
            sleeve_right = SleevesType.objects.get(id=data['sleeve_right_id'])
            pocket = PocketType.objects.get(id=data['pocket_id'])
            button = ButtonType.objects.get(id=data['button_id'])
            button_strip = ButtonStripType.objects.get(id=data['button_strip_id'])

            # Calculate total price
            total_price = (
                category.initial_price +
                fabric_color.total_price +
                collar.initial_price +
                sleeve_left.initial_price +
                sleeve_right.initial_price +
                pocket.initial_price +
                button.initial_price +
                button_strip.initial_price
            )

            # Build comprehensive summary
            summary = {
                'category': {
                    'id': category.id,
                    'name_eng': category.main_category_name_eng,
                    'name_arb': category.main_category_name_arb,
                    'price': str(category.initial_price),
                    'image': category.cover.url if category.cover else None,
                    'delivery_period': category.duration_delivery_period
                },
                'fabric': {
                    'id': fabric_color.id,
                    'name_eng': fabric_color.color_name_eng,
                    'name_arb': fabric_color.color_name_arb,
                    'fabric_type': fabric_color.fabric_type.fabric_name_eng,
                    'price': str(fabric_color.total_price),
                    'image': fabric_color.cover.url if fabric_color.cover else None
                },
                'collar': {
                    'id': collar.id,
                    'name_eng': collar.ghola_type_name_eng,
                    'name_arb': collar.ghola_type_name_arb,
                    'color': collar.color,
                    'price': str(collar.initial_price),
                    'image': collar.cover.url if collar.cover else None
                },
                'sleeve_left': {
                    'id': sleeve_left.id,
                    'name_eng': sleeve_left.sleeves_type_name_eng,
                    'name_arb': sleeve_left.sleeves_type_name_arb,
                    'color': sleeve_left.color,
                    'price': str(sleeve_left.initial_price),
                    'image': sleeve_left.cover.url if sleeve_left.cover else None
                },
                'sleeve_right': {
                    'id': sleeve_right.id,
                    'name_eng': sleeve_right.sleeves_type_name_eng,
                    'name_arb': sleeve_right.sleeves_type_name_arb,
                    'color': sleeve_right.color,
                    'price': str(sleeve_right.initial_price),
                    'image': sleeve_right.cover.url if sleeve_right.cover else None
                },
                'pocket': {
                    'id': pocket.id,
                    'name_eng': pocket.pocket_type_name_eng,
                    'name_arb': pocket.pocket_type_name_arb,
                    'color': pocket.color,
                    'price': str(pocket.initial_price),
                    'image': pocket.cover.url if pocket.cover else None
                },
                'button': {
                    'id': button.id,
                    'name_eng': button.button_type_name_eng,
                    'name_arb': button.button_type_name_arb,
                    'color': button.color,
                    'price': str(button.initial_price),
                    'image': button.cover.url if button.cover else None
                },
                'button_strip': {
                    'id': button_strip.id,
                    'name_eng': button_strip.button_strip_type_name_eng,
                    'name_arb': button_strip.button_strip_type_name_arb,
                    'color': button_strip.color,
                    'price': str(button_strip.initial_price),
                    'image': button_strip.cover.url if button_strip.cover else None
                },
                'pricing': {
                    'category_price': str(category.initial_price),
                    'fabric_price': str(fabric.initial_price),
                    'collar_price': str(collar.initial_price),
                    'sleeve_left_price': str(sleeve_left.initial_price),
                    'sleeve_right_price': str(sleeve_right.initial_price),
                    'pocket_price': str(pocket.initial_price),
                    'button_price': str(button.initial_price),
                    'button_strip_price': str(button_strip.initial_price),
                    'total_price': str(total_price)
                },
                'estimated_delivery': category.duration_delivery_period
            }

            return Response(summary, status=HTTP_200_OK, content_type='application/json; charset=utf-8')

        except HomePageSelectionCategory.DoesNotExist:
            return Response({'error': 'Category not found'}, status=HTTP_400_BAD_REQUEST)
        except FabricColor.DoesNotExist:
            return Response({'error': 'Fabric color not found'}, status=HTTP_400_BAD_REQUEST)
        except GholaType.DoesNotExist:
            return Response({'error': 'Collar not found'}, status=HTTP_400_BAD_REQUEST)
        except SleevesType.DoesNotExist:
            return Response({'error': 'Sleeve not found'}, status=HTTP_400_BAD_REQUEST)
        except PocketType.DoesNotExist:
            return Response({'error': 'Pocket not found'}, status=HTTP_400_BAD_REQUEST)
        except ButtonType.DoesNotExist:
            return Response({'error': 'Button not found'}, status=HTTP_400_BAD_REQUEST)
        except ButtonStripType.DoesNotExist:
            return Response({'error': 'Button strip not found'}, status=HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=HTTP_400_BAD_REQUEST)


#================== INVENTORY MANAGEMENT (ADMIN SIDE) ====================================================

class LowStockAlertAPIView(APIView):
    """
    GET: Get list of fabric colors with low stock (quantity <= threshold)
    Endpoint: /design/inventory/low-stock/
    Query params: ?threshold=5 (default: 10)
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            threshold = int(request.GET.get('threshold', 10))

            low_stock_fabrics = FabricColor.objects.filter(
                quantity__lte=threshold
            ).select_related('fabric_type').order_by('quantity')

            data = []
            for fabric in low_stock_fabrics:
                data.append({
                    'id': fabric.id,
                    'fabric_type_name': fabric.fabric_type.fabric_name_eng,
                    'color_name': fabric.color_name_eng,
                    'current_quantity': fabric.quantity,
                    'inStock': fabric.inStock,
                    'cover': fabric.cover.url if fabric.cover else None
                })

            return Response({
                'threshold': threshold,
                'low_stock_count': len(data),
                'fabrics': data
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch low stock items',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class BulkUpdateInventoryAPIView(APIView):
    """
    PUT: Bulk update inventory quantities for multiple fabric colors
    Endpoint: /design/inventory/bulk-update/
    Body: {
        "updates": [
            {"fabric_color_id": 1, "quantity": 50, "notes": "Restocked"},
            {"fabric_color_id": 2, "quantity": 30}
        ]
    }
    """
    permission_classes = [IsAdminUser]

    @transaction.atomic
    def put(self, request):
        try:
            updates = request.data.get('updates', [])

            if not updates:
                return Response({
                    'error': 'No updates provided',
                    'message': 'Please provide updates array'
                }, status=HTTP_400_BAD_REQUEST)

            updated_fabrics = []
            errors = []

            for update in updates:
                fabric_color_id = update.get('fabric_color_id')
                new_quantity = update.get('quantity')
                notes = update.get('notes', '')

                if not fabric_color_id or new_quantity is None:
                    errors.append({
                        'fabric_color_id': fabric_color_id,
                        'error': 'Missing fabric_color_id or quantity'
                    })
                    continue

                try:
                    fabric_color = FabricColor.objects.get(id=fabric_color_id)
                    quantity_before = fabric_color.quantity
                    quantity_change = new_quantity - quantity_before

                    fabric_color.quantity = new_quantity
                    fabric_color.inStock = new_quantity > 0
                    fabric_color.save()

                    # Log transaction
                    InventoryTransaction.objects.create(
                        fabric_color=fabric_color,
                        transaction_type='RESTOCK' if quantity_change > 0 else 'ADJUSTMENT',
                        quantity_change=quantity_change,
                        quantity_before=quantity_before,
                        quantity_after=new_quantity,
                        notes=notes or f"Bulk update by admin",
                        created_by=request.user
                    )

                    updated_fabrics.append({
                        'id': fabric_color.id,
                        'name': fabric_color.color_name_eng,
                        'quantity_before': quantity_before,
                        'quantity_after': new_quantity,
                        'change': quantity_change
                    })

                except FabricColor.DoesNotExist:
                    errors.append({
                        'fabric_color_id': fabric_color_id,
                        'error': 'Fabric color not found'
                    })

            return Response({
                'message': f'Successfully updated {len(updated_fabrics)} fabric colors',
                'updated': updated_fabrics,
                'errors': errors
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Bulk update failed',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class InventoryHistoryAPIView(APIView):
    """
    GET: Get inventory transaction history for a specific fabric color
    Endpoint: /design/inventory/history/<fabric_color_id>/
    Query params: ?limit=50 (default: 100)
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            limit = int(request.GET.get('limit', 100))

            try:
                fabric_color = FabricColor.objects.get(id=pk)
            except FabricColor.DoesNotExist:
                return Response({
                    'error': 'Fabric color not found'
                }, status=HTTP_400_BAD_REQUEST)

            transactions = InventoryTransaction.objects.filter(
                fabric_color=fabric_color
            ).select_related('created_by')[:limit]

            data = []
            for transaction in transactions:
                data.append({
                    'id': transaction.id,
                    'transaction_type': transaction.transaction_type,
                    'quantity_change': transaction.quantity_change,
                    'quantity_before': transaction.quantity_before,
                    'quantity_after': transaction.quantity_after,
                    'reference_order': transaction.reference_order,
                    'notes': transaction.notes,
                    'created_by': transaction.created_by.username if transaction.created_by else 'System',
                    'timestamp': transaction.timestamp
                })

            return Response({
                'fabric_color': {
                    'id': fabric_color.id,
                    'name': fabric_color.color_name_eng,
                    'current_quantity': fabric_color.quantity
                },
                'transactions': data,
                'count': len(data)
            }, status=HTTP_200_OK)

        except Exception as e:
            return Response({
                'error': 'Failed to fetch inventory history',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


class UploadDesignScreenshotAPIView(APIView):
    """
    Upload design screenshot to Cloudinary with duplicate detection
    Receives base64 image and design component IDs from Flutter app
    If same design configuration exists, returns existing screenshot URL instead of uploading
    """
    def post(self, request):
        import base64
        import hashlib
        import cloudinary.uploader
        from io import BytesIO
        from .models import DesignScreenshot

        try:
            # Get design component IDs (all optional)
            fabric_color_id = request.data.get('fabric_color_id')
            collar_id = request.data.get('collar_id')
            sleeve_left_id = request.data.get('sleeve_left_id')
            sleeve_right_id = request.data.get('sleeve_right_id')
            pocket_id = request.data.get('pocket_id')
            button_id = request.data.get('button_id')
            button_strip_id = request.data.get('button_strip_id')
            body_id = request.data.get('body_id')

            # Create hash from component IDs to identify unique design configurations
            # Use sorted list to ensure consistent hash for same components
            component_ids = [
                str(fabric_color_id) if fabric_color_id else 'none',
                str(collar_id) if collar_id else 'none',
                str(sleeve_left_id) if sleeve_left_id else 'none',
                str(sleeve_right_id) if sleeve_right_id else 'none',
                str(pocket_id) if pocket_id else 'none',
                str(button_id) if button_id else 'none',
                str(button_strip_id) if button_strip_id else 'none',
                str(body_id) if body_id else 'none',
            ]

            # Create MD5 hash of component IDs
            design_hash = hashlib.md5('|'.join(component_ids).encode()).hexdigest()

            # Check if screenshot for this exact design configuration already exists
            try:
                existing_screenshot = DesignScreenshot.objects.get(design_hash=design_hash)

                # Increment reuse counter
                existing_screenshot.times_reused += 1
                existing_screenshot.save()

                # Return existing screenshot URL without uploading
                return Response({
                    'success': True,
                    'url': existing_screenshot.screenshot_url,
                    'public_id': existing_screenshot.cloudinary_public_id,
                    'reused': True,
                    'message': 'Existing screenshot returned for identical design'
                }, status=HTTP_200_OK)

            except DesignScreenshot.DoesNotExist:
                # No existing screenshot - proceed with upload
                pass

            # Get base64 image data from request
            image_data = request.data.get('image')
            if not image_data:
                return Response({
                    'error': 'No image data provided'
                }, status=HTTP_400_BAD_REQUEST)

            # Decode base64 image
            try:
                # Remove data URL prefix if present (data:image/png;base64,...)
                if ',' in image_data:
                    image_data = image_data.split(',')[1]

                image_bytes = base64.b64decode(image_data)
            except Exception as e:
                return Response({
                    'error': 'Invalid image data',
                    'message': str(e)
                }, status=HTTP_400_BAD_REQUEST)

            # Upload to Cloudinary
            try:
                result = cloudinary.uploader.upload(
                    image_bytes,
                    folder='user_designs',
                    resource_type='image'
                )

                # Save screenshot information to database for future reuse
                DesignScreenshot.objects.create(
                    design_hash=design_hash,
                    screenshot_url=result['secure_url'],
                    cloudinary_public_id=result['public_id'],
                    fabric_color_id=fabric_color_id,
                    collar_id=collar_id,
                    sleeve_left_id=sleeve_left_id,
                    sleeve_right_id=sleeve_right_id,
                    pocket_id=pocket_id,
                    button_id=button_id,
                    button_strip_id=button_strip_id,
                    body_id=body_id,
                    times_reused=0
                )

                return Response({
                    'success': True,
                    'url': result['secure_url'],
                    'public_id': result['public_id'],
                    'reused': False,
                    'message': 'New screenshot uploaded and saved'
                }, status=HTTP_200_OK)

            except Exception as e:
                return Response({
                    'error': 'Failed to upload to Cloudinary',
                    'message': str(e)
                }, status=HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': 'Upload failed',
                'message': str(e)
            }, status=HTTP_400_BAD_REQUEST)


def all_design_view(request):
    return render(request, 'Design/all_design.html')