"""
Django management command to create test users with random connections.

Usage:
    python manage.py create_test_users --count 50
    python manage.py create_test_users --count 100 --photos 10 --posts 5
    python manage.py create_test_users --count 20 --clean
"""

import random
import string
from datetime import date, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from users.models import CustomUser, UserRelationship
from photos.models import Photo
from posts.models import Post


class Command(BaseCommand):
    help = 'Create test users with random connections, photos, and posts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of test users to create (default: 20)'
        )
        parser.add_argument(
            '--photos',
            type=int,
            default=None,
            help='Max number of photos per user (random 0-N, default: 0-15)'
        )
        parser.add_argument(
            '--posts',
            type=int,
            default=None,
            help='Max number of posts per user (random 0-N, default: 0-10)'
        )
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean existing test users before creating new ones'
        )
        parser.add_argument(
            '--connections',
            type=float,
            default=0.3,
            help='Connection probability between users (0.0-1.0, default: 0.3)'
        )

    def handle(self, *args, **options):
        count = options['count']
        max_photos = options['photos'] or 15
        max_posts = options['posts'] or 10
        clean = options['clean']
        connection_prob = options['connections']

        if count <= 0:
            raise CommandError('Count must be positive')
        
        if connection_prob < 0 or connection_prob > 1:
            raise CommandError('Connection probability must be between 0.0 and 1.0')

        self.stdout.write(
            self.style.SUCCESS(f'Creating {count} test users...')
        )

        try:
            with transaction.atomic():
                if clean:
                    self._clean_test_users()
                
                users = self._create_test_users(count)
                self._create_random_connections(users, connection_prob)
                self._create_test_content(users, max_photos, max_posts)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created {count} test users with random connections and content!'
                )
            )
            
        except Exception as e:
            raise CommandError(f'Error creating test users: {str(e)}')

    def _clean_test_users(self):
        """Remove existing test users"""
        test_users = CustomUser.objects.filter(bio="TEST USERS")
        count = test_users.count()
        
        if count > 0:
            self.stdout.write(f'Cleaning {count} existing test users...')
            test_users.delete()
            self.stdout.write(
                self.style.WARNING(f'Deleted {count} existing test users')
            )

    def _create_test_users(self, count):
        """Create test users with random profiles"""
        users = []
        
        # Common test data
        first_names = [
            'Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Henry',
            'Ivy', 'Jack', 'Kate', 'Liam', 'Maya', 'Noah', 'Olivia', 'Paul',
            'Quinn', 'Ruby', 'Sam', 'Tara', 'Uma', 'Victor', 'Wendy', 'Xander',
            'Yara', 'Zoe', 'Alex', 'Blake', 'Casey', 'Drew'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
        ]

        self.stdout.write('Creating users...')
        
        for i in range(count):
            # Generate random user data
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            username = f"testuser_{i+1:03d}_{random.randint(100, 999)}"
            email = f"{username}@test.com"
            
            # Random birth date (18-65 years old)
            min_age = 18
            max_age = 65
            birth_year = date.today().year - random.randint(min_age, max_age)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)  # Safe day for all months
            birth_date = date(birth_year, birth_month, birth_day)
            
            # Random privacy setting (30% private)
            is_private = random.random() < 0.3
            
            # Create user
            user = CustomUser.objects.create_user(
                email=email,
                username=username,
                password='testpassword123',
                first_name=first_name,
                last_name=last_name,
                date_of_birth=birth_date,
                bio="TEST USERS",
                is_private=is_private,
                is_email_verified=True,
                is_active=True
            )
            
            users.append(user)
            
            if (i + 1) % 10 == 0:
                self.stdout.write(f'Created {i + 1}/{count} users')

        self.stdout.write(
            self.style.SUCCESS(f'Created {len(users)} test users')
        )
        return users

    def _create_random_connections(self, users, connection_prob):
        """Create random follow relationships between users"""
        self.stdout.write('Creating random connections...')
        
        total_connections = 0
        close_friends = 0
        
        for user in users:
            # Each user follows some others based on probability
            for other_user in users:
                if user != other_user and random.random() < connection_prob:
                    # Create follow relationship
                    UserRelationship.objects.get_or_create(
                        from_user=user,
                        to_user=other_user,
                        relationship_type="follow"
                    )
                    total_connections += 1
                    
                    # 20% chance to also be close friends (if following)
                    if random.random() < 0.2:
                        UserRelationship.objects.get_or_create(
                            from_user=user,
                            to_user=other_user,
                            relationship_type="close_friend"
                        )
                        close_friends += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {total_connections} follow relationships and {close_friends} close friend relationships'
            )
        )

    def _create_test_content(self, users, max_photos, max_posts):
        """Create random photos and posts for test users"""
        self.stdout.write('Creating test content...')
        
        total_photos = 0
        total_posts = 0
        
        for user in users:
            # Random number of photos (0 to max_photos)
            num_photos = random.randint(0, max_photos)
            for i in range(num_photos):
                try:
                    photo = Photo.objects.create(
                        user=user,
                        title="TEST PHOTO",
                        description="TEST USERS",
                        file_path=f"test/photo_{user.id}_{i+1}.jpg",  # Dummy path
                        created_at=self._random_recent_date(),
                        is_public=not user.is_private or random.random() < 0.7  # 70% public even for private users
                    )
                    total_photos += 1
                except Exception:
                    # Skip if photo creation fails (missing file, etc.)
                    pass
            
            # Random number of posts (0 to max_posts)
            num_posts = random.randint(0, max_posts)
            for i in range(num_posts):
                try:
                    post = Post.objects.create(
                        author=user,
                        title="TEST USERS",
                        content="TEST USERS - This is a test post created for development purposes.",
                        is_public=not user.is_private or random.random() < 0.7,  # 70% public even for private users
                        created_at=self._random_recent_date()
                    )
                    total_posts += 1
                except Exception:
                    # Skip if post creation fails
                    pass

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {total_photos} test photos and {total_posts} test posts'
            )
        )

    def _random_recent_date(self):
        """Generate a random date within the last 6 months"""
        now = timezone.now()
        days_ago = random.randint(0, 180)  # 0-6 months ago
        hours_ago = random.randint(0, 23)
        minutes_ago = random.randint(0, 59)
        
        return now - timedelta(
            days=days_ago,
            hours=hours_ago,
            minutes=minutes_ago
        )
