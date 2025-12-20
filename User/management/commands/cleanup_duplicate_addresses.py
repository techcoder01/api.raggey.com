"""
Django management command to clean up duplicate addresses
Usage: python manage.py cleanup_duplicate_addresses
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from User.models import Address


class Command(BaseCommand):
    help = 'Remove duplicate addresses for all users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No addresses will be deleted'))

        total_duplicates = 0
        total_kept = 0

        for user in User.objects.all():
            self.stdout.write(f'\n📋 Checking addresses for user: {user.username} (ID: {user.id})')

            addresses = Address.objects.filter(user=user).order_by('-created_at')

            if addresses.count() == 0:
                self.stdout.write('  ℹ️  No addresses found')
                continue

            self.stdout.write(f'  Found {addresses.count()} addresses')

            # Track unique addresses by key fields
            seen = {}
            duplicates_for_user = 0
            kept_for_user = 0

            for addr in addresses:
                # Create a unique key based on address components
                key = (
                    addr.governorate or '',
                    addr.area or '',
                    addr.block or '',
                    addr.street or '',
                    addr.building or '',
                    addr.apartment or '',
                    addr.floor or '',
                )

                if key in seen:
                    # Duplicate found
                    duplicates_for_user += 1
                    total_duplicates += 1

                    if dry_run:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  🗑️  Would delete: ID {addr.id} - {addr.full_address[:50]}'
                            )
                        )
                    else:
                        addr.delete()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'  ✅ Deleted duplicate: ID {addr.id} - {addr.full_address[:50]}'
                            )
                        )
                else:
                    # First occurrence, keep it
                    seen[key] = addr.id
                    kept_for_user += 1
                    total_kept += 1
                    self.stdout.write(
                        f'  ✨ Kept: ID {addr.id} - {addr.full_address[:50]}'
                    )

            if duplicates_for_user > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  📊 User summary: Kept {kept_for_user}, {"Would delete" if dry_run else "Deleted"} {duplicates_for_user}'
                    )
                )

        # Final summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('\n📈 FINAL SUMMARY:'))
        self.stdout.write(f'  ✅ Total addresses kept: {total_kept}')

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'  🗑️  Total duplicates that would be deleted: {total_duplicates}')
            )
            self.stdout.write('\n💡 Run without --dry-run to actually delete duplicates')
        else:
            self.stdout.write(
                self.style.SUCCESS(f'  🗑️  Total duplicates deleted: {total_duplicates}')
            )

        self.stdout.write('=' * 60 + '\n')
