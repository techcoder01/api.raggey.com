"""
Professional Cache Invalidation using Django Signals
Automatically clears cache when design models are modified
"""
from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
import logging

from .models import (
    FabricType, FabricColor,
    GholaType, SleevesType, PocketType,
    ButtonType, BodyType
)

logger = logging.getLogger(__name__)


def invalidate_all_design_cache():
    """
    Professional cache invalidation - clears all design-related caches
    Uses multiple strategies to ensure cache is properly cleared
    """
    try:
        logger.info("🔥 Starting cache invalidation...")

        # Strategy 1: Clear entire Django cache (most reliable)
        cache.clear()
        logger.info("✅ Django cache cleared")

        # Strategy 2: If using Redis, flush the database
        if 'django_redis' in settings.CACHES.get('default', {}).get('BACKEND', ''):
            try:
                from django_redis import get_redis_connection
                redis_conn = get_redis_connection('default')

                # Get all keys and delete them
                all_keys = redis_conn.keys('*')
                if all_keys:
                    redis_conn.delete(*all_keys)
                    logger.info(f"✅ Redis: Deleted {len(all_keys)} cache keys")
                else:
                    logger.info("✅ Redis: No keys to delete")

            except Exception as redis_err:
                logger.warning(f"⚠️ Redis specific clearing failed: {redis_err}")

        # Strategy 3: Clear specific cache key patterns (if cache.clear() fails)
        try:
            # Clear view cache keys
            cache_patterns = [
                'views.decorators.cache.cache_page',
                'design',
                'fabric',
                'collar',
                'sleeves',
                'pocket',
                'button',
                'body',
            ]

            for pattern in cache_patterns:
                cache.delete_pattern(f'*{pattern}*')

        except AttributeError:
            # delete_pattern not available in all cache backends
            pass

        logger.info("🎯 Cache invalidation completed successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Cache invalidation failed: {e}")
        return False


# ==================== AUTO CACHE INVALIDATION SIGNALS ====================

@receiver(post_save, sender=FabricType)
@receiver(post_delete, sender=FabricType)
def fabric_type_changed(sender, instance, **kwargs):
    """Clear cache when FabricType is modified"""
    logger.info(f"📝 FabricType changed: {instance.fabric_name_eng}")
    invalidate_all_design_cache()


@receiver(post_save, sender=FabricColor)
@receiver(post_delete, sender=FabricColor)
def fabric_color_changed(sender, instance, **kwargs):
    """Clear cache when FabricColor is modified"""
    logger.info(f"📝 FabricColor changed: {instance.color_name_eng}")
    invalidate_all_design_cache()


@receiver(post_save, sender=GholaType)
@receiver(post_delete, sender=GholaType)
def collar_changed(sender, instance, **kwargs):
    """Clear cache when Collar is modified"""
    logger.info(f"📝 Collar changed: {instance.ghola_type_name_eng}")
    invalidate_all_design_cache()


@receiver(post_save, sender=SleevesType)
@receiver(post_delete, sender=SleevesType)
def sleeves_changed(sender, instance, **kwargs):
    """Clear cache when Sleeves is modified"""
    logger.info(f"📝 Sleeves changed: {instance.sleeves_type_name_eng}")
    invalidate_all_design_cache()


@receiver(post_save, sender=PocketType)
@receiver(post_delete, sender=PocketType)
def pocket_changed(sender, instance, **kwargs):
    """Clear cache when Pocket is modified"""
    logger.info(f"📝 Pocket changed: {instance.pocket_type_name_eng}")
    invalidate_all_design_cache()


@receiver(post_save, sender=ButtonType)
@receiver(post_delete, sender=ButtonType)
def button_changed(sender, instance, **kwargs):
    """Clear cache when Button is modified"""
    logger.info(f"📝 Button changed: {instance.button_type_name_eng}")
    invalidate_all_design_cache()





@receiver(post_save, sender=BodyType)
@receiver(post_delete, sender=BodyType)
def body_changed(sender, instance, **kwargs):
    """Clear cache when Body is modified"""
    logger.info(f"📝 Body changed: {instance.body_type_name_eng}")
    invalidate_all_design_cache()


logger.info("✅ Design cache invalidation signals registered successfully")
