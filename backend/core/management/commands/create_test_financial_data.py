from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from core.models import (
    User, Company, Financing, EducationalModule, ModuleCompletion,
    AccreditedInvestorQualification, SubscriptionAgreement,
    InvestmentTransaction, PaymentInstruction, DRSDocument
)


class Command(BaseCommand):
    help = 'Creates comprehensive test data for the Financial Hub'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating test data for Financial Hub...'))

        # Get or create test user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'[OK] Created test user: {user.username}'))
        else:
            self.stdout.write(f'[OK] Using existing user: {user.username}')

        # Get or create admin user
        admin, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )

        # Check if Company model has the fields we need
        company_fields = {
            'name': 'Golden Minerals Corp',
            'ticker_symbol': 'GOLD',
            'description': 'Premier gold mining company with operations in Nevada',
        }

        # Try to add optional fields if they exist
        if hasattr(Company, 'website'):
            company_fields['website'] = 'https://goldenminerals.com'
        if hasattr(Company, 'headquarters'):
            company_fields['headquarters'] = 'Vancouver, BC'
        if hasattr(Company, 'founded_year'):
            company_fields['founded_year'] = 2010
        if hasattr(Company, 'stock_exchange'):
            company_fields['stock_exchange'] = 'TSX-V'

        company, created = Company.objects.get_or_create(
            name='Golden Minerals Corp',
            defaults=company_fields
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created test company: {company.name}'))
        else:
            self.stdout.write(f'[OK] Using existing company: {company.name}')

        # Create test financing round
        financing, created = Financing.objects.get_or_create(
            company=company,
            financing_type='private_placement',
            announced_date=timezone.now().date() - timedelta(days=30),
            defaults={
                'status': 'closing',
                'closing_date': (timezone.now() + timedelta(days=60)).date(),
                'amount_raised_usd': Decimal('5000000.00'),
                'price_per_share': Decimal('2.50'),
                'shares_issued': 2000000,
                'has_warrants': True,
                'warrant_strike_price': Decimal('3.50'),
                'warrant_expiry_date': (timezone.now() + timedelta(days=730)).date(),
                'use_of_proceeds': 'Funds will be used for mine expansion and working capital',
                'lead_agent': 'Canaccord Genuity',
                'notes': 'Series A financing round with 1:1 warrant coverage'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created financing round: {financing.id}'))
        else:
            self.stdout.write(f'[OK] Using existing financing: {financing.id}')

        # Create educational modules
        modules_data = [
            {
                'title': 'Mining Company Financing 101',
                'module_type': 'basics',
                'description': 'Learn the fundamentals of mining company financing',
                'content': '<h2>Introduction to Mining Financing</h2><p>Learn the fundamentals of how mining companies raise capital through equity financing, private placements, and other instruments.</p><h3>Key Topics</h3><ul><li>Types of financing rounds</li><li>Share dilution</li><li>Valuation methods</li><li>Risk factors</li></ul>',
                'estimated_read_time_minutes': 15,
                'sort_order': 1
            },
            {
                'title': 'Canadian Securities Regulations',
                'module_type': 'regulations',
                'description': 'Understanding Canadian securities law and accreditation',
                'content': '<h2>Understanding Canadian Securities Law</h2><p>Overview of securities regulations in Canada, accredited investor requirements, and compliance obligations.</p><h3>Accredited Investor Criteria</h3><p>To qualify as an accredited investor in Canada, you must meet one of several criteria including income thresholds or net asset requirements.</p>',
                'estimated_read_time_minutes': 20,
                'sort_order': 2
            },
            {
                'title': 'Understanding Subscription Agreements',
                'module_type': 'subscription_agreement',
                'description': 'Learn about subscription agreements and investment terms',
                'content': '<h2>What is a Subscription Agreement?</h2><p>A subscription agreement is a legal contract between you and the company outlining investment terms.</p><h3>Key Components</h3><ul><li>Investment amount and share allocation</li><li>Warrant terms (if applicable)</li><li>Payment instructions</li><li>Representations and warranties</li></ul>',
                'estimated_read_time_minutes': 12,
                'sort_order': 3
            },
            {
                'title': 'Direct Registration System (DRS)',
                'module_type': 'drs',
                'description': 'Understanding DRS and direct share ownership',
                'content': '<h2>Understanding DRS</h2><p>The Direct Registration System allows you to hold shares directly with the company, providing proof of ownership without a broker.</p><h3>Benefits</h3><ul><li>Direct ownership</li><li>No broker fees</li><li>Enhanced security</li><li>Voting rights</li></ul>',
                'estimated_read_time_minutes': 10,
                'sort_order': 4
            }
        ]

        for mod_data in modules_data:
            module, created = EducationalModule.objects.get_or_create(
                title=mod_data['title'],
                defaults={
                    **mod_data,
                    'created_by': admin,
                    'is_published': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Created educational module: {module.title}'))

        # Create accredited investor qualification
        qualification, created = AccreditedInvestorQualification.objects.get_or_create(
            user=user,
            defaults={
                'status': 'qualified',
                'criteria_met': 'income_individual',
                'questionnaire_responses': {
                    'employment': 'Self-employed business owner',
                    'investment_experience': '5+ years',
                    'risk_tolerance': 'Moderate to High',
                    'annual_income': 250000
                },
                'qualified_at': timezone.now()
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created qualification for {user.username}: QUALIFIED'))
        else:
            # Update to qualified if it exists
            qualification.status = 'qualified'
            qualification.criteria_met = 'income_individual'
            qualification.qualified_at = timezone.now()
            qualification.save()
            self.stdout.write(f'[OK] Updated qualification: {qualification.status}')

        # Create subscription agreement (investor field is actually a User, not Investor)
        agreement, created = SubscriptionAgreement.objects.get_or_create(
            investor=user,  # This is a User instance
            financing=financing,
            defaults={
                'status': 'signed',
                'total_investment_amount': Decimal('100000.00'),
                'num_shares': 40000,
                'warrant_shares': 40000,
                'warrant_strike_price': Decimal('3.50'),
                'warrant_expiry_date': (timezone.now() + timedelta(days=730)).date(),
                'investor_signed_at': timezone.now() - timedelta(days=5),
                'price_per_share': financing.price_per_share,
                'company': company,
                'currency': 'CAD'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created subscription agreement: #{agreement.id} - ${agreement.total_investment_amount}'))
        else:
            agreement.status = 'signed'
            agreement.num_shares = 40000
            agreement.warrant_shares = 40000
            agreement.investor_signed_at = timezone.now() - timedelta(days=5)
            agreement.save()
            self.stdout.write(f'[OK] Updated existing agreement: #{agreement.id}')

        # Create payment instruction
        from core.models import PaymentInstruction
        payment, created = PaymentInstruction.objects.get_or_create(
            subscription_agreement=agreement,
            defaults={
                'company': company,
                'payment_method': 'wire',
                'bank_name': 'Royal Bank of Canada',
                'bank_account_name': 'Golden Minerals Corp - Trust Account',
                'bank_account_number': '1234567890',
                'routing_number': '00001-003',
                'swift_code': 'ROYCCAT2',
                'reference_code': f'AGR-{agreement.id}-{user.username.upper()}',
                'special_instructions': f'Please include reference code in wire transfer memo. Contact finance@goldenminerals.com with any questions.',
                'sent_to_investor_at': timezone.now() - timedelta(days=3)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'[OK] Created payment instruction: {payment.payment_method}'))
        else:
            self.stdout.write('[OK] Using existing payment instruction')

        # Create investment transactions
        from core.models import InvestmentTransaction
        transactions_data = [
            {
                'amount': Decimal('100000.00'),
                'currency': 'CAD',
                'status': 'completed',
                'payment_method': 'Wire Transfer',
                'payment_reference': 'WIRE-2024-11-25-001',
                'payment_date': timezone.now() - timedelta(days=2),
                'shares_allocated': 40000,
                'price_per_share': financing.price_per_share,
                'completed_at': timezone.now() - timedelta(days=1)
            }
        ]

        for txn_data in transactions_data:
            txn, created = InvestmentTransaction.objects.get_or_create(
                subscription_agreement=agreement,
                user=user,
                financing=financing,
                payment_reference=txn_data['payment_reference'],
                defaults=txn_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Created transaction: {txn.payment_reference} - ${txn.amount}'))

        # Create DRS documents
        from core.models import DRSDocument
        drs_docs_data = [
            {
                'document_type': 'certificate',
                'certificate_number': 'GOLD-C-2024-00001',
                'num_shares': 40000,
                'issue_date': timezone.now().date() - timedelta(days=1),
                'document_url': 'https://storage.goldventure.com/drs/certificates/GOLD-C-2024-00001.pdf',
                'document_hash': 'abc123def456',
                'delivery_status': 'delivered',
                'delivery_method': 'email',
                'sent_at': timezone.now() - timedelta(hours=24),
                'delivered_at': timezone.now() - timedelta(hours=12)
            },
            {
                'document_type': 'statement',
                'certificate_number': 'GOLD-S-2024-00001',
                'num_shares': 40000,
                'issue_date': timezone.now().date(),
                'document_url': 'https://storage.goldventure.com/drs/statements/GOLD-S-2024-00001.pdf',
                'document_hash': 'xyz789ghi012',
                'delivery_status': 'sent',
                'delivery_method': 'email',
                'sent_at': timezone.now() - timedelta(hours=2),
                'delivered_at': None
            }
        ]

        for doc_data in drs_docs_data:
            doc, created = DRSDocument.objects.get_or_create(
                subscription_agreement=agreement,
                user=user,
                company=company,
                certificate_number=doc_data['certificate_number'],
                defaults=doc_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'[OK] Created DRS document: {doc.certificate_number} - {doc.num_shares} shares'))

        # Update agreement status
        agreement.status = 'drs_issued'
        agreement.save()
        self.stdout.write(self.style.SUCCESS(f'[OK] Updated agreement status to: {agreement.status}'))

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('TEST DATA CREATION COMPLETE!'))
        self.stdout.write('='*60)
        self.stdout.write(f'\nLogin Credentials:')
        self.stdout.write(f'  Username: testuser')
        self.stdout.write(f'  Password: testpass123')
        self.stdout.write(f'\nTest Data Summary:')
        self.stdout.write(f'  Company: {company.name} ({company.ticker_symbol})')
        self.stdout.write(f'  Financing Round: #{financing.id} - ${financing.amount_raised_usd}')
        self.stdout.write(f'  Qualification Status: {qualification.status.upper()}')
        self.stdout.write(f'  Subscription Agreement: #{agreement.id} - ${agreement.total_investment_amount}')
        self.stdout.write(f'  Shares Allocated: {agreement.num_shares:,}')
        self.stdout.write(f'  Warrants Allocated: {agreement.warrant_shares:,}')
        self.stdout.write(f'  Transactions: {InvestmentTransaction.objects.filter(subscription_agreement=agreement).count()}')
        self.stdout.write(f'  DRS Documents: {DRSDocument.objects.filter(subscription_agreement=agreement).count()}')
        self.stdout.write(f'  Educational Modules: {EducationalModule.objects.filter(is_published=True).count()}')
        self.stdout.write(f'\nYou can now test the Financial Hub at:')
        self.stdout.write(f'  http://localhost:3000/financial-hub')
        self.stdout.write('='*60)
