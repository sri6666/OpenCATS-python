"""
Stripe Webhook Handlers
"""
from flask import request, jsonify, current_app
from app.billing import billing_bp
from app.models import Site
from app.extensions import db
import stripe
from datetime import datetime


@billing_bp.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        # Invalid payload
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle different event types
    event_type = event['type']
    data = event['data']['object']

    if event_type == 'checkout.session.completed':
        handle_checkout_completed(data)
    elif event_type == 'customer.subscription.created':
        handle_subscription_created(data)
    elif event_type == 'customer.subscription.updated':
        handle_subscription_updated(data)
    elif event_type == 'customer.subscription.deleted':
        handle_subscription_deleted(data)
    elif event_type == 'invoice.payment_succeeded':
        handle_payment_succeeded(data)
    elif event_type == 'invoice.payment_failed':
        handle_payment_failed(data)

    return jsonify({'status': 'success'}), 200


def handle_checkout_completed(session):
    """Handle successful checkout"""
    site_id = session.get('metadata', {}).get('site_id')
    plan_name = session.get('metadata', {}).get('plan_name')

    if site_id and plan_name:
        site = Site.query.get(site_id)
        if site:
            site.subscription_plan = plan_name
            site.subscription_status = 'active'
            site.stripe_subscription_id = session.get('subscription')
            site.trial_ends_at = None  # Clear trial

            db.session.commit()

            # Send welcome email
            send_subscription_email(site, 'activated')


def handle_subscription_created(subscription):
    """Handle new subscription creation"""
    customer_id = subscription.get('customer')

    site = Site.query.filter_by(stripe_customer_id=customer_id).first()
    if site:
        site.stripe_subscription_id = subscription.get('id')
        site.subscription_status = 'active'

        db.session.commit()


def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')

    site = Site.query.filter_by(
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id
    ).first()

    if site:
        # Update status based on subscription status
        stripe_status = subscription.get('status')

        if stripe_status == 'active':
            site.subscription_status = 'active'
        elif stripe_status == 'past_due':
            site.subscription_status = 'past_due'
        elif stripe_status == 'canceled':
            site.subscription_status = 'canceled'
        elif stripe_status == 'unpaid':
            site.subscription_status = 'past_due'

        # Check if subscription will cancel at period end
        if subscription.get('cancel_at_period_end'):
            site.subscription_ends_at = datetime.fromtimestamp(
                subscription.get('current_period_end')
            )

        db.session.commit()


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    customer_id = subscription.get('customer')

    site = Site.query.filter_by(stripe_customer_id=customer_id).first()
    if site:
        site.subscription_status = 'canceled'
        site.subscription_ends_at = datetime.utcnow()

        db.session.commit()

        # Send cancellation email
        send_subscription_email(site, 'canceled')


def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice.get('customer')
    subscription_id = invoice.get('subscription')

    site = Site.query.filter_by(
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id
    ).first()

    if site:
        # Ensure status is active
        if site.subscription_status in ['past_due', 'unpaid']:
            site.subscription_status = 'active'
            db.session.commit()

        # Send receipt email
        send_payment_receipt(site, invoice)


def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice.get('customer')

    site = Site.query.filter_by(stripe_customer_id=customer_id).first()
    if site:
        site.subscription_status = 'past_due'
        db.session.commit()

        # Send payment failed email
        send_payment_failed_email(site, invoice)


def send_subscription_email(site, event_type):
    """Send subscription-related email"""
    # TODO: Implement email sending via Celery task
    from app.tasks.email import send_email

    if event_type == 'activated':
        subject = 'Welcome to OpenCATS!'
        template = 'emails/subscription_activated.html'
    elif event_type == 'canceled':
        subject = 'Subscription Canceled'
        template = 'emails/subscription_canceled.html'
    else:
        return

    # Queue email task
    # send_email.delay(site.owner.email, subject, template, {'site': site})


def send_payment_receipt(site, invoice):
    """Send payment receipt email"""
    # TODO: Implement via Celery
    pass


def send_payment_failed_email(site, invoice):
    """Send payment failure notification"""
    # TODO: Implement via Celery
    pass
