import requests
import time
import random
import string
from decimal import Decimal
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class PayzahService:
    """
    Payzah Payment Gateway Service for Kuwait
    Handles payment initialization, verification, and status checking
    Supports K-Net, Credit Card, and Apple Pay through unified transit page
    """

    def __init__(self):
        """Initialize Payzah service with configuration from Django settings"""
        self.base_url = getattr(settings, 'PAYZAH_BASE_URL', 'https://api.payzah.com')
        self.private_key = getattr(settings, 'PAYZAH_PRIVATE_KEY', '')
        self.currency = getattr(settings, 'PAYZAH_CURRENCY', 'KWD')
        self.language = getattr(settings, 'PAYZAH_LANGUAGE', 'en')

        # Authorization header (Base64 encoded private key)
        self.auth_header = self.private_key

    def generate_track_id(self):
        """
        Generate unique track ID for payment transaction
        Format: RAGY-{timestamp}-{random_string}

        Returns:
            str: Unique track ID
        """
        timestamp = int(time.time() * 1000)
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"RAGY-{timestamp}-{random_str}"

    def initiate_payment(self, payment_data):
        """
        Initialize payment with Payzah gateway
        Creates payment session and returns redirect URL for customer

        Args:
            payment_data (dict): Payment information containing:
                - amount (Decimal): Payment amount in KWD
                - success_url (str): URL to redirect after successful payment
                - error_url (str): URL to redirect after failed payment
                - track_id (str, optional): Unique track ID (generated if not provided)
                - user_name (str, optional): Customer name
                - user_email (str, optional): Customer email
                - invoice_number (str, optional): Order invoice number
                - order_details (str, optional): Order description

        Returns:
            dict: Response containing:
                - success (bool): Whether initialization succeeded
                - track_id (str): Unique track ID for this payment
                - payment_id (str): Payzah payment ID
                - redirect_url (str): URL to redirect customer for payment
                - is_transit (bool): Whether using transit (unified) page
                - error (str, optional): Error message if failed
        """
        try:
            amount = payment_data.get('amount')
            success_url = payment_data.get('success_url')
            error_url = payment_data.get('error_url')
            track_id = payment_data.get('track_id') or self.generate_track_id()

            # Format amount to 3 decimal places for KWD
            if isinstance(amount, (int, float, Decimal)):
                formatted_amount = f"{float(amount):.3f}"
            else:
                formatted_amount = str(amount)

            # Build request payload for Payzah
            request_payload = {
                'trackid': track_id,
                'amount': formatted_amount,
                'success_url': success_url,
                'error_url': error_url,
                'language': self.language,
                'currency': self.currency,
                'payment_type': '3',  # REQUIRED: "3" for transit_url (unified payment page)
                                      # Transit page shows: K-Net, Credit Card, Apple Pay
                'udf1': payment_data.get('invoice_number', ''),
                'udf2': payment_data.get('user_name', ''),
                'udf3': payment_data.get('user_email', ''),
                'udf5': payment_data.get('order_details', f'Raggey Order - {track_id}'),
                'customer_name': payment_data.get('user_name', ''),
                'customer_email': payment_data.get('user_email', ''),
            }

            logger.info(f"Payzah Payment Initialization Request: {request_payload}")

            # Make API call to Payzah
            response = requests.post(
                f"{self.base_url}/ws/paymentgateway/index",
                json=request_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': self.auth_header,
                },
                timeout=30
            )

            response_data = response.json()
            logger.info(f"Payzah Payment Initialization Response: {response_data}")

            if response_data.get('status') is True:
                # Always use transit_url for unified payment page
                transit_url = response_data.get('data', {}).get('transit_url')

                if not transit_url:
                    raise Exception("Transit URL not provided by Payzah. Please contact support.")

                logger.info("✅ Payment initialized successfully - Redirecting to Transit Page")

                return {
                    'success': True,
                    'track_id': track_id,
                    'payment_id': response_data.get('data', {}).get('PaymentID'),
                    'redirect_url': transit_url,
                    'payment_url': response_data.get('data', {}).get('PaymentUrl'),
                    'is_transit': True,
                }
            else:
                error_msg = response_data.get('message', 'Payment initialization failed')
                logger.error(f"Payzah initialization failed: {error_msg}")
                raise Exception(error_msg)

        except requests.exceptions.RequestException as e:
            logger.error(f"Payzah Payment Error: {str(e)}")

            error_message = "Payment initialization failed"
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_message = f"{error_data.get('message', error_message)} (Code: {error_data.get('code', 'UNKNOWN')})"
                except:
                    pass
            elif 'Connection' in str(e):
                error_message = "Cannot connect to payment gateway. Please try again."
            elif 'Timeout' in str(e):
                error_message = "Payment gateway timeout. Please try again."

            return {
                'success': False,
                'error': error_message,
                'code': 'PAYMENT_INIT_ERROR'
            }

        except Exception as e:
            logger.error(f"Payzah Payment Exception: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'UNKNOWN_ERROR'
            }

    def verify_payment(self, track_id, payment_id=None):
        """
        Verify payment status with Payzah gateway
        Used to confirm payment after customer redirect

        Args:
            track_id (str): Unique track ID for the payment
            payment_id (str, optional): Payzah payment ID

        Returns:
            dict: Verification result containing:
                - success (bool): Whether verification succeeded
                - verified (bool): Whether payment is verified
                - payment_status (str): Payment status from Payzah
                - payzah_reference_code (str): Payzah reference code
                - knet_payment_id (str): K-Net payment ID
                - transaction_number (str): Transaction number
                - payment_date (str): Payment date
                - track_id (str): Track ID
                - udf1-udf5 (str): User defined fields
                - error (str, optional): Error message if failed
        """
        try:
            request_payload = {
                'trackid': track_id,
            }

            # Add payment_id if provided
            if payment_id:
                request_payload['payment_id'] = payment_id

            logger.info(f"Payzah Payment Verification Request: {request_payload}")

            response = requests.post(
                f"{self.base_url}/ws/paymentgateway/get-payment-details",
                json=request_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': self.auth_header,
                },
                timeout=15
            )

            response_data = response.json()
            logger.info(f"Payzah Payment Verification Response: {response_data}")

            if response_data.get('status') is True:
                data = response_data.get('data', {})
                return {
                    'success': True,
                    'verified': True,
                    'payment_status': data.get('paymentStatus'),
                    'payzah_reference_code': data.get('payzahRefrenceCode'),
                    'knet_payment_id': data.get('knetPaymentId'),
                    'transaction_number': data.get('transactionNumber'),
                    'payment_date': data.get('paymentDate'),
                    'track_id': data.get('trackId'),
                    'udf1': data.get('UDF1'),
                    'udf2': data.get('UDF2'),
                    'udf3': data.get('UDF3'),
                    'udf4': data.get('UDF4'),
                    'udf5': data.get('UDF5'),
                }
            else:
                error_msg = response_data.get('message', 'Payment verification failed')
                logger.error(f"Payzah verification failed: {error_msg}")
                return {
                    'success': False,
                    'verified': False,
                    'error': error_msg
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Payzah Verification Error: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': 'Failed to verify payment'
            }

        except Exception as e:
            logger.error(f"Payzah Verification Exception: {str(e)}")
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }

    def check_payment_status(self, track_id, payment_id):
        """
        Check payment status with Payzah gateway
        Similar to verify_payment but requires payment_id

        Args:
            track_id (str): Unique track ID for the payment
            payment_id (str): Payzah payment ID

        Returns:
            dict: Status check result (same format as verify_payment)
        """
        try:
            request_payload = {
                'trackid': track_id,
                'payment_id': payment_id,
            }

            logger.info(f"Payzah Payment Status Check Request: {request_payload}")

            response = requests.post(
                f"{self.base_url}/ws/paymentgateway/get-payment-details",
                json=request_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': self.auth_header,
                },
                timeout=15
            )

            response_data = response.json()
            logger.info(f"Payzah Payment Status Check Response: {response_data}")

            if response_data.get('status') is True:
                data = response_data.get('data', {})
                return {
                    'success': True,
                    'payment_status': data.get('paymentStatus'),
                    'payzah_reference_code': data.get('payzahRefrenceCode'),
                    'knet_payment_id': data.get('knetPaymentId'),
                    'transaction_number': data.get('transactionNumber'),
                    'payment_date': data.get('paymentDate'),
                    'track_id': data.get('trackId'),
                    'udf1': data.get('UDF1'),
                    'udf2': data.get('UDF2'),
                    'udf3': data.get('UDF3'),
                    'udf4': data.get('UDF4'),
                    'udf5': data.get('UDF5'),
                }
            else:
                error_msg = response_data.get('message', 'Payment status check failed')
                logger.error(f"Payzah status check failed: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'code': response_data.get('code')
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"Payzah Status Check Error: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to check payment status',
                'code': 'STATUS_CHECK_ERROR'
            }

        except Exception as e:
            logger.error(f"Payzah Status Check Exception: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'UNKNOWN_ERROR'
            }

    def map_payment_status(self, payzah_status):
        """
        Map Payzah payment status to internal system status

        Args:
            payzah_status (str): Status from Payzah (e.g., 'CAPTURED', 'VOIDED')

        Returns:
            str: Internal status ('captured', 'failed', 'pending')
        """
        status_map = {
            'CAPTURED': 'captured',
            'VOIDED': 'failed',
            'NOT CAPTURED': 'failed',
            'CANCELED': 'failed',
            'DENIED BY RISK': 'failed',
            'HOST TIMEOUT': 'failed',
        }

        return status_map.get(payzah_status, 'pending')


# Singleton instance
payzah_service = PayzahService()
