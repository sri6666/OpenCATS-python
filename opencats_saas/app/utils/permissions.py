"""
Permission System
Maps permissions to required access levels
"""

# Access level constants
ACCESS_LEVEL_DELETED = -100
ACCESS_LEVEL_DISABLED = 0
ACCESS_LEVEL_READ = 100
ACCESS_LEVEL_EDIT = 200
ACCESS_LEVEL_DELETE = 300
ACCESS_LEVEL_DEMO = 350
ACCESS_LEVEL_SA = 400  # Site Administrator
ACCESS_LEVEL_MULTI_SA = 450  # Multi-tenant SA
ACCESS_LEVEL_ROOT = 500  # Root Administrator

# Permission mapping
PERMISSIONS = {
    # Candidates
    'candidates.view': ACCESS_LEVEL_READ,
    'candidates.add': ACCESS_LEVEL_EDIT,
    'candidates.edit': ACCESS_LEVEL_EDIT,
    'candidates.delete': ACCESS_LEVEL_DELETE,

    # Job Orders
    'joborders.view': ACCESS_LEVEL_READ,
    'joborders.add': ACCESS_LEVEL_EDIT,
    'joborders.edit': ACCESS_LEVEL_EDIT,
    'joborders.delete': ACCESS_LEVEL_DELETE,

    # Companies
    'companies.view': ACCESS_LEVEL_READ,
    'companies.add': ACCESS_LEVEL_EDIT,
    'companies.edit': ACCESS_LEVEL_EDIT,
    'companies.delete': ACCESS_LEVEL_DELETE,

    # Contacts
    'contacts.view': ACCESS_LEVEL_READ,
    'contacts.add': ACCESS_LEVEL_EDIT,
    'contacts.edit': ACCESS_LEVEL_EDIT,
    'contacts.delete': ACCESS_LEVEL_DELETE,

    # Calendar/Activities
    'calendar.view': ACCESS_LEVEL_READ,
    'calendar.add': ACCESS_LEVEL_EDIT,
    'calendar.edit': ACCESS_LEVEL_EDIT,
    'calendar.delete': ACCESS_LEVEL_EDIT,

    'activities.view': ACCESS_LEVEL_READ,
    'activities.add': ACCESS_LEVEL_EDIT,
    'activities.edit': ACCESS_LEVEL_EDIT,
    'activities.delete': ACCESS_LEVEL_DELETE,

    # Reports
    'reports.view': ACCESS_LEVEL_READ,
    'reports.export': ACCESS_LEVEL_EDIT,

    # Settings
    'settings.view': ACCESS_LEVEL_SA,
    'settings.edit': ACCESS_LEVEL_SA,
    'users.manage': ACCESS_LEVEL_SA,

    # Import/Export
    'import.candidates': ACCESS_LEVEL_EDIT,
    'import.companies': ACCESS_LEVEL_EDIT,
    'export.data': ACCESS_LEVEL_EDIT,

    # Admin
    'admin.access': ACCESS_LEVEL_SA,
    'admin.billing': ACCESS_LEVEL_SA,
    'admin.site': ACCESS_LEVEL_ROOT,
}


def get_required_level(permission):
    """Get required access level for permission"""
    return PERMISSIONS.get(permission, ACCESS_LEVEL_READ)
