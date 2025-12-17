"""
Store Stripe Service for E-commerce Checkout

Handles:
- Checkout session creation for physical and digital goods
- Shipping rate integration
- Stripe Tax automatic calculation
- Order fulfillment via webhooks
- Digital asset download URL generation
"""

import stripe
import logging
import boto3
from botocore.config import Config
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def _get_stripe_api_key():
    """Get the Stripe API key, ensuring Django settings are loaded."""
    key = getattr(settings, 'STRIPE_SECRET_KEY', None)
    if key:
        stripe.api_key = key
    return key


class StoreStripeService:
    """Service class for Store Stripe operations"""

    @staticmethod
    def is_configured():
        """Check if Stripe is properly configured"""
        key = _get_stripe_api_key()
        return key and (key.startswith('sk_test_') or key.startswith('sk_live_'))

    @staticmethod
    def create_checkout_session(
        cart,
        user,
        shipping_address: Optional[Dict] = None,
        shipping_rate_id: Optional[int] = None,
        success_url: str = '',
        cancel_url: str = ''
    ) -> Dict[str, Any]:
        """
        Create a Stripe checkout session for store purchases.

        Handles both physical and digital goods:
        - Physical: Includes shipping address collection and rates
        - Digital: No shipping required
        - Mixed: Both types handled appropriately
        """
        from .models import StoreShippingRate, StoreCart

        if not StoreStripeService.is_configured():
            raise ValueError("Stripe is not configured")

        _get_stripe_api_key()

        # Build line items from cart
        line_items = []
        has_physical = False
        has_digital = False

        for cart_item in cart.items.select_related('product', 'variant'):
            product = cart_item.product
            variant = cart_item.variant

            # Determine price
            unit_price = cart_item.unit_price_cents

            # Product name with variant
            product_name = product.name
            if variant:
                product_name = f"{product_name} - {variant.name}"

            line_item = {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': product_name,
                        'description': product.short_description or product.description[:200],
                        'metadata': {
                            'product_id': str(product.id),
                            'variant_id': str(variant.id) if variant else '',
                            'product_type': product.product_type,
                        }
                    },
                    'unit_amount': unit_price,
                },
                'quantity': cart_item.quantity,
            }

            # Add product image if available
            primary_image = product.images.filter(is_primary=True).first()
            if not primary_image:
                primary_image = product.images.first()
            if primary_image:
                line_item['price_data']['product_data']['images'] = [primary_image.image_url]

            line_items.append(line_item)

            if product.product_type == 'physical':
                has_physical = True
            else:
                has_digital = True

        # Build checkout session params
        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': line_items,
            'mode': 'payment',
            'success_url': success_url + '?session_id={CHECKOUT_SESSION_ID}',
            'cancel_url': cancel_url,
            'metadata': {
                'cart_id': str(cart.id),
                'user_id': str(user.id),
                'has_physical': str(has_physical),
                'has_digital': str(has_digital),
            },
            'customer_email': user.email,
        }

        # Enable Stripe Tax for automatic tax calculation
        checkout_params['automatic_tax'] = {'enabled': True}

        # Handle shipping for physical goods
        if has_physical:
            if shipping_rate_id:
                shipping_rate = StoreShippingRate.objects.get(id=shipping_rate_id)

                # Create shipping rate in Stripe
                stripe_shipping = stripe.ShippingRate.create(
                    display_name=shipping_rate.name,
                    type='fixed_amount',
                    fixed_amount={
                        'amount': shipping_rate.price_cents,
                        'currency': 'usd',
                    },
                    delivery_estimate={
                        'minimum': {
                            'unit': 'business_day',
                            'value': shipping_rate.estimated_days_min,
                        },
                        'maximum': {
                            'unit': 'business_day',
                            'value': shipping_rate.estimated_days_max,
                        }
                    },
                    metadata={
                        'shipping_rate_id': str(shipping_rate.id),
                    }
                )
                checkout_params['shipping_options'] = [{'shipping_rate': stripe_shipping.id}]

            # Collect shipping address
            checkout_params['shipping_address_collection'] = {
                'allowed_countries': ['US', 'CA'],  # North America only
            }

            # Pre-fill shipping address if provided
            if shipping_address:
                checkout_params['metadata']['shipping_address'] = str(shipping_address)

        try:
            session = stripe.checkout.Session.create(**checkout_params)

            logger.info(f"Created store checkout session {session.id} for cart {cart.id}")

            return {
                'checkout_url': session.url,
                'session_id': session.id,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout: {str(e)}")
            raise ValueError(f"Payment error: {str(e)}")

    @staticmethod
    def process_webhook(event) -> Dict[str, Any]:
        """
        Process Stripe webhook events for store purchases.

        Handles:
        - checkout.session.completed: Create order, reduce inventory
        - payment_intent.payment_failed: Log failure
        """
        from .models import (
            StoreCart, StoreOrder, StoreOrderItem, StoreProduct,
            StoreRecentPurchase, UserStoreBadge, User
        )

        event_type = event.type
        data = event.data.object

        logger.info(f"Processing store webhook: {event_type}")

        if event_type == 'checkout.session.completed':
            session_id = data.id
            payment_intent_id = data.payment_intent
            customer_email = data.customer_details.email if data.customer_details else ''

            # Get metadata
            metadata = data.metadata or {}
            cart_id = metadata.get('cart_id')
            user_id = metadata.get('user_id')
            has_physical = metadata.get('has_physical') == 'True'
            has_digital = metadata.get('has_digital') == 'True'

            if not cart_id:
                logger.warning(f"No cart_id in checkout session {session_id}")
                return {'success': False, 'error': 'No cart_id in metadata'}

            try:
                cart = StoreCart.objects.get(id=cart_id)
                user = User.objects.get(id=user_id) if user_id else None
            except (StoreCart.DoesNotExist, User.DoesNotExist) as e:
                logger.error(f"Cart or user not found: {str(e)}")
                return {'success': False, 'error': str(e)}

            # Extract amounts from session
            amount_total = data.amount_total or 0
            amount_subtotal = data.amount_subtotal or 0
            total_details = data.total_details or {}
            tax_amount = total_details.get('amount_tax', 0)
            shipping_amount = total_details.get('amount_shipping', 0)

            # Get shipping address
            shipping_address = {}
            if data.shipping_details:
                addr = data.shipping_details.address
                shipping_address = {
                    'name': data.shipping_details.name,
                    'line1': addr.line1,
                    'line2': addr.line2 or '',
                    'city': addr.city,
                    'state': addr.state,
                    'postal_code': addr.postal_code,
                    'country': addr.country,
                }

            # Create order
            order = StoreOrder.objects.create(
                user=user,
                stripe_checkout_session_id=session_id,
                stripe_payment_intent_id=payment_intent_id or '',
                status='paid',
                subtotal_cents=amount_subtotal,
                shipping_cents=shipping_amount,
                tax_cents=tax_amount,
                total_cents=amount_total,
                shipping_address=shipping_address,
                customer_email=customer_email,
                paid_at=timezone.now(),
            )

            # Create order items and update inventory
            for cart_item in cart.items.select_related('product', 'variant'):
                product = cart_item.product
                variant = cart_item.variant

                # Create order item
                order_item = StoreOrderItem.objects.create(
                    order=order,
                    product=product,
                    variant=variant,
                    product_name=product.name,
                    variant_name=variant.name if variant else '',
                    quantity=cart_item.quantity,
                    price_cents=cart_item.unit_price_cents,
                )

                # Reduce inventory for physical products
                if product.product_type == 'physical':
                    if variant:
                        variant.inventory_count = max(0, variant.inventory_count - cart_item.quantity)
                        variant.save()
                    else:
                        product.inventory_count = max(0, product.inventory_count - cart_item.quantity)

                # Update sales count
                product.total_sold += cart_item.quantity
                product.save()

                # Generate download URL for digital products
                if product.product_type == 'digital':
                    download_url = StoreStripeService._generate_download_url(product, order_item)
                    if download_url:
                        order_item.digital_download_url = download_url
                        order_item.download_expires_at = timezone.now() + timedelta(hours=72)
                        order_item.save()

                # Create recent purchase for The Ticker (only for items > $100)
                if cart_item.line_total_cents >= 10000:  # $100 threshold
                    city = shipping_address.get('city', '')
                    country = shipping_address.get('country', '')

                    StoreRecentPurchase.objects.create(
                        user=user,
                        product=product,
                        order=order,
                        city=city,
                        country=country,
                        is_anonymous=True,
                        amount_cents=cart_item.line_total_cents,
                    )

            # Award badges
            if user:
                StoreStripeService._award_badges(user)

            # Clear the cart
            cart.items.all().delete()

            logger.info(f"Order {order.id} created from session {session_id}")

            return {
                'success': True,
                'order_id': order.id,
                'event_type': event_type,
            }

        elif event_type == 'payment_intent.payment_failed':
            payment_intent_id = data.id
            error_message = data.last_payment_error.message if data.last_payment_error else 'Unknown error'

            logger.warning(f"Payment failed for {payment_intent_id}: {error_message}")

            return {
                'success': True,
                'event_type': event_type,
                'error_message': error_message,
            }

        return {'success': True, 'event_type': event_type}

    @staticmethod
    def _generate_download_url(product, order_item) -> Optional[str]:
        """
        Generate a secure, time-limited download URL for digital products.
        Uses AWS S3 presigned URLs.
        """
        from .models import StoreDigitalAsset

        digital_asset = product.digital_assets.first()
        if not digital_asset:
            return None

        # Check if AWS credentials are configured
        aws_access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        aws_secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        aws_bucket = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)

        if not all([aws_access_key, aws_secret_key, aws_bucket]):
            logger.warning("AWS not configured for digital downloads")
            return digital_asset.file_url  # Return direct URL as fallback

        try:
            # Parse S3 key from URL
            file_url = digital_asset.file_url
            if aws_bucket in file_url:
                # Extract key from S3 URL
                s3_key = file_url.split(f'{aws_bucket}/')[1] if f'{aws_bucket}/' in file_url else file_url

                # Create presigned URL
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    config=Config(signature_version='s3v4')
                )

                presigned_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={
                        'Bucket': aws_bucket,
                        'Key': s3_key,
                    },
                    ExpiresIn=digital_asset.expiry_hours * 3600  # Convert hours to seconds
                )

                return presigned_url

            return digital_asset.file_url

        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return digital_asset.file_url

    @staticmethod
    def _award_badges(user):
        """
        Award gamification badges based on purchase history.

        Badge tiers:
        - founder: First purchase
        - bronze_collector: $100+ total spent
        - silver_prospector: $500+ total spent
        - gold_miner: $1000+ total spent
        """
        from .models import StoreOrder, UserStoreBadge
        from django.db.models import Sum

        # Get user's total spending and order count
        stats = StoreOrder.objects.filter(
            user=user,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).aggregate(
            total_spent=Sum('total_cents'),
            order_count=Sum('id')  # This gives us count
        )

        total_spent = stats['total_spent'] or 0
        order_count = StoreOrder.objects.filter(
            user=user,
            status__in=['paid', 'processing', 'shipped', 'delivered']
        ).count()

        badges_to_award = []

        # Founder badge - first purchase
        if order_count == 1:
            badges_to_award.append('founder')

        # Spending tier badges
        if total_spent >= 10000:  # $100
            badges_to_award.append('bronze_collector')
        if total_spent >= 50000:  # $500
            badges_to_award.append('silver_prospector')
        if total_spent >= 100000:  # $1000
            badges_to_award.append('gold_miner')

        # Award badges that user doesn't already have
        for badge_type in badges_to_award:
            UserStoreBadge.objects.get_or_create(
                user=user,
                badge_type=badge_type,
                defaults={
                    'total_spent_cents': total_spent,
                    'order_count': order_count,
                }
            )

    @staticmethod
    def get_order_by_session(session_id: str):
        """Get order by Stripe checkout session ID"""
        from .models import StoreOrder

        try:
            return StoreOrder.objects.get(stripe_checkout_session_id=session_id)
        except StoreOrder.DoesNotExist:
            return None
