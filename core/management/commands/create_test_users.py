from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = 'Create test users for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test users...')
        
        # Load fixtures
        call_command('loaddata', 'test_users', verbosity=1)
        
        self.stdout.write(self.style.SUCCESS('Successfully created test users!'))
        self.stdout.write(self.style.SUCCESS('You can now login with:'))
        self.stdout.write(self.style.SUCCESS('- Username: student1, Password: password123'))
        self.stdout.write(self.style.SUCCESS('- Username: student2, Password: password123'))
        self.stdout.write(self.style.SUCCESS('- Username: student3, Password: password123')) 