"""
Stripe Service for Company Subscriptions

Handles:
- Customer creation
- Subscription management
- Webhook processing
- Trial period handling (1 month free)
- $50/month pricing (limited time promotional rate)
"""

import stripe
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Configure Stripe - set dynamically to ensure settings are loaded
def _get_stripe_api_key():
    """Get the Stripe API key, ensuring Django settings are loaded."""
    key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if key:
        stripe.api_key = key
    return key

# Pricing configuration
SUBSCRIPTION_PRICE_CENTS = 5000  # $50.00 (limited time promotional rate)
TRIAL_DAYS = 30  # 1 month free trial


class StripeService:
    """Service class for Stripe subscription operations"""

    @staticmethod
    def is_configured():
        """Check if Stripe is properly configured with valid API keys"""
        key = _get_stripe_api_key()
        if not key:
            return False
        # Validate key format - must start with sk_test_ or sk_live_
        if not (key.startswith('sk_test_') or key.startswith('sk_live_')):
            logger.error(f"Invalid Stripe API key format. Key must start with 'sk_test_' or 'sk_live_'. Got: {key[:10]}...")
            return False
        return True

    @staticmethod
    def get_configuration_error():
        """Get a descriptive error message for Stripe configuration issues"""
        if not stripe.api_key:
            return "Stripe API key is not set. Please configure STRIPE_SECRET_KEY in your environment."
        key = stripe.api_key
        if not (key.startswith('sk_test_') or key.startswith('sk_live_')):
            return f"Invalid Stripe API key format. Keys must start with 'sk_test_' or 'sk_live_'. Your key starts with '{key[:5]}...' which is not valid. Please get valid API keys from https://dashboard.stripe.com/apikeys"
        return None

    @staticmethod
    def create_customer(company, user):
        """
        Create a Stripe customer for a company.

        Args:
            company: Company model instance
            user: User who is setting up the subscription

        Returns:
            Stripe Customer object
        """
        _get_stripe_api_key()  # Ensure API key is set
        try:
            customer = stripe.Customer.create(
                name=company.name,
                email=user.email,
                metadata={
                    'company_id': str(company.id),
                    'company_name': company.name,
                    'user_id': str(user.id),
                }
            )
            logger.info(f"Created Stripe customer {customer.id} for company {company.id}")
            return customer
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise

    @staticmethod
    def get_or_create_price(interval='month'):
        """
        Get or create the subscription price in Stripe.

        This should ideally be created once in the Stripe dashboard,
        but this method provides programmatic creation if needed.

        Args:
            interval: 'month' or 'year'

        Returns:
            Price ID string
        """
        _get_stripe_api_key()  # Ensure API key is set
        price_id = getattr(settings, 'STRIPE_PRICE_ID', None)
        if price_id:
            return price_id

        # Create price programmatically if not configured
        try:
            # First, get or create the product
            products = stripe.Product.list(limit=1, active=True)
            if products.data:
                product = products.data[0]
            else:
                product = stripe.Product.create(
                    name="GoldVenture Company Portal Subscription",
                    description="Premium access to Company Portal features including resources, events, and investor tools"
                )

            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=SUBSCRIPTION_PRICE_CENTS if interval == 'month' else 50000,  # $500/year (limited time promotional rate)
                currency='usd',
                recurring={'interval': interval},
                metadata={'plan_type': 'monthly' if interval == 'month' else 'annual'}
            )
            logger.info(f"Created Stripe price {price.id}")
            return price.id
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe price: {str(e)}")
            raise

    @staticmethod
    def create_subscription(company, customer_id, price_id=None):
        """
        Create a subscription with a free trial.

        Args:
            company: Company model instance
            customer_id: Stripe customer ID
            price_id: Stripe price ID (optional, will use default if not provided)

        Returns:
            Stripe Subscription object
        """
        _get_stripe_api_key()  # Ensure API key is set
        if not price_id:
            price_id = StripeService.get_or_create_price()

        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=TRIAL_DAYS,
                metadata={
                    'company_id': str(company.id),
                    'company_name': company.name,
                },
                expand=['latest_invoice.payment_intent']
            )
            logger.info(f"Created subscription {subscription.id} for company {company.id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise

    @staticmethod
    def cancel_subscription(subscription_id, at_period_end=True):
        """
        Cancel a subscription.

        Args:
            subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of current period; if False, cancel immediately

        Returns:
            Stripe Subscription object
        """
        _get_stripe_api_key()  # Ensure API key is set
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            logger.info(f"Cancelled subscription {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise

    @staticmethod
    def reactivate_subscription(subscription_id):
        """
        Reactivate a subscription that was set to cancel at period end.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe Subscription object
        """
        _get_stripe_api_key()  # Ensure API key is set
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            logger.info(f"Reactivated subscription {subscription_id}")
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Error reactivating subscription: {str(e)}")
            raise

    @staticmethod
    def get_subscription(subscription_id):
        """
        Retrieve subscription details from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe Subscription object
        """
        _get_stripe_api_key()  # Ensure API key is set
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            raise

    @staticmethod
    def create_checkout_session(company, user, success_url, cancel_url, price_id=None):
        """
        Create a Stripe Checkout session for new subscriptions.

        Args:
            company: Company model instance
            user: User initiating checkout
            success_url: URL to redirect to on success
            cancel_url: URL to redirect to on cancel
            price_id: Stripe price ID (optional)

        Returns:
            Stripe Checkout Session object
        """
        _get_stripe_api_key()  # Ensure API key is set
        from .models import CompanySubscription

        if not price_id:
            price_id = StripeService.get_or_create_price()

        # Check if company already has a subscription
        try:
            existing_sub = CompanySubscription.objects.get(company=company)
            if existing_sub.stripe_customer_id:
                customer_id = existing_sub.stripe_customer_id
            else:
                customer = StripeService.create_customer(company, user)
                customer_id = customer.id
                existing_sub.stripe_customer_id = customer_id
                existing_sub.save(update_fields=['stripe_customer_id'])
        except CompanySubscription.DoesNotExist:
            customer = StripeService.create_customer(company, user)
            customer_id = customer.id

        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                subscription_data={
                    'trial_period_days': TRIAL_DAYS,
                    'metadata': {
                        'company_id': str(company.id),
                        'company_name': company.name,
                    }
                },
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'company_id': str(company.id),
                    'user_id': str(user.id),
                }
            )
            logger.info(f"Created checkout session {session.id} for company {company.id}")
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            raise

    @staticmethod
    def create_billing_portal_session(customer_id, return_url):
        """
        Create a Stripe Billing Portal session for subscription management.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Stripe BillingPortal Session object
        """
        _get_stripe_api_key()  # Ensure API key is set
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Error creating billing portal session: {str(e)}")
            raise

    @staticmethod
    def construct_webhook_event(payload, sig_header, webhook_secret=None):
        """
        Construct and verify a Stripe webhook event.

        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header
            webhook_secret: Webhook signing secret

        Returns:
            Stripe Event object
        """
        if not webhook_secret:
            webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', None)

        if not webhook_secret:
            raise ValueError("Stripe webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise


def process_subscription_webhook(event):
    """
    Process Stripe webhook events for subscriptions.

    Args:
        event: Stripe Event object

    Returns:
        dict with processing result
    """
    from .models import CompanySubscription, SubscriptionInvoice, Company

    event_type = event.type
    data = event.data.object

    logger.info(f"Processing webhook event: {event_type}")

    try:
        if event_type == 'customer.subscription.created':
            # New subscription created
            company_id = data.metadata.get('company_id')
            if company_id:
                company = Company.objects.get(id=company_id)
                subscription, created = CompanySubscription.objects.update_or_create(
                    company=company,
                    defaults={
                        'stripe_customer_id': data.customer,
                        'stripe_subscription_id': data.id,
                        'stripe_price_id': data.items.data[0].price.id if data.items.data else '',
                        'status': data.status,
                        'trial_start': datetime.fromtimestamp(data.trial_start, tz=timezone.utc) if data.trial_start else None,
                        'trial_end': datetime.fromtimestamp(data.trial_end, tz=timezone.utc) if data.trial_end else None,
                        'current_period_start': datetime.fromtimestamp(data.current_period_start, tz=timezone.utc),
                        'current_period_end': datetime.fromtimestamp(data.current_period_end, tz=timezone.utc),
                    }
                )
                logger.info(f"{'Created' if created else 'Updated'} subscription for company {company_id}")

        elif event_type == 'customer.subscription.updated':
            # Subscription updated (status change, renewal, etc.)
            subscription_id = data.id
            try:
                subscription = CompanySubscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = data.status
                subscription.cancel_at_period_end = data.cancel_at_period_end
                subscription.current_period_start = datetime.fromtimestamp(data.current_period_start, tz=timezone.utc)
                subscription.current_period_end = datetime.fromtimestamp(data.current_period_end, tz=timezone.utc)
                if data.canceled_at:
                    subscription.canceled_at = datetime.fromtimestamp(data.canceled_at, tz=timezone.utc)
                subscription.save()
                logger.info(f"Updated subscription {subscription_id} status to {data.status}")
            except CompanySubscription.DoesNotExist:
                logger.warning(f"Subscription {subscription_id} not found in database")

        elif event_type == 'customer.subscription.deleted':
            # Subscription cancelled/ended
            subscription_id = data.id
            try:
                subscription = CompanySubscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = 'canceled'
                subscription.canceled_at = timezone.now()
                subscription.save()
                logger.info(f"Marked subscription {subscription_id} as cancelled")
            except CompanySubscription.DoesNotExist:
                logger.warning(f"Subscription {subscription_id} not found in database")

        elif event_type == 'invoice.paid':
            # Invoice paid - record it
            subscription_id = data.subscription
            if subscription_id:
                try:
                    subscription = CompanySubscription.objects.get(stripe_subscription_id=subscription_id)
                    SubscriptionInvoice.objects.update_or_create(
                        stripe_invoice_id=data.id,
                        defaults={
                            'subscription': subscription,
                            'stripe_payment_intent_id': data.payment_intent or '',
                            'status': 'paid',
                            'amount_cents': data.amount_paid,
                            'currency': data.currency,
                            'invoice_date': datetime.fromtimestamp(data.created, tz=timezone.utc),
                            'paid_at': datetime.fromtimestamp(data.status_transitions.paid_at, tz=timezone.utc) if data.status_transitions.paid_at else timezone.now(),
                            'invoice_pdf_url': data.invoice_pdf or '',
                            'hosted_invoice_url': data.hosted_invoice_url or '',
                        }
                    )
                    logger.info(f"Recorded paid invoice {data.id}")
                except CompanySubscription.DoesNotExist:
                    logger.warning(f"Subscription {subscription_id} not found for invoice")

        elif event_type == 'invoice.payment_failed':
            # Payment failed - update subscription status
            subscription_id = data.subscription
            if subscription_id:
                try:
                    subscription = CompanySubscription.objects.get(stripe_subscription_id=subscription_id)
                    subscription.status = 'past_due'
                    subscription.save(update_fields=['status'])
                    logger.info(f"Marked subscription {subscription_id} as past_due due to payment failure")
                except CompanySubscription.DoesNotExist:
                    logger.warning(f"Subscription {subscription_id} not found")

        elif event_type == 'checkout.session.completed':
            # Checkout completed - link customer and subscription to company
            company_id = data.metadata.get('company_id')
            user_id = data.metadata.get('user_id')
            if company_id and data.subscription:
                from .models import User
                from .email_service import EmailService

                company = Company.objects.get(id=company_id)
                stripe_sub = stripe.Subscription.retrieve(data.subscription)
                subscription, created = CompanySubscription.objects.update_or_create(
                    company=company,
                    defaults={
                        'stripe_customer_id': data.customer,
                        'stripe_subscription_id': data.subscription,
                        'stripe_price_id': stripe_sub.items.data[0].price.id if stripe_sub.items.data else '',
                        'status': stripe_sub.status,
                        'trial_start': datetime.fromtimestamp(stripe_sub.trial_start, tz=timezone.utc) if stripe_sub.trial_start else None,
                        'trial_end': datetime.fromtimestamp(stripe_sub.trial_end, tz=timezone.utc) if stripe_sub.trial_end else None,
                        'current_period_start': datetime.fromtimestamp(stripe_sub.current_period_start, tz=timezone.utc),
                        'current_period_end': datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc),
                    }
                )
                logger.info(f"Checkout completed for company {company_id}")

                # Send confirmation email to the user who subscribed
                if user_id:
                    try:
                        user = User.objects.get(id=user_id)
                        EmailService.send_subscription_confirmation(subscription, user, company)
                        logger.info(f"Sent subscription confirmation email to user {user_id}")
                    except User.DoesNotExist:
                        logger.warning(f"User {user_id} not found for subscription email")
                    except Exception as e:
                        logger.error(f"Failed to send subscription email: {str(e)}")

        return {'success': True, 'event_type': event_type}

    except Exception as e:
        logger.error(f"Error processing webhook {event_type}: {str(e)}")
        # SECURITY: Don't expose internal error details in response
        return {'success': False, 'error': 'Webhook processing failed', 'event_type': event_type}
