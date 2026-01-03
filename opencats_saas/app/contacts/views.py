"""
Contacts Views - Contact Management
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.contacts import contacts_bp
from app.contacts.forms import ContactForm, ContactSearchForm
from app.models import Contact, Company, JobOrder, Activity
from app.extensions import db
from app.utils.decorators import permission_required
from datetime import datetime


@contacts_bp.route('/')
@login_required
@permission_required('contacts.view')
def index():
    """List all contacts"""
    page = request.args.get('page', 1, type=int)
    per_page = current_user.items_per_page or 20

    query = Contact.query_for_site(current_user.site_id)

    # Search filter
    search = request.args.get('search')
    if search:
        search_term = f'%{search}%'
        query = query.filter(
            db.or_(
                Contact.first_name.like(search_term),
                Contact.last_name.like(search_term),
                Contact.email1.like(search_term)
            )
        )

    # Company filter
    company_id = request.args.get('company_id', type=int)
    if company_id:
        query = query.filter_by(company_id=company_id)

    # Hot contacts
    if request.args.get('hot') == '1':
        query = query.filter_by(is_hot=True)

    # Sorting
    sort_by = request.args.get('sort', 'last_name')
    sort_dir = request.args.get('dir', 'asc')

    if sort_by == 'name':
        order_col = Contact.last_name
    elif sort_by == 'company':
        order_col = Company.name
        query = query.join(Contact.company)
    elif sort_by == 'date_created':
        order_col = Contact.date_created
    else:
        order_col = Contact.date_modified

    if sort_dir == 'desc':
        order_col = order_col.desc()

    query = query.order_by(order_col)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('contacts/index.html',
                         contacts=pagination.items,
                         pagination=pagination,
                         search=search)


@contacts_bp.route('/<int:id>')
@contacts_bp.route('/view/<int:id>')
@login_required
@permission_required('contacts.view')
def show(id):
    """Show contact details"""
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    # Load related data
    joborders = contact.joborders.filter_by(is_admin_hidden=False).order_by(JobOrder.date_modified.desc()).limit(10).all()

    activities = Activity.query_for_site(current_user.site_id).filter_by(
        data_item_type=300,  # Contact
        data_item_id=contact.contact_id
    ).order_by(Activity.date_created.desc()).limit(10).all()

    return render_template('contacts/show.html',
                         contact=contact,
                         joborders=joborders,
                         activities=activities)


@contacts_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('contacts.add')
def add():
    """Add new contact"""
    form = ContactForm()

    # Pre-fill company if provided
    company_id = request.args.get('company_id', type=int)
    if company_id and request.method == 'GET':
        form.company_id.data = company_id

    if form.validate_on_submit():
        contact = Contact(
            site_id=current_user.site_id,
            entered_by=current_user.user_id,
            owner=current_user.user_id
        )

        form.populate_obj(contact)

        db.session.add(contact)
        db.session.commit()

        # Log activity
        log_activity(contact.contact_id, 300, 'created', current_user.user_id)

        flash(f'Contact {contact.full_name} added successfully.', 'success')
        return redirect(url_for('contacts.show', id=contact.contact_id))

    return render_template('contacts/add.html', form=form)


@contacts_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('contacts.edit')
def edit(id):
    """Edit contact"""
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    form = ContactForm(obj=contact)

    if form.validate_on_submit():
        form.populate_obj(contact)
        contact.date_modified = datetime.utcnow()

        db.session.commit()

        # Log activity
        log_activity(contact.contact_id, 300, 'updated', current_user.user_id)

        flash(f'Contact {contact.full_name} updated successfully.', 'success')
        return redirect(url_for('contacts.show', id=contact.contact_id))

    return render_template('contacts/edit.html', form=form, contact=contact)


@contacts_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('contacts.delete')
def delete(id):
    """Delete contact"""
    contact = Contact.query_for_site(current_user.site_id).get_or_404(id)

    db.session.delete(contact)
    db.session.commit()

    # Log activity to company
    log_activity(contact.company_id, 200, f'deleted contact: {contact.full_name}', current_user.user_id)

    flash(f'Contact {contact.full_name} has been deleted.', 'success')
    return redirect(url_for('contacts.index'))


@contacts_bp.route('/search', methods=['GET', 'POST'])
@login_required
@permission_required('contacts.view')
def search():
    """Search contacts"""
    form = ContactSearchForm()

    if form.validate_on_submit():
        query = Contact.query_for_site(current_user.site_id)

        if form.name.data:
            name_term = f'%{form.name.data}%'
            query = query.filter(
                db.or_(
                    Contact.first_name.like(name_term),
                    Contact.last_name.like(name_term)
                )
            )

        if form.email.data:
            query = query.filter(
                db.or_(
                    Contact.email1.like(f'%{form.email.data}%'),
                    Contact.email2.like(f'%{form.email.data}%')
                )
            )

        if form.company_id.data:
            query = query.filter_by(company_id=form.company_id.data)

        if form.title.data:
            query = query.filter(Contact.title.like(f'%{form.title.data}%'))

        results = query.limit(100).all()

        return render_template('contacts/search_results.html',
                             form=form,
                             results=results,
                             count=len(results))

    return render_template('contacts/search.html', form=form)


def log_activity(data_item_id, data_item_type, action, user_id):
    """Log activity"""
    activity = Activity(
        site_id=current_user.site_id,
        data_item_id=data_item_id,
        data_item_type=data_item_type,
        type=400,  # Other
        notes=action,
        entered_by=user_id,
        owner=user_id
    )
    db.session.add(activity)
    db.session.commit()
