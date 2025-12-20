from django.shortcuts import render
from .models import Fee, Area
from .serializers import FeeSerializer, AreaSerializer
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from rest_framework.views import APIView
from django.db.models import Q
from django.db import transaction


class FeeABIVIew(APIView):
    # Create Fee
    def post(self, request, pk=None, format=None):
        user = self.request.user
        data = self.request.data
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
           if type(data['area']) == list:
                areas = Area.objects.filter(
                    id__in=data['area'])
                # Create a list of Fee objects to be bulk created
                fees_to_create = [
                    Fee(
                        area=area,
                        fee=data['fee'],
                        availble=data['availble']
                    )
                    for area in areas
                ]
                # Use the bulk_create method within a transaction to optimize the operation
                with transaction.atomic():
                    created_fees = Fee.objects.bulk_create(fees_to_create)
                serializer = FeeSerializer(
                    created_fees, context={'request': request}, many=True)

                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
           else:
                area = Area.objects.get(
                    area_name_eng=data['area'])

                fee = Fee.objects.create(
                    area=area,
                    fee=data['fee'],
                    availble=data['availble'])

                serializer = FeeSerializer(
                    fee, context={'request': request}, many=False)
                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Update Fee
    def put(self, request, pk=None, format=None):
        user = self.request.user
        data = self.request.data
        if user.is_authenticated and (user.profile.premission == "Admin" or user.profile.premission == "Partner" or user.profile.premission == "Data-Entry"):
            fee = Fee.objects.get(id=pk)
            area = Area.objects.get(area_name_eng=data['area'])
            if fee:
                fee.area = area
                fee.fee = data['fee']
                fee.availble = data['availble']
                fee.save()

                serializer = FeeSerializer(
                    fee, context={'request': request}, many=False)
                return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

    # Delete Fee
    def delete(self, request, pk=None, format=None):
        user = self.request.user

        if user.is_authenticated and user.profile.premission == "Admin" or user.profile.premission == "Data-Entry" or user.profile.premission == "Partner":
            fee = Fee.objects.get(id=pk)
            if fee:
                fee.delete()
                return Response("Deleted", status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
    # Fetch  Fee

    def get(self, request, pk=None, format=None):
        user = self.request.user
        if user.is_authenticated and user.profile.premission == "Admin" or user.profile.premission == "Data-Entry" or user.profile.premission == "Partner":
            fee = Fee.objects.get(id=pk)
            serializer = FeeSerializer(
                fee, context={'request': request},  many=False)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)

# List Fee


class FeeListAPIVIew(APIView):
    def get(self, request, pk=None, format=None):
        user = self.request.user
        name = self.request.query_params.get('name', None)
        if user.is_authenticated and user.profile.premission == "Admin" or user.profile.premission == "Data-Entry" or user.profile.premission == "Partner":
            fee = Fee.objects.filter(
                Q(area__area_name_eng__icontains=name) | Q(area__area_name_arb__icontains=name))
            serializer = FeeSerializer(
                fee, context={'request': request},  many=True)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)


class FeeListUserAPIVIew(APIView):
    def get(self, request, pk=None, format=None):
        name = self.request.query_params.get('name', None)
        user = self.request.user

        if user.is_authenticated: 
            if name is not None:
                fee = Fee.objects.filter((Q(area__area_name_eng__icontains=name) | Q(
                    area__area_name_arb__icontains=name)), availble=True)
            else:
                fee = Fee.objects.filter(availble=True)

            serializer = FeeSerializer(
                fee, context={'request': request},  many=True)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)


class FeeAreaAPIVIew(APIView):
    def get(self, request, pk=None, format=None):
        user = self.request.user
        name = self.request.query_params.get('name', None)

        if user.is_authenticated and user.profile.premission == "Admin" or user.profile.premission == "Data-Entry" or user.profile.premission == "Partner":
            area = Area.objects.filter(
                (Q(area_name_eng__icontains=name) | Q(area_name_arb__icontains=name)))
            serializer = AreaSerializer(
                area, context={'request': request},  many=True)
            return Response(serializer.data, status=HTTP_200_OK, content_type='application/json; charset=utf-8')
        return Response('Something went wrong', status=HTTP_400_BAD_REQUEST)
