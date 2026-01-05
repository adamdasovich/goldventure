"""
Email Notification Utilities
Sends email alerts for important system events like NI 43-101 discoveries and new financings
"""

from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_ni43101_discovery_notification(document, company):
    """
    Send email notification when a new NI 43-101 report is discovered.

    Args:
        document: Document instance (NI 43-101 report)
        company: Company instance
    """
    subject = f'🔔 New NI 43-101 Report Discovered: {company.name}'

    # Email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #D4AF37; margin-top: 0;">New NI 43-101 Report Discovered</h2>

                <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #D4AF37; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Company:</strong> {company.name}</p>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Ticker:</strong> {company.ticker_symbol}</p>' if company.ticker_symbol else ''}
                    <p style="margin: 0 0 10px 0;"><strong>Document Title:</strong> {document.title}</p>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Document Date:</strong> {document.document_date}</p>' if document.document_date else ''}
                    {f'<p style="margin: 0;"><strong>URL:</strong> <a href="{document.file_url}" style="color: #D4AF37;">{document.file_url}</a></p>' if document.file_url else ''}
                </div>

                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    This NI 43-101 report was automatically discovered and will be processed for resource estimates,
                    economic data, and added to the RAG system for chatbot queries.
                </p>

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Junior Mining Intelligence Platform<br>
                        Automated Document Discovery System
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
New NI 43-101 Report Discovered

Company: {company.name}
{'Ticker: ' + company.ticker_symbol if company.ticker_symbol else ''}
Document Title: {document.title}
{'Document Date: ' + str(document.document_date) if document.document_date else ''}
{'URL: ' + document.file_url if document.file_url else ''}

This NI 43-101 report was automatically discovered and will be processed for resource estimates,
economic data, and added to the RAG system for chatbot queries.

