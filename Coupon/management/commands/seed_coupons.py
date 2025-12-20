from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from Coupon.models import Coupon


class Command(BaseCommand):
    help = 'Seeds the database with sample coupons for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding coupons...')

        # Create Beta coupon code
        beta_coupon, created = Coupon.objects.get_or_create(
            code='BETA50',
            defaults={
                'name_en': 'Beta User Discount',
                'name_ar': 'خصم مستخدمي البيتا',
                'description_en': 'Special 50% discount for beta users',
                'description_ar': 'خصم خاص 50٪ لمستخدمي البيتا',
                'coupon_type': 'beta',
                'discount_type': 'percentage',
                'discount_value': 50,
                'max_uses': None,  # Unlimited
                'max_uses_per_user': 1,
                'min_order_amount': 0,
                'max_discount_amount': 20.000,  # Max 20 KWD discount
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=90),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created beta coupon: {beta_coupon.code}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Beta coupon already exists: {beta_coupon.code}'))

        # Create Card Promo 1 - Welcome Discount
        welcome_coupon, created = Coupon.objects.get_or_create(
            code='WELCOME10',
            defaults={
                'name_en': 'Welcome Discount',
                'name_ar': 'خصم الترحيب',
                'description_en': '10% off your first order',
                'description_ar': 'خصم 10٪ على طلبك الأول',
                'coupon_type': 'card',
                'discount_type': 'percentage',
                'discount_value': 10,
                'max_uses': None,
                'max_uses_per_user': 1,
                'min_order_amount': 20.000,
                'max_discount_amount': 5.000,
                'valid_from': timezone.now(),
                'valid_until': None,  # No expiry
                'is_active': True,
                'is_featured': True,
                'card_color': '#0B5D35',
                'card_icon': 'welcome',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created card coupon: {welcome_coupon.code}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Card coupon already exists: {welcome_coupon.code}'))

        # Create Card Promo 2 - Eid Special
        eid_coupon, created = Coupon.objects.get_or_create(
            code='EID2024',
            defaults={
                'name_en': 'Eid Special',
                'name_ar': 'عرض العيد',
                'description_en': '15 KWD off on orders above 50 KWD',
                'description_ar': 'خصم 15 د.ك على الطلبات فوق 50 د.ك',
                'coupon_type': 'card',
                'discount_type': 'fixed',
                'discount_value': 15.000,
                'max_uses': 100,
                'max_uses_per_user': 1,
                'min_order_amount': 50.000,
                'max_discount_amount': None,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=30),
                'is_active': True,
                'is_featured': True,
                'card_color': '#D4AF37',
                'card_icon': 'eid',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created card coupon: {eid_coupon.code}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Card coupon already exists: {eid_coupon.code}'))

        # Create Card Promo 3 - Free Delivery
        delivery_coupon, created = Coupon.objects.get_or_create(
            code='FREEDEL',
            defaults={
                'name_en': 'Free Delivery',
                'name_ar': 'توصيل مجاني',
                'description_en': '5 KWD off delivery charges',
                'description_ar': 'خصم 5 د.ك على رسوم التوصيل',
                'coupon_type': 'card',
                'discount_type': 'fixed',
                'discount_value': 5.000,
                'max_uses': None,
                'max_uses_per_user': 3,
                'min_order_amount': 30.000,
                'max_discount_amount': None,
                'valid_from': timezone.now(),
                'valid_until': None,
                'is_active': True,
                'is_featured': False,
                'card_color': '#4A90E2',
                'card_icon': 'delivery',
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created card coupon: {delivery_coupon.code}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Card coupon already exists: {delivery_coupon.code}'))

        # Create test general coupon
        summer_coupon, created = Coupon.objects.get_or_create(
            code='SUMMER25',
            defaults={
                'name_en': 'Summer Sale',
                'name_ar': 'تخفيضات الصيف',
                'description_en': '25% discount on all items',
                'description_ar': 'خصم 25٪ على جميع المنتجات',
                'coupon_type': 'general',
                'discount_type': 'percentage',
                'discount_value': 25,
                'max_uses': 50,
                'max_uses_per_user': 2,
                'min_order_amount': 15.000,
                'max_discount_amount': 10.000,
                'valid_from': timezone.now(),
                'valid_until': timezone.now() + timedelta(days=60),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created general coupon: {summer_coupon.code}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ General coupon already exists: {summer_coupon.code}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Coupon seeding completed!'))
        self.stdout.write(f'\nTotal coupons in database: {Coupon.objects.count()}')
