from django.shortcuts import render
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from .serializers import SizesSerializer
from django.contrib.auth.models import User
from .models import Sizes

# ===========  ONLY FOR AUTHENTICATED USER ==========

class FetchSizesAPIView(APIView):
    # Fetch Size Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            queryset = Sizes.objects.filter(user=user).order_by("-timestamp")
            serializer = SizesSerializer(
                queryset, context={'request': request},  many=True)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)


class SizesDetailAPIView(APIView):
    # Fetch Size Detail
    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            queryset = Sizes.objects.get(id=pk)
            serializer = SizesSerializer(
                queryset, context={'request': request},  many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Delete a Size 
    def delete(self, request, pk):
        user = self.request.user
        if user.is_authenticated:
            deleted_size = Sizes.objects.get(id=pk)
            if deleted_size:
                deleted_size.delete()
                return Response('deleted', status=HTTP_200_OK)
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    
    # Create a Size 
    def post(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            data = request.data
            size = Sizes.objects.create(
                user = user,
                size_name=data['size_name'],
                front_hight=data['front_hight'],
                back_hight=data['back_hight'],
                around_neck=data['around_neck'],
                around_legs =  data['around_legs'] ,
                full_chest=data['full_chest'],
                half_chest = data['half_chest'] ,
                full_belly=data['full_belly'],
                half_belly=data['half_belly'],
                neck_to_center_belly=data['neck_to_center_belly'],
                neck_to_chest=data['neck_to_chest'],
                shoulders_width =  data['shoulders_width'] ,
                arm_tall=data['arm_tall'],
                arm_width_one = data['arm_width_one'] ,
                arm_width_two =  data['arm_width_two'] ,
                arm_width_three=data['arm_width_three'],
                arm_width_four = data['arm_width_four'] )
            serializer = SizesSerializer(
                size, context={'request': request})
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Update a Size 
    def put(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated:
            data = request.data
            size = Sizes.objects.get(id=pk)
            if size:
                size.size_name = data['size_name']
                size.front_hight = data['front_hight']
                size.back_hight = data["back_hight"]
                size.around_neck = data["around_neck"]
                size.around_legs = data['around_legs']  
                size.full_chest=data['full_chest'] 
                size.half_chest = data['half_chest'] 
                size.full_belly = data['full_belly']
                size.half_belly = data['half_belly']
                size.neck_to_center_belly = data["neck_to_center_belly"]
                size.neck_to_chest = data["neck_to_chest"]
                size.shoulders_width = data['shoulders_width']  
                size.arm_tall=data['arm_tall'] 
                size.arm_width_one = data['arm_width_one'] 
                size.arm_width_two = data["arm_width_two"]
                size.arm_width_three = data["arm_width_three"]
                size.arm_width_four = data['arm_width_four']  
                size.save()
                serializer = SizesSerializer(
                    size, context={'request': request})
                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

