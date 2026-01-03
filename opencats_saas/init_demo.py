#!/usr/bin/env python3
"""
Initialize OpenCATS demo database with sample data
"""
import os
os.chdir('/home/user/OpenCATS-python/opencats_saas')

from app import create_app
from app.extensions import db
from app.models import Site, User, Candidate, JobOrder, Company, Contact
from datetime import datetime

app = create_app()

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("✓ Database tables created")

    # Check if demo site already exists
    demo_site = Site.query.filter_by(subdomain='demo').first()
    if demo_site:
        print("✓ Demo site already exists")
    else:
        # Create demo site
        print("\nCreating demo site...")
        demo_site = Site(
            name='Demo Company',
            subdomain='demo',
            subscription_plan='starter',
            subscription_status='trial',
            trial_ends_at=datetime.utcnow(),
            is_active=True
        )
        db.session.add(demo_site)
        db.session.commit()
        print(f"✓ Demo site created (ID: {demo_site.site_id})")

        # Create admin user
        print("\nCreating admin user...")
        admin_user = User(
            site_id=demo_site.site_id,
            username='admin',
            email='admin@demo.com',
            first_name='Admin',
            last_name='User',
            access_level=500,  # Root access
            is_active=True
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        db.session.commit()
        print(f"✓ Admin user created (username: admin, password: admin123)")

        # Create sample company
        print("\nCreating sample data...")
        company = Company(
            site_id=demo_site.site_id,
            name='Tech Innovations Inc',
            phone='555-0100',
            city='San Francisco',
            state='CA',
            is_admin_hidden=False,
            entered_by=admin_user.user_id
        )
        db.session.add(company)
        db.session.commit()
        print(f"✓ Company created: {company.name}")

        # Create sample contact
        contact = Contact(
            site_id=demo_site.site_id,
            company_id=company.company_id,
            first_name='John',
            last_name='Smith',
            title='HR Manager',
            email='john.smith@techinnovations.com',
            phone_work='555-0101',
            is_admin_hidden=False,
            entered_by=admin_user.user_id
        )
        db.session.add(contact)
        db.session.commit()
        print(f"✓ Contact created: {contact.first_name} {contact.last_name}")

        # Create sample job order
        job = JobOrder(
            site_id=demo_site.site_id,
            recruiter_id=admin_user.user_id,
            company_id=company.company_id,
            contact_id=contact.contact_id,
            title='Senior Python Developer',
            description='We are looking for an experienced Python developer...',
            type='H',  # Full-time
            duration='Permanent',
            rate_max='150000',
            salary='120000-150000',
            status=0,  # Active
            openings=2,
            openings_available=2,
            city='San Francisco',
            state='CA',
            is_admin_hidden=False,
            entered_by=admin_user.user_id
        )
        db.session.add(job)
        db.session.commit()
        print(f"✓ Job order created: {job.title}")

        # Create sample candidates
        candidates_data = [
            {
                'first_name': 'Alice',
                'last_name': 'Johnson',
                'email': 'alice.johnson@email.com',
                'phone': '555-0201',
                'key_skills': 'Python, Flask, SQLAlchemy, PostgreSQL, Docker',
                'current_employer': 'Tech Corp',
                'is_hot': True
            },
            {
                'first_name': 'Bob',
                'last_name': 'Williams',
                'email': 'bob.williams@email.com',
                'phone': '555-0202',
                'key_skills': 'Python, Django, REST APIs, AWS, MySQL',
                'current_employer': 'StartUp Inc',
                'is_hot': False
            },
            {
                'first_name': 'Carol',
                'last_name': 'Davis',
                'email': 'carol.davis@email.com',
                'phone': '555-0203',
                'key_skills': 'Python, FastAPI, Redis, Kubernetes, CI/CD',
                'current_employer': 'Big Tech',
                'is_hot': True
            }
        ]

        for data in candidates_data:
            candidate = Candidate(
                site_id=demo_site.site_id,
                first_name=data['first_name'],
                last_name=data['last_name'],
                email1=data['email'],
                phone_home=data['phone'],
                key_skills=data['key_skills'],
                current_employer=data['current_employer'],
                is_hot=data['is_hot'],
                is_active=True,
                is_admin_hidden=False,
                entered_by=admin_user.user_id,
                owner=admin_user.user_id
            )
            db.session.add(candidate)
            print(f"✓ Candidate created: {candidate.first_name} {candidate.last_name}")

        db.session.commit()

    print("\n" + "="*60)
    print("✅ DEMO DATABASE INITIALIZED SUCCESSFULLY!")
    print("="*60)
    print("\nLogin credentials:")
    print("  URL: http://localhost:5000")
    print("  Username: admin")
    print("  Password: admin123")
    print("\nData created:")
    print(f"  - Sites: {Site.query.count()}")
    print(f"  - Users: {User.query.count()}")
    print(f"  - Companies: {Company.query.count()}")
    print(f"  - Contacts: {Contact.query.count()}")
    print(f"  - Job Orders: {JobOrder.query.count()}")
    print(f"  - Candidates: {Candidate.query.count()}")
    print("="*60)
