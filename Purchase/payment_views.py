"""
Payment Views for Payzah Payment Gateway Integration
Handles payment initialization, callback processing, and verification
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import redirect
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging
import uuid

from .models import Payment, Purchase
from .serializers import (
    PaymentInitiateSerializer,
    PaymentCallbackSerializer,
    PaymentVerifySerializer,
    PaymentSerializer,
    PaymentStatusSerializer
)
from .services.payzahService import payzah_service
from .notification_utils import send_payment_success_notification, send_payment_failed_notification

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class InitiatePaymentAPIView(APIView):
    """
    POST /api/payment/initiate/
    Initiate payment with Payzah gateway
    Creates payment record and returns redirect URL

    Request Body:
    {
        "purchase_id": 123,
        "success_url": "https://app.raggey.com/payment/success",
        "error_url": "https://app.raggey.com/payment/error"
    }

    Response:
    {
        "success": true,
        "redirect_url": "https://payzah.com/transit/...",
        "track_id": "RAGY-1234567890-ABC123",
        "payment_id": "PAY_123456"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Validate request data
            serializer = PaymentInitiateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'Invalid request data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            purchase_id = serializer.validated_data['purchase_id']
            success_url = serializer.validated_data['success_url']
            error_url = serializer.validated_data['error_url']

            # Get purchase
            try:
                purchase = Purchase.objects.get(id=purchase_id, user=request.user)
            except Purchase.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Purchase not found or unauthorized'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if purchase already has a captured payment
            if hasattr(purchase, 'payment') and purchase.payment:
                if purchase.payment.status == 'captured':
                    return Response({
                        'success': False,
                        'error': 'Payment already completed for this purchase'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Generate idempotency key
            idempotency_key = str(uuid.uuid4())

            # Generate track ID
            track_id = payzah_service.generate_track_id()

            # Prepare payment data for Payzah
            payment_data = {
                'amount': purchase.total_price,
                'success_url': success_url,
                'error_url': error_url,
                'track_id': track_id,
                'user_name': purchase.full_name,
                'user_email': purchase.email or request.user.email,
                'invoice_number': purchase.invoice_number,
                'order_details': f'Raggey Order - {purchase.invoice_number}'
            }

            # Call Payzah service to initiate payment
            payzah_response = payzah_service.initiate_payment(payment_data)

            if not payzah_response.get('success'):
                logger.error(f"Payzah payment initiation failed: {payzah_response.get('error')}")
                return Response({
                    'success': False,
                    'error': payzah_response.get('error', 'Failed to initiate payment')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Create payment record in database
            with transaction.atomic():
                # Delete existing pending payment if exists
                if hasattr(purchase, 'payment') and purchase.payment:
                    if purchase.payment.status == 'pending':
                        purchase.payment.delete()

                payment = Payment.objects.create(
                    user=request.user,
                    purchase=purchase,
                    amount=purchase.total_price,
                    currency='KWD',
                    track_id=track_id,
                    payzah_payment_id=payzah_response.get('payment_id', ''),
                    status='pending',
                    redirect_url=payzah_response.get('redirect_url'),
                    success_url=success_url,
                    error_url=error_url,
                    idempotency_key=idempotency_key,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    ip_address=get_client_ip(request),
                    # Store order details in UDF fields
                    udf1=purchase.invoice_number,
                    udf2=purchase.full_name,
                    udf3=purchase.email or request.user.email,
                    udf5=f'Raggey Order - {purchase.invoice_number}'
                )

                logger.info(f"Payment initiated successfully: {track_id}")

            return Response({
                'success': True,
                'redirect_url': payzah_response.get('redirect_url'),
                'track_id': track_id,
                'payment_id': payzah_response.get('payment_id'),
                'is_transit': payzah_response.get('is_transit', True)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while initiating payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentCallbackAPIView(APIView):
    """
    GET /api/payment/callback/
    Handle payment callback from Payzah
    Verifies payment and updates order status

    Query Parameters (from Payzah):
    - trackid: Payment track ID
    - payment_id: Payzah payment ID
    - paymentStatus: Payment status
    - payzahRefrenceCode: Payzah reference code
    - knetPaymentId: K-Net payment ID
    - transactionNumber: Transaction number
    - paymentDate: Payment date
    - UDF1-UDF5: User defined fields
    """
    permission_classes = [AllowAny]  # Callback from Payzah doesn't have auth

    def get(self, request):
        try:
            # Log callback data
            logger.info(f"Payment callback received: {request.GET.dict()}")

            # Extract track ID
            track_id = request.GET.get('trackid')
            if not track_id:
                logger.error("Payment callback missing track ID")
                # Redirect to error URL if available
                return redirect(f"{settings.FRONTEND_URL}/payment/error?error=missing_track_id")

            # Get payment record
            try:
                payment = Payment.objects.select_related('purchase', 'user').get(track_id=track_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for track ID: {track_id}")
                return redirect(f"{settings.FRONTEND_URL}/payment/error?error=payment_not_found")

            # Verify payment with Payzah API
            verification = payzah_service.verify_payment(
                track_id=track_id,
                payment_id=request.GET.get('payment_id')
            )

            if not verification.get('success') or not verification.get('verified'):
                logger.error(f"Payment verification failed: {verification.get('error')}")
                payment.status = 'failed'
                payment.payment_status_raw = request.GET.get('paymentStatus', '')
                payment.save()

                return redirect(f"{payment.error_url}?track_id={track_id}&error=verification_failed")

            # Payment verified successfully
            payzah_status = verification.get('payment_status')
            internal_status = payzah_service.map_payment_status(payzah_status)

            # Update payment record
            with transaction.atomic():
                payment.status = internal_status
                payment.verified_with_gateway = True
                payment.gateway_verification_attempts += 1
                payment.payzah_reference_code = verification.get('payzah_reference_code')
                payment.knet_payment_id = verification.get('knet_payment_id')
                payment.transaction_number = verification.get('transaction_number')
                payment.payment_date = verification.get('payment_date')
                payment.payment_status_raw = payzah_status

                if internal_status == 'captured':
                    payment.completed_at = timezone.now()
                    # Update purchase status to Processing
                    if payment.purchase:
                        payment.purchase.status = 'Processing'
                        payment.purchase.save()
                        logger.info(f"Purchase {payment.purchase.invoice_number} marked as Processing")

                        # Send payment success notification
                        try:
                            user_profile = getattr(payment.purchase.user, 'profile', None)
                            if user_profile and user_profile.fcm_token:
                                send_payment_success_notification(
                                    user_fcm_token=user_profile.fcm_token,
                                    order=payment.purchase
                                )
                                logger.info(f"🔔 Payment success notification sent to user {payment.purchase.user.id}")
                            else:
                                logger.warning(f"⚠️ No FCM token found for user {payment.purchase.user.id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Could not send payment success notification: {e}")

                payment.save()
                logger.info(f"Payment {track_id} status updated to {internal_status}")

            # Redirect based on payment status
            if internal_status == 'captured':
                return redirect(f"{payment.success_url}?track_id={track_id}&status=success")
            else:
                # Send payment failed notification
                if payment.purchase:
                    try:
                        user_profile = getattr(payment.purchase.user, 'profile', None)
                        if user_profile and user_profile.fcm_token:
                            send_payment_failed_notification(
                                user_fcm_token=user_profile.fcm_token,
                                order=payment.purchase,
                                error_message=f"Payment status: {internal_status}"
                            )
                            logger.info(f"🔔 Payment failed notification sent to user {payment.purchase.user.id}")
                        else:
                            logger.warning(f"⚠️ No FCM token found for user {payment.purchase.user.id}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not send payment failed notification: {e}")

                return redirect(f"{payment.error_url}?track_id={track_id}&status={internal_status}")

        except Exception as e:
            logger.error(f"Payment callback error: {str(e)}", exc_info=True)
            return redirect(f"{settings.FRONTEND_URL}/payment/error?error=system_error")

    def post(self, request):
        """Handle POST callback (some gateways send POST)"""
        return self.get(request)


class VerifyPaymentAPIView(APIView):
    """
    POST /api/payment/verify/
    Manually verify payment status with Payzah API
    Used by frontend to check payment status

    Request Body:
    {
        "track_id": "RAGY-1234567890-ABC123",
        "payment_id": "PAY_123456"  // optional
    }

    Response:
    {
        "success": true,
        "payment": {
            "track_id": "RAGY-1234567890-ABC123",
            "status": "captured",
            "amount": "45.000",
            "verified_with_gateway": true
        }
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # Validate request data
            serializer = PaymentVerifySerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'Invalid request data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

            track_id = serializer.validated_data['track_id']
            payment_id = serializer.validated_data.get('payment_id')

            # Get payment record
            try:
                payment = Payment.objects.select_related('purchase').get(
                    track_id=track_id,
                    user=request.user
                )
            except Payment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Payment not found or unauthorized'
                }, status=status.HTTP_404_NOT_FOUND)

            # If payment already captured, return current status
            if payment.status == 'captured' and payment.verified_with_gateway:
                return Response({
                    'success': True,
                    'message': 'Payment already verified',
                    'payment': PaymentStatusSerializer(payment).data
                }, status=status.HTTP_200_OK)

            # Verify with Payzah API
            verification = payzah_service.verify_payment(
                track_id=track_id,
                payment_id=payment_id or payment.payzah_payment_id
            )

            if not verification.get('success'):
                logger.error(f"Payment verification API failed: {verification.get('error')}")
                return Response({
                    'success': False,
                    'error': verification.get('error', 'Verification failed')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Update payment with verification result
            payzah_status = verification.get('payment_status')
            internal_status = payzah_service.map_payment_status(payzah_status)

            with transaction.atomic():
                payment.status = internal_status
                payment.verified_with_gateway = True
                payment.gateway_verification_attempts += 1
                payment.payzah_reference_code = verification.get('payzah_reference_code')
                payment.knet_payment_id = verification.get('knet_payment_id')
                payment.transaction_number = verification.get('transaction_number')
                payment.payment_date = verification.get('payment_date')
                payment.payment_status_raw = payzah_status

                if internal_status == 'captured' and not payment.completed_at:
                    payment.completed_at = timezone.now()
                    # Update purchase status
                    if payment.purchase:
                        payment.purchase.status = 'Processing'
                        payment.purchase.save()

                payment.save()

            logger.info(f"Payment {track_id} verified: {internal_status}")

            return Response({
                'success': True,
                'verified': verification.get('verified'),
                'payment': PaymentStatusSerializer(payment).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while verifying payment'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentStatusAPIView(APIView):
    """
    GET /api/payment/status/{track_id}/
    Get payment status by track ID

    Response:
    {
        "success": true,
        "payment": {
            "track_id": "RAGY-1234567890-ABC123",
            "status": "captured",
            "amount": "45.000",
            "verified_with_gateway": true
        }
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, track_id):
        try:
            # Get payment record
            try:
                payment = Payment.objects.select_related('purchase').get(
                    track_id=track_id,
                    user=request.user
                )
            except Payment.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Payment not found or unauthorized'
                }, status=status.HTTP_404_NOT_FOUND)

            return Response({
                'success': True,
                'payment': PaymentSerializer(payment).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Payment status retrieval error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while retrieving payment status'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserPaymentsListAPIView(APIView):
    """
    GET /api/payment/my-payments/
    Get all payments for authenticated user

    Response:
    {
        "success": true,
        "payments": [...]
    }
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            payments = Payment.objects.filter(user=request.user).select_related('purchase').order_by('-created_at')

            return Response({
                'success': True,
                'payments': PaymentSerializer(payments, many=True).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Payment list retrieval error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': 'An error occurred while retrieving payments'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