---
Junior Mining Intelligence Platform
Automated Document Discovery System
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.NI43101_NOTIFICATION_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✉️  Sent NI 43-101 discovery notification for {company.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to send NI 43-101 notification: {str(e)}")
        return False


def send_financing_flag_notification(flag, company, news_release):
    """
    Send email notification when a news release is flagged for potential financing.

    Args:
        flag: NewsReleaseFlag instance
        company: Company instance
        news_release: NewsRelease instance
    """
    subject = f'🚩 Financing Alert: {company.name} - News Release Flagged'

    # Email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #D4AF37; margin-top: 0;">🚩 Potential Financing Detected</h2>

                <div style="background-color: #fff9e6; padding: 20px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Company:</strong> {company.name}</p>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Ticker:</strong> {company.ticker_symbol}</p>' if company.ticker_symbol else ''}
                    <p style="margin: 0 0 10px 0;"><strong>News Title:</strong> {news_release.title}</p>
                    <p style="margin: 0 0 10px 0;"><strong>Release Date:</strong> {news_release.release_date}</p>
                    <p style="margin: 0;"><strong>URL:</strong> <a href="{news_release.url}" style="color: #D4AF37;">{news_release.url}</a></p>
                </div>

                <div style="margin: 20px 0;">
                    <p style="margin: 0 0 10px 0; color: #856404;"><strong>Detected Keywords:</strong></p>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        {''.join([f'<span style="display: inline-block; padding: 4px 12px; background-color: #D4AF37; color: white; border-radius: 4px; font-size: 14px; margin-right: 8px; margin-bottom: 8px;">{kw}</span>' for kw in flag.detected_keywords])}
                    </div>
                </div>

                <div style="background-color: #e3f2fd; padding: 15px; border-left: 4px solid #2196F3; margin: 20px 0;">
                    <p style="margin: 0; color: #1565C0;"><strong>⚡ Action Required:</strong></p>
                    <p style="margin: 5px 0 0 0; color: #1565C0; font-size: 14px;">
                        Review this news release at <a href="https://juniorgoldminingintelligence.com/admin/news-flags" style="color: #1565C0; text-decoration: underline;">Admin Panel → News Flags</a>
                    </p>
                </div>

                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    This news release was automatically flagged by the financing detection system based on keywords in the title.
                    Please review and confirm if this represents an actual financing announcement.
                </p>

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Junior Mining Intelligence Platform<br>
                        Automated Financing Detection System
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
🚩 Potential Financing Detected

Company: {company.name}
{'Ticker: ' + company.ticker_symbol if company.ticker_symbol else ''}
News Title: {news_release.title}
Release Date: {news_release.release_date}
URL: {news_release.url}

Detected Keywords: {', '.join(flag.detected_keywords)}

⚡ Action Required:
Review this news release at: https://juniorgoldminingintelligence.com/admin/news-flags

This news release was automatically flagged by the financing detection system based on keywords in the title.
Please review and confirm if this represents an actual financing announcement.

---
Junior Mining Intelligence Platform
Automated Financing Detection System
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.FINANCING_NOTIFICATION_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✉️  Sent financing flag notification for {company.name}")
        return True
    except Exception as e:
        print(f"❌ Failed to send financing flag notification: {str(e)}")
        return False


def send_financing_created_notification(financing, company, news_release=None):
    """
    Send email notification when a new financing is created.

    Args:
        financing: Financing instance
        company: Company instance
        news_release: Optional NewsRelease instance (if created from flagged news)
    """
    subject = f'💰 New Financing Created: {company.name} - ${financing.amount_raised_usd:,.0f}'

    # Format financing details
    financing_type = financing.get_financing_type_display()
    status = financing.get_status_display()

    # Email content
    html_message = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
            <div style="background-color: #ffffff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h2 style="color: #D4AF37; margin-top: 0;">New Financing Created</h2>

                <div style="background-color: #f9f9f9; padding: 20px; border-left: 4px solid #D4AF37; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Company:</strong> {company.name}</p>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Ticker:</strong> {company.ticker_symbol}</p>' if company.ticker_symbol else ''}
                    <p style="margin: 0 0 10px 0;"><strong>Financing Type:</strong> {financing_type}</p>
                    <p style="margin: 0 0 10px 0;"><strong>Status:</strong> {status}</p>
                    <p style="margin: 0 0 10px 0;"><strong>Amount Raised:</strong> ${financing.amount_raised_usd:,.2f} USD</p>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Price Per Share:</strong> ${financing.price_per_share}</p>' if financing.price_per_share else ''}
                    {f'<p style="margin: 0 0 10px 0;"><strong>Shares Issued:</strong> {financing.shares_issued:,}</p>' if financing.shares_issued else ''}
                    <p style="margin: 0 0 10px 0;"><strong>Announced Date:</strong> {financing.announced_date}</p>
                    {f'<p style="margin: 0 0 10px 0;"><strong>Closing Date:</strong> {financing.closing_date}</p>' if financing.closing_date else ''}
                    {f'<p style="margin: 0 0 10px 0;"><strong>Lead Agent:</strong> {financing.lead_agent}</p>' if financing.lead_agent else ''}
                    {f'<p style="margin: 0;"><strong>Has Warrants:</strong> Yes (Strike: ${financing.warrant_strike_price})</p>' if financing.has_warrants else '<p style="margin: 0;"><strong>Has Warrants:</strong> No</p>'}
                </div>

                {f'''
                <div style="background-color: #fff9e6; padding: 15px; border-left: 4px solid #ffc107; margin: 20px 0;">
                    <p style="margin: 0 0 10px 0; color: #856404;"><strong>📰 Source:</strong></p>
                    <p style="margin: 0; font-size: 14px;">{news_release.title}</p>
                    <p style="margin: 5px 0 0 0;"><a href="{news_release.url}" style="color: #D4AF37; font-size: 14px;">View News Release →</a></p>
                </div>
                ''' if news_release else ''}

                {f'''
                <div style="margin: 20px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Use of Proceeds:</strong></p>
                    <p style="margin: 0; color: #666; font-size: 14px;">{financing.use_of_proceeds}</p>
                </div>
                ''' if financing.use_of_proceeds else ''}

                {f'''
                <div style="margin: 20px 0;">
                    <p style="margin: 0 0 10px 0;"><strong>Notes:</strong></p>
                    <p style="margin: 0; color: #666; font-size: 14px;">{financing.notes}</p>
                </div>
                ''' if financing.notes else ''}

                <p style="color: #666; font-size: 14px; margin-top: 20px;">
                    {'This financing was automatically detected from a news release and confirmed by a superuser.' if news_release else 'This financing was manually created by a superuser.'}
                </p>

                <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <p style="color: #999; font-size: 12px; margin: 0;">
                        Junior Mining Intelligence Platform<br>
                        {'Automated Financing Detection System' if news_release else 'Financing Management System'}
                    </p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    plain_message = f"""
New Financing Created

Company: {company.name}
{'Ticker: ' + company.ticker_symbol if company.ticker_symbol else ''}
Financing Type: {financing_type}
Status: {status}
Amount Raised: ${financing.amount_raised_usd:,.2f} USD
{'Price Per Share: $' + str(financing.price_per_share) if financing.price_per_share else ''}
{'Shares Issued: ' + f'{financing.shares_issued:,}' if financing.shares_issued else ''}
Announced Date: {financing.announced_date}
{'Closing Date: ' + str(financing.closing_date) if financing.closing_date else ''}
{'Lead Agent: ' + financing.lead_agent if financing.lead_agent else ''}
Has Warrants: {'Yes (Strike: $' + str(financing.warrant_strike_price) + ')' if financing.has_warrants else 'No'}

{f'''
Source News Release:
{news_release.title}
{news_release.url}
''' if news_release else ''}

{'Use of Proceeds: ' + financing.use_of_proceeds if financing.use_of_proceeds else ''}

{'Notes: ' + financing.notes if financing.notes else ''}

{'This financing was automatically detected from a news release and confirmed by a superuser.' if news_release else 'This financing was manually created by a superuser.'}

---
Junior Mining Intelligence Platform
{'Automated Financing Detection System' if news_release else 'Financing Management System'}
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.FINANCING_NOTIFICATION_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✉️  Sent financing notification for {company.name} - ${financing.amount_raised_usd:,.0f}")
        return True
    except Exception as e:
        print(f"❌ Failed to send financing notification: {str(e)}")
        return False
