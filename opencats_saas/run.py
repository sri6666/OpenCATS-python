"""
OpenCATS SaaS - Application Entry Point
Run with: python run.py or flask run
"""
import os
from app import create_app
from app.extensions import db
from app.models import User, Site, Candidate, Company, JobOrder

# Create application
app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Shell context for flask shell
@app.shell_context_processor
def make_shell_context():
    """Make database models available in flask shell"""
    return {
        'db': db,
        'User': User,
        'Site': Site,
        'Candidate': Candidate,
        'Company': Company,
        'JobOrder': JobOrder,
    }


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
