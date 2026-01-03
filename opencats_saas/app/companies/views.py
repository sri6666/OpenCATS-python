"""
Companies Views - Client Management
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.companies import companies_bp
from app.companies.forms import CompanyForm, CompanySearchForm, DepartmentForm
from app.models import Company, CompanyDepartment, Contact, JobOrder, Activity
from app.extensions import db
from app.utils.decorators import permission_required
from datetime import datetime


@companies_bp.route('/')
@login_required
@permission_required('companies.view')
def index():
    """List all companies"""
    page = request.args.get('page', 1, type=int)
    per_page = current_user.items_per_page or 20

    query = Company.query_for_site(current_user.site_id)
    query = query.filter_by(is_admin_hidden=False)

    # Search filter
    search = request.args.get('search')
    if search:
        search_term = f'%{search}%'
        query = query.filter(Company.name.like(search_term))

    # Hot companies
    if request.args.get('hot') == '1':
        query = query.filter_by(is_hot=True)

    # Sorting
    sort_by = request.args.get('sort', 'name')
    sort_dir = request.args.get('dir', 'asc')

    if sort_by == 'name':
        order_col = Company.name
    elif sort_by == 'date_created':
        order_col = Company.date_created
    else:
        order_col = Company.date_modified

    if sort_dir == 'desc':
        order_col = order_col.desc()

    query = query.order_by(order_col)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return render_template('companies/index.html',
                         companies=pagination.items,
                         pagination=pagination,
                         search=search)


@companies_bp.route('/<int:id>')
@companies_bp.route('/view/<int:id>')
@login_required
@permission_required('companies.view')
def show(id):
    """Show company details"""
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=id).first_or_404()

    if company.is_admin_hidden:
        flash('Company not found.', 'warning')
        return redirect(url_for('companies.index'))

    # Load related data
    contacts = company.contacts.filter_by().all()
    joborders = company.joborders.filter_by(is_admin_hidden=False).order_by(JobOrder.date_modified.desc()).limit(10).all()
    departments = company.departments.all()

    activities = Activity.query_for_site(current_user.site_id).filter_by(
        data_item_type=200,  # Company
        data_item_id=company.company_id
    ).order_by(Activity.date_created.desc()).limit(10).all()

    return render_template('companies/view.html',
                         company=company,
                         contacts=contacts,
                         joborders=joborders,
                         departments=departments,
                         activities=activities)


@companies_bp.route('/add', methods=['GET', 'POST'])
@login_required
@permission_required('companies.add')
def add():
    """Add new company"""
    form = CompanyForm()

    if form.validate_on_submit():
        company = Company(
            site_id=current_user.site_id,
            entered_by=current_user.user_id,
            owner=current_user.user_id
        )

        form.populate_obj(company)

        db.session.add(company)
        db.session.commit()

        # Log activity
        log_activity(company.company_id, 200, 'created', current_user.user_id)

        flash(f'Company "{company.name}" added successfully.', 'success')
        return redirect(url_for('companies.show', id=company.company_id))

    return render_template('companies/add.html', form=form)


@companies_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@permission_required('companies.edit')
def edit(id):
    """Edit company"""
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=id).first_or_404()

    if company.is_admin_hidden:
        flash('Company not found.', 'warning')
        return redirect(url_for('companies.index'))

    form = CompanyForm(obj=company)

    if form.validate_on_submit():
        form.populate_obj(company)
        company.date_modified = datetime.utcnow()

        db.session.commit()

        # Log activity
        log_activity(company.company_id, 200, 'updated', current_user.user_id)

        flash(f'Company "{company.name}" updated successfully.', 'success')
        return redirect(url_for('companies.show', id=company.company_id))

    return render_template('companies/edit.html', form=form, company=company)


@companies_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('companies.delete')
def delete(id):
    """Delete (hide) company"""
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=id).first_or_404()

    company.is_admin_hidden = True
    company.date_modified = datetime.utcnow()

    db.session.commit()

    # Log activity
    log_activity(company.company_id, 200, 'deleted', current_user.user_id)

    flash(f'Company "{company.name}" has been deleted.', 'success')
    return redirect(url_for('companies.index'))


@companies_bp.route('/<int:company_id>/departments/add', methods=['GET', 'POST'])
@login_required
@permission_required('companies.edit')
def add_department(company_id):
    """Add department to company"""
    company = Company.query_for_site(current_user.site_id).filter_by(company_id=company_id).first_or_404()
    form = DepartmentForm()

    if form.validate_on_submit():
        department = CompanyDepartment(
            site_id=current_user.site_id,
            company_id=company_id,
            name=form.name.data,
            entered_by=current_user.user_id,
            owner=current_user.user_id
        )

        db.session.add(department)
        db.session.commit()

        flash(f'Department "{department.name}" added.', 'success')
        return redirect(url_for('companies.show', id=company_id))

    return render_template('companies/add_department.html', form=form, company=company)


@companies_bp.route('/search', methods=['GET', 'POST'])
@login_required
@permission_required('companies.view')
def search():
    """Search companies"""
    form = CompanySearchForm()

    if form.validate_on_submit():
        query = Company.query_for_site(current_user.site_id)
        query = query.filter_by(is_admin_hidden=False)

        if form.name.data:
            query = query.filter(Company.name.like(f'%{form.name.data}%'))

        if form.city.data:
            query = query.filter(Company.city.like(f'%{form.city.data}%'))

        if form.state.data:
            query = query.filter_by(state=form.state.data)

        if form.technologies.data:
            query = query.filter(Company.key_technologies.like(f'%{form.technologies.data}%'))

        results = query.limit(100).all()

        return render_template('companies/search_results.html',
                             form=form,
                             results=results,
                             count=len(results))

    return render_template('companies/search.html', form=form)


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
