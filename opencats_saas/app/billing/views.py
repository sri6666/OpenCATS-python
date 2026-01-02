"""
Billing Views - Subscription Management
"""
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.billing import billing_bp
from app.models import Site
from app.extensions import db
from app.utils.decorators import admin_required
import stripe
from datetime import datetime

# Initialize Stripe
def init_stripe():
    """Initialize Stripe with secret key"""
    stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')


@billing_bp.route('/plans')
@login_required
def plans():
    """View available subscription plans"""
    from config import Config

    site = current_user.site
    current_plan = Config.SUBSCRIPTION_PLANS.get(site.subscription_plan, {})
    all_plans = Config.SUBSCRIPTION_PLANS

    # Calculate trial days left
    trial_days_left = None
    if site.subscription_status == 'trial' and site.trial_ends_at:
        trial_days_left = (site.trial_ends_at - datetime.utcnow()).days

    return render_template('billing/plans.html',
                         site=site,
                         current_plan=current_plan,
                         all_plans=all_plans,
                         trial_days_left=trial_days_left)


@billing_bp.route('/checkout/<plan_name>')
@login_required
@admin_required
def checkout(plan_name):
    """Create Stripe checkout session for plan upgrade"""
    init_stripe()

    from config import Config

    # Validate plan
    if plan_name not in Config.SUBSCRIPTION_PLANS:
        flash('Invalid plan selected.', 'danger')
        return redirect(url_for('billing.plans'))

    plan = Config.SUBSCRIPTION_PLANS[plan_name]
    site = current_user.site

    # Check if downgrading
    current_tier = ['starter', 'professional', 'enterprise'].index(site.subscription_plan)
    new_tier = ['starter', 'professional', 'enterprise'].index(plan_name)

    if new_tier < current_tier:
        flash('Please contact support for plan downgrades.', 'warning')
        return redirect(url_for('billing.plans'))

    try:
        # Create or retrieve Stripe customer
        if not site.stripe_customer_id:
            customer = stripe.Customer.create(
                email=current_user.email,
                metadata={
                    'site_id': site.site_id,
                    'site_name': site.name
                }
            )
            site.stripe_customer_id = customer.id
            db.session.commit()

        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=site.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': plan['price'] * 100,  # Convert to cents
                    'recurring': {
                        'interval': 'month'
                    },
                    'product_data': {
                        'name': f"OpenCATS {plan_name.title()} Plan",
                        'description': f"{plan['features']['max_users']} users, {plan['features']['max_candidates']} candidates",
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('billing.success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('billing.plans', _external=True),
            metadata={
                'site_id': site.site_id,
                'plan_name': plan_name
            }
        )

        return redirect(checkout_session.url, code=303)

    except stripe.error.StripeError as e:
        flash(f'Payment error: {str(e)}', 'danger')
        return redirect(url_for('billing.plans'))


@billing_bp.route('/success')
@login_required
def success():
    """Payment success callback"""
    session_id = request.args.get('session_id')

    if not session_id:
        flash('Invalid payment session.', 'danger')
        return redirect(url_for('billing.plans'))

    init_stripe()

    try:
        # Retrieve session
        session = stripe.checkout.Session.retrieve(session_id)

        if session.payment_status == 'paid':
            site = current_user.site
            plan_name = session.metadata.get('plan_name')

            # Update subscription
            site.subscription_plan = plan_name
            site.subscription_status = 'active'
            site.stripe_subscription_id = session.subscription

            db.session.commit()

            flash(f'Successfully subscribed to {plan_name.title()} plan!', 'success')
        else:
            flash('Payment not completed. Please try again.', 'warning')

    except stripe.error.StripeError as e:
        flash(f'Error verifying payment: {str(e)}', 'danger')

    return redirect(url_for('billing.plans'))


@billing_bp.route('/portal')
@login_required
@admin_required
def customer_portal():
    """Redirect to Stripe customer portal for subscription management"""
    init_stripe()

    site = current_user.site

    if not site.stripe_customer_id:
        flash('No active subscription found.', 'warning')
        return redirect(url_for('billing.plans'))

    try:
        # Create portal session
        portal_session = stripe.billing_portal.Session.create(
            customer=site.stripe_customer_id,
            return_url=url_for('billing.plans', _external=True)
        )

        return redirect(portal_session.url, code=303)

    except stripe.error.StripeError as e:
        flash(f'Error accessing customer portal: {str(e)}', 'danger')
        return redirect(url_for('billing.plans'))


@billing_bp.route('/cancel', methods=['POST'])
@login_required
@admin_required
def cancel_subscription():
    """Cancel subscription"""
    init_stripe()

    site = current_user.site

    if not site.stripe_subscription_id:
        flash('No active subscription to cancel.', 'warning')
        return redirect(url_for('billing.plans'))

    try:
        # Cancel subscription at period end
        subscription = stripe.Subscription.modify(
            site.stripe_subscription_id,
            cancel_at_period_end=True
        )

        flash('Subscription will be canceled at the end of the current billing period.', 'info')

    except stripe.error.StripeError as e:
        flash(f'Error canceling subscription: {str(e)}', 'danger')

    return redirect(url_for('billing.plans'))


@billing_bp.route('/usage')
@login_required
@admin_required
def usage():
    """View current usage statistics"""
    site = current_user.site
    from config import Config

    plan = Config.SUBSCRIPTION_PLANS.get(site.subscription_plan, {})
    limits = plan.get('features', {})

    # Calculate usage
    stats = {
        'users': User.query_for_site(site.site_id).filter_by(is_active=True).count(),
        'candidates': Candidate.query_for_site(site.site_id).filter_by(is_admin_hidden=False).count(),
        'jobs': JobOrder.query_for_site(site.site_id).filter_by(is_admin_hidden=False).count(),
        'storage_mb': site.storage_used_mb
    }

    # Calculate percentages
    usage_data = {
        'users': {
            'used': stats['users'],
            'limit': limits.get('max_users', -1),
            'percentage': calculate_usage_percentage(stats['users'], limits.get('max_users', -1))
        },
        'candidates': {
            'used': stats['candidates'],
            'limit': limits.get('max_candidates', -1),
            'percentage': calculate_usage_percentage(stats['candidates'], limits.get('max_candidates', -1))
        },
        'jobs': {
            'used': stats['jobs'],
            'limit': limits.get('max_jobs', -1),
            'percentage': calculate_usage_percentage(stats['jobs'], limits.get('max_jobs', -1))
        },
        'storage': {
            'used_mb': stats['storage_mb'],
            'limit_mb': limits.get('storage_gb', 0) * 1024,
            'percentage': calculate_usage_percentage(stats['storage_mb'], limits.get('storage_gb', 0) * 1024)
        }
    }

    return render_template('billing/usage.html',
                         site=site,
                         plan=plan,
                         usage=usage_data)


def calculate_usage_percentage(used, limit):
    """Calculate usage percentage"""
    if limit == -1:  # Unlimited
        return 0
    if limit == 0:
        return 100
    return min(100, int((used / limit) * 100))
