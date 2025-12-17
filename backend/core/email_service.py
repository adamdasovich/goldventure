"""
Email Service for GoldVenture Platform

Handles sending transactional emails for:
- Order confirmations
- Shipping notifications
- Digital download links
"""

import logging
import threading
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for sending transactional emails"""

    @staticmethod
    def is_configured():
        """Check if email is properly configured"""
        return bool(settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD)

    @staticmethod
    def send_order_confirmation(order):
        """
        Send order confirmation email after successful purchase.
        Runs in a background thread to avoid blocking the webhook response.

        Args:
            order: StoreOrder instance with items prefetched
        """
        if not EmailService.is_configured():
            logger.warning("Email not configured, skipping order confirmation email")
            return False

        # Get recipient email
        recipient_email = order.customer_email
        if not recipient_email and order.user:
            recipient_email = order.user.email

        if not recipient_email:
            logger.warning(f"No email address for order {order.id}")
            return False

        # Build context before spawning thread (to avoid lazy loading issues)
        try:
            context = EmailService._build_order_context(order)
        except Exception as e:
            logger.error(f"Failed to build email context for order {order.id}: {str(e)}")
            return False

        # Send email in background thread
        def send_email_thread():
            try:
                html_content = EmailService._render_order_confirmation_html(context)
                text_content = strip_tags(html_content)

                subject = f"Order Confirmation - #{context['order_id']}"
                from_email = settings.DEFAULT_FROM_EMAIL

                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[recipient_email],
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)

                logger.info(f"Order confirmation email sent for order {context['order_id']} to {recipient_email}")

            except Exception as e:
                logger.error(f"Failed to send order confirmation email for order {context['order_id']}: {str(e)}")

        # Start background thread
        thread = threading.Thread(target=send_email_thread, daemon=True)
        thread.start()

        logger.info(f"Order confirmation email queued for order {order.id}")
        return True

    @staticmethod
    def _build_order_context(order):
        """Build context dictionary for order email templates"""
        items = []
        has_digital = False
        has_physical = False

        for item in order.items.all():
            item_data = {
                'name': item.product_name,
                'variant': item.variant_name,
                'quantity': item.quantity,
                'unit_price': item.price_cents / 100,
                'total': item.line_total_cents / 100,
                'is_digital': bool(item.digital_download_url),
                'download_url': item.digital_download_url,
            }
            items.append(item_data)

            if item.digital_download_url:
                has_digital = True
            else:
                has_physical = True

        # Format shipping address
        shipping_address = None
        if order.shipping_address and isinstance(order.shipping_address, dict):
            addr = order.shipping_address
            if addr.get('line1'):
                shipping_address = {
                    'name': addr.get('name', ''),
                    'line1': addr.get('line1', ''),
                    'line2': addr.get('line2', ''),
                    'city': addr.get('city', ''),
                    'state': addr.get('state', ''),
                    'postal_code': addr.get('postal_code', ''),
                    'country': addr.get('country', ''),
                }

        return {
            'order_id': order.id,
            'order_date': order.created_at,
            'items': items,
            'subtotal': order.subtotal_cents / 100,
            'shipping': order.shipping_cents / 100,
            'tax': order.tax_cents / 100,
            'total': order.total_cents / 100,
            'shipping_address': shipping_address,
            'has_digital': has_digital,
            'has_physical': has_physical,
            'tracking_number': order.tracking_number,
            'customer_name': order.shipping_address.get('name', '') if order.shipping_address else '',
            'site_url': 'https://juniorgoldminingintelligence.com',
        }

    @staticmethod
    def _render_order_confirmation_html(context):
        """Render order confirmation email as HTML"""
        # Inline HTML template for better email client compatibility
        items_html = ""
        for item in context['items']:
            variant_text = f" - {item['variant']}" if item['variant'] else ""
            download_link = ""
            if item['is_digital'] and item['download_url']:
                download_link = f'''
                    <div style="margin-top: 8px;">
                        <a href="{item['download_url']}" style="color: #D4AF37; text-decoration: none; font-size: 14px;">
                            📥 Download Now
                        </a>
                    </div>
                '''

            items_html += f'''
                <tr>
                    <td style="padding: 16px 0; border-bottom: 1px solid #334155;">
                        <div style="font-weight: 500; color: #F1F5F9;">{item['name']}{variant_text}</div>
                        <div style="font-size: 14px; color: #94A3B8; margin-top: 4px;">
                            Qty: {item['quantity']} × ${item['unit_price']:.2f}
                        </div>
                        {download_link}
                    </td>
                    <td style="padding: 16px 0; border-bottom: 1px solid #334155; text-align: right; color: #F1F5F9; font-weight: 500;">
                        ${item['total']:.2f}
                    </td>
                </tr>
            '''

        # Shipping address section
        shipping_html = ""
        if context['has_physical'] and context['shipping_address']:
            addr = context['shipping_address']
            shipping_html = f'''
                <div style="margin-top: 32px; padding-top: 24px; border-top: 1px solid #334155;">
                    <h3 style="color: #D4AF37; font-size: 16px; margin: 0 0 12px 0;">Shipping Address</h3>
                    <div style="color: #94A3B8; font-size: 14px; line-height: 1.6;">
                        <div>{addr['name']}</div>
                        <div>{addr['line1']}</div>
                        {'<div>' + addr['line2'] + '</div>' if addr['line2'] else ''}
                        <div>{addr['city']}, {addr['state']} {addr['postal_code']}</div>
                        <div>{addr['country']}</div>
                    </div>
                </div>
            '''

        # Digital downloads notice
        digital_notice = ""
        if context['has_digital']:
            digital_notice = '''
                <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #D4AF37; border-radius: 8px; padding: 16px; margin-top: 24px;">
                    <div style="color: #D4AF37; font-weight: 600; margin-bottom: 8px;">📚 Digital Downloads Ready</div>
                    <div style="color: #94A3B8; font-size: 14px;">
                        Your digital items are available for immediate download. Click the download links above or visit your
                        <a href="https://juniorgoldminingintelligence.com/account/orders" style="color: #D4AF37;">orders page</a>.
                    </div>
                </div>
            '''

        # Shipping row
        shipping_row = ""
        if context['shipping'] > 0:
            shipping_row = f'''
                <tr>
                    <td style="padding: 8px 0; color: #94A3B8;">Shipping</td>
                    <td style="padding: 8px 0; text-align: right; color: #94A3B8;">${context['shipping']:.2f}</td>
                </tr>
            '''

        # Tax row
        tax_row = ""
        if context['tax'] > 0:
            tax_row = f'''
                <tr>
                    <td style="padding: 8px 0; color: #94A3B8;">Tax</td>
                    <td style="padding: 8px 0; text-align: right; color: #94A3B8;">${context['tax']:.2f}</td>
                </tr>
            '''

        html = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Confirmation</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0F172A;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px;">

                    <!-- Header -->
                    <tr>
                        <td style="text-align: center; padding-bottom: 32px;">
                            <div style="font-size: 24px; font-weight: 700; color: #D4AF37; letter-spacing: 1px;">
                                JUNIOR GOLD MINING INTELLIGENCE
                            </div>
                        </td>
                    </tr>

                    <!-- Main Card -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-radius: 16px; padding: 32px;">

                            <!-- Success Icon -->
                            <div style="text-align: center; margin-bottom: 24px;">
                                <div style="display: inline-block; width: 64px; height: 64px; background: linear-gradient(135deg, #D4AF37 0%, #B8860B 100%); border-radius: 50%; line-height: 64px; font-size: 32px;">
                                    ✓
                                </div>
                            </div>

                            <!-- Title -->
                            <h1 style="color: #F1F5F9; font-size: 28px; text-align: center; margin: 0 0 8px 0;">
                                Thank You for Your Order!
                            </h1>
                            <p style="color: #94A3B8; text-align: center; margin: 0 0 32px 0;">
                                Order #{context['order_id']} has been confirmed
                            </p>

                            <!-- Order Items -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <thead>
                                    <tr>
                                        <th style="text-align: left; color: #64748B; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 12px; border-bottom: 1px solid #334155;">Item</th>
                                        <th style="text-align: right; color: #64748B; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; padding-bottom: 12px; border-bottom: 1px solid #334155;">Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items_html}
                                </tbody>
                            </table>

                            <!-- Order Summary -->
                            <div style="margin-top: 24px; padding-top: 16px; border-top: 2px solid #334155;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                    <tr>
                                        <td style="padding: 8px 0; color: #94A3B8;">Subtotal</td>
                                        <td style="padding: 8px 0; text-align: right; color: #94A3B8;">${context['subtotal']:.2f}</td>
                                    </tr>
                                    {shipping_row}
                                    {tax_row}
                                    <tr>
                                        <td style="padding: 16px 0 0 0; color: #F1F5F9; font-size: 18px; font-weight: 600; border-top: 1px solid #334155;">Total</td>
                                        <td style="padding: 16px 0 0 0; text-align: right; color: #D4AF37; font-size: 18px; font-weight: 600; border-top: 1px solid #334155;">${context['total']:.2f}</td>
                                    </tr>
                                </table>
                            </div>

                            {digital_notice}
                            {shipping_html}

                            <!-- CTA Button -->
                            <div style="text-align: center; margin-top: 32px;">
                                <a href="https://juniorgoldminingintelligence.com/account/orders"
                                   style="display: inline-block; background: linear-gradient(135deg, #D4AF37 0%, #B8860B 100%); color: #0F172A; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600; font-size: 16px;">
                                    View Your Orders
                                </a>
                            </div>

                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="text-align: center; padding-top: 32px;">
                            <p style="color: #64748B; font-size: 14px; margin: 0 0 8px 0;">
                                Questions about your order? Contact us at support@juniorgoldminingintelligence.com
                            </p>
                            <p style="color: #475569; font-size: 12px; margin: 0;">
                                © 2025 Junior Gold Mining Intelligence. All rights reserved.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        '''

        return html

    @staticmethod
    def send_shipping_notification(order):
        """
        Send shipping notification email when order is shipped.

        Args:
            order: StoreOrder instance with tracking information
        """
        if not EmailService.is_configured():
            logger.warning("Email not configured, skipping shipping notification email")
            return False

        recipient_email = order.customer_email
        if not recipient_email and order.user:
            recipient_email = order.user.email

        if not recipient_email:
            logger.warning(f"No email address for order {order.id}")
            return False

        try:
            subject = f"Your Order #{order.id} Has Shipped!"
            from_email = settings.DEFAULT_FROM_EMAIL

            # Simple shipping notification
            html_content = f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #0F172A; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0F172A;">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width: 600px;">
                    <tr>
                        <td style="text-align: center; padding-bottom: 32px;">
                            <div style="font-size: 24px; font-weight: 700; color: #D4AF37;">JUNIOR GOLD MINING INTELLIGENCE</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); border: 1px solid #334155; border-radius: 16px; padding: 32px; text-align: center;">
                            <div style="font-size: 48px; margin-bottom: 16px;">📦</div>
                            <h1 style="color: #F1F5F9; font-size: 28px; margin: 0 0 16px 0;">Your Order Has Shipped!</h1>
                            <p style="color: #94A3B8; margin: 0 0 24px 0;">Order #{order.id} is on its way to you.</p>

                            {f'<div style="background: #0F172A; border: 1px solid #334155; border-radius: 8px; padding: 16px; margin-bottom: 24px;"><div style="color: #64748B; font-size: 12px; text-transform: uppercase; margin-bottom: 8px;">Tracking Number</div><div style="color: #D4AF37; font-family: monospace; font-size: 18px;">{order.tracking_number}</div></div>' if order.tracking_number else ''}

                            <a href="https://juniorgoldminingintelligence.com/account/orders" style="display: inline-block; background: linear-gradient(135deg, #D4AF37 0%, #B8860B 100%); color: #0F172A; text-decoration: none; padding: 14px 32px; border-radius: 8px; font-weight: 600;">
                                Track Your Order
                            </a>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
            '''

            text_content = strip_tags(html_content)

            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient_email],
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)

            logger.info(f"Shipping notification email sent for order {order.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to send shipping notification for order {order.id}: {str(e)}")
            return False
