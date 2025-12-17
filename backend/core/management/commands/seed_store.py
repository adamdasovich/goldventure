"""
Management command to seed the store with sample products.
Run: python manage.py seed_store
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import (
    StoreCategory,
    StoreProduct,
    StoreProductImage,
    StoreProductVariant,
    StoreDigitalAsset,
    StoreShippingRate,
)


class Command(BaseCommand):
    help = 'Seed the store with sample categories and products'

    def handle(self, *args, **options):
        self.stdout.write('Seeding store data...')

        # Create shipping rates
        self.create_shipping_rates()

        # Create categories
        categories = self.create_categories()

        # Create products for each category
        self.create_vault_products(categories['the-vault'])
        self.create_gear_products(categories['field-gear'])
        self.create_library_products(categories['resource-library'])

        self.stdout.write(self.style.SUCCESS('Store seeded successfully!'))

    def create_shipping_rates(self):
        """Create shipping rate tiers"""
        rates = [
            {
                'name': 'Standard Shipping',
                'min_weight_grams': 0,
                'max_weight_grams': 50000,
                'price_cents': 999,
                'estimated_days_min': 5,
                'estimated_days_max': 7,
            },
            {
                'name': 'Expedited Shipping',
                'min_weight_grams': 0,
                'max_weight_grams': 50000,
                'price_cents': 1999,
                'estimated_days_min': 3,
                'estimated_days_max': 5,
            },
            {
                'name': 'Express Shipping',
                'min_weight_grams': 0,
                'max_weight_grams': 50000,
                'price_cents': 3999,
                'estimated_days_min': 1,
                'estimated_days_max': 2,
            },
        ]

        for rate_data in rates:
            StoreShippingRate.objects.update_or_create(
                name=rate_data['name'],
                defaults=rate_data
            )
        self.stdout.write(f'  Created {len(rates)} shipping rates')

    def create_categories(self):
        """Create store categories"""
        categories_data = [
            {
                'name': 'The Vault',
                'slug': 'the-vault',
                'description': 'Rare specimens, collectible bullion, and premium geological artifacts',
                'display_order': 1,
                'icon': 'vault',
            },
            {
                'name': 'Field Gear',
                'slug': 'field-gear',
                'description': 'Essential equipment and apparel for prospectors and geologists',
                'display_order': 2,
                'icon': 'pickaxe',
            },
            {
                'name': 'Resource Library',
                'slug': 'resource-library',
                'description': 'Educational materials, maps, and digital downloads',
                'display_order': 3,
                'icon': 'book',
            },
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = StoreCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = category

        self.stdout.write(f'  Created {len(categories)} categories')
        return categories

    def create_vault_products(self, category):
        """Create premium vault products"""
        products = [
            {
                'name': 'The Core Sample Series - Carlin Trend',
                'slug': 'core-sample-carlin-trend',
                'short_description': 'Authentic drill core from the legendary Carlin Trend gold deposit',
                'description': '''
                    <h3>A Piece of Mining History</h3>
                    <p>Own a piece of one of the most significant gold discoveries in North American history.
                    This authenticated drill core sample comes from the Carlin Trend in Nevada, which has
                    produced over 90 million ounces of gold since its discovery.</p>

                    <h4>Specifications</h4>
                    <ul>
                        <li>Length: 6 inches (15 cm)</li>
                        <li>Diameter: 2 inches (HQ core)</li>
                        <li>Encased in museum-quality resin block</li>
                        <li>Includes certificate of authenticity</li>
                        <li>Display stand included</li>
                    </ul>

                    <h4>Geological Significance</h4>
                    <p>This sample showcases the characteristic sediment-hosted gold mineralization
                    that made Carlin-type deposits famous worldwide.</p>
                ''',
                'price_cents': 249900,
                'compare_at_price_cents': 299900,
                'product_type': 'physical',
                'sku': 'VLT-CORE-001',
                'inventory_count': 12,
                'weight_grams': 850,
                'is_featured': True,
                'badges': ['rare', 'limited_edition'],
                'provenance_info': 'Sample authenticated by Nevada Bureau of Mines and Geology. Certificate #NV-2024-0847.',
                'authentication_docs': ['Certificate of Authenticity', 'Geological Analysis Report', 'Chain of Custody Documentation'],
            },
            {
                'name': 'Limited Edition Gold Buffalo Round',
                'slug': 'gold-buffalo-round-1oz',
                'short_description': '1 oz .9999 fine gold commemorative round - GoldVenture exclusive',
                'description': '''
                    <h3>GoldVenture Exclusive Mintage</h3>
                    <p>A stunning 1 oz gold round featuring the iconic American Buffalo design,
                    exclusively minted for the GoldVenture community. Only 500 pieces worldwide.</p>

                    <h4>Specifications</h4>
                    <ul>
                        <li>Weight: 1 Troy Ounce (31.1g)</li>
                        <li>Purity: .9999 Fine Gold</li>
                        <li>Diameter: 32.7mm</li>
                        <li>Thickness: 2.87mm</li>
                        <li>Mintage: 500 pieces</li>
                    </ul>

                    <p>Each round is individually numbered and comes with a certificate of authenticity.</p>
                ''',
                'price_cents': 289500,
                'product_type': 'physical',
                'sku': 'VLT-GOLD-001',
                'inventory_count': 47,
                'weight_grams': 31,
                'is_featured': True,
                'badges': ['limited_edition', 'new_arrival'],
                'authentication_docs': ['Assay Certificate', 'Certificate of Authenticity'],
            },
            {
                'name': 'Historic Assay Report Collection',
                'slug': 'historic-assay-collection',
                'short_description': 'Framed collection of original 1890s Comstock Lode assay reports',
                'description': '''
                    <h3>Window into Mining History</h3>
                    <p>This remarkable collection includes five original assay reports from the
                    Comstock Lode mining district, dating from 1892-1897. Each document has been
                    professionally preserved and framed.</p>

                    <h4>Collection Includes</h4>
                    <ul>
                        <li>Five original handwritten assay reports</li>
                        <li>Professional museum-quality framing</li>
                        <li>Historical context documentation</li>
                        <li>Conservation certificate</li>
                    </ul>
                ''',
                'price_cents': 175000,
                'product_type': 'physical',
                'sku': 'VLT-HIST-001',
                'inventory_count': 3,
                'weight_grams': 2500,
                'is_featured': False,
                'badges': ['rare'],
                'provenance_info': 'Documents acquired from the estate of mining engineer Robert Harrison. Authenticated by the Nevada Historical Society.',
            },
            {
                'name': 'Native Gold Specimen - Motherlode',
                'slug': 'native-gold-specimen-motherlode',
                'short_description': 'Museum-quality crystalline gold specimen from California Motherlode',
                'description': '''
                    <h3>Exceptional Crystalline Gold</h3>
                    <p>A truly exceptional specimen of native gold displaying beautiful
                    crystalline structure. Sourced from the historic California Motherlode region.</p>

                    <h4>Specifications</h4>
                    <ul>
                        <li>Gold Weight: Approximately 12.4 grams</li>
                        <li>Total Specimen Weight: 28 grams (with matrix)</li>
                        <li>Dimensions: 35mm x 25mm x 18mm</li>
                        <li>Crystal habit: Octahedral with modifications</li>
                    </ul>
                ''',
                'price_cents': 850000,
                'product_type': 'physical',
                'sku': 'VLT-SPEC-001',
                'inventory_count': 1,
                'weight_grams': 28,
                'is_featured': True,
                'badges': ['rare', 'community_favorite'],
                'min_price_for_inquiry': 500000,
                'provenance_info': 'Specimen from the collection of Dr. James Mitchell, Stanford University Geology Department.',
                'authentication_docs': ['Gemological Institute Report', 'XRF Analysis', 'Provenance Documentation'],
            },
        ]

        self._create_products(category, products)
        self.stdout.write(f'  Created {len(products)} Vault products')

    def create_gear_products(self, category):
        """Create field gear products"""
        products = [
            {
                'name': 'GoldVenture Prospector Hat',
                'slug': 'gv-prospector-hat',
                'short_description': 'Premium wide-brim field hat with UPF 50+ protection',
                'description': '''
                    <h3>Built for the Field</h3>
                    <p>Our signature prospector hat combines classic style with modern sun protection.
                    Perfect for long days in the field.</p>

                    <h4>Features</h4>
                    <ul>
                        <li>UPF 50+ sun protection</li>
                        <li>Moisture-wicking sweatband</li>
                        <li>Adjustable chin cord</li>
                        <li>Ventilated crown</li>
                        <li>Embroidered GoldVenture logo</li>
                    </ul>
                ''',
                'price_cents': 4999,
                'product_type': 'physical',
                'sku': 'GR-HAT-001',
                'inventory_count': 150,
                'weight_grams': 180,
                'is_featured': True,
                'badges': ['community_favorite'],
                'variants': [
                    {'name': 'Small/Medium', 'sku': 'GR-HAT-001-SM', 'inventory_count': 50},
                    {'name': 'Large/XL', 'sku': 'GR-HAT-001-LX', 'inventory_count': 100},
                ],
            },
            {
                'name': 'Stake Your Claim T-Shirt',
                'slug': 'stake-your-claim-tshirt',
                'short_description': 'Premium cotton tee with vintage mining artwork',
                'description': '''
                    <h3>Stake Your Claim</h3>
                    <p>Show your prospector spirit with this premium cotton t-shirt featuring
                    our exclusive vintage-style mining artwork.</p>

                    <h4>Details</h4>
                    <ul>
                        <li>100% ring-spun cotton</li>
                        <li>Pre-shrunk fabric</li>
                        <li>Vintage-style screen print</li>
                        <li>Relaxed fit</li>
                    </ul>
                ''',
                'price_cents': 3499,
                'product_type': 'physical',
                'sku': 'GR-TEE-001',
                'inventory_count': 200,
                'weight_grams': 200,
                'is_featured': False,
                'badges': ['new_arrival'],
                'variants': [
                    {'name': 'Small', 'sku': 'GR-TEE-001-S', 'inventory_count': 40},
                    {'name': 'Medium', 'sku': 'GR-TEE-001-M', 'inventory_count': 60},
                    {'name': 'Large', 'sku': 'GR-TEE-001-L', 'inventory_count': 60},
                    {'name': 'XL', 'sku': 'GR-TEE-001-XL', 'inventory_count': 40},
                ],
            },
            {
                'name': 'Professional Gold Pan Kit',
                'slug': 'professional-gold-pan-kit',
                'short_description': 'Complete 7-piece gold panning kit for serious prospectors',
                'description': '''
                    <h3>Everything You Need to Start Panning</h3>
                    <p>Our professional-grade kit includes everything needed for successful gold panning,
                    from beginner to experienced prospector.</p>

                    <h4>Kit Includes</h4>
                    <ul>
                        <li>14" professional gold pan with riffles</li>
                        <li>10" finishing pan</li>
                        <li>Classifier screen set (3 sizes)</li>
                        <li>Snuffer bottle</li>
                        <li>Glass vials (5 pack)</li>
                        <li>Instructional guide</li>
                        <li>Carrying mesh bag</li>
                    </ul>
                ''',
                'price_cents': 8999,
                'compare_at_price_cents': 11999,
                'product_type': 'physical',
                'sku': 'GR-PAN-001',
                'inventory_count': 75,
                'weight_grams': 1200,
                'is_featured': True,
                'badges': ['community_favorite'],
            },
            {
                'name': 'Geologist Field Notebook',
                'slug': 'geologist-field-notebook',
                'short_description': 'Weatherproof field notebook with geological reference pages',
                'description': '''
                    <h3>Built for the Elements</h3>
                    <p>Our field notebook is designed to withstand the rigors of geological fieldwork
                    while keeping your observations organized and accessible.</p>

                    <h4>Features</h4>
                    <ul>
                        <li>Waterproof synthetic paper</li>
                        <li>Grid and blank pages</li>
                        <li>Geological reference section</li>
                        <li>Mohs hardness scale</li>
                        <li>Rock identification guide</li>
                        <li>Lay-flat binding</li>
                    </ul>
                ''',
                'price_cents': 2499,
                'product_type': 'physical',
                'sku': 'GR-NB-001',
                'inventory_count': 300,
                'weight_grams': 150,
                'is_featured': False,
                'badges': [],
            },
            {
                'name': 'Specimen Collection Starter Kit',
                'slug': 'specimen-collection-starter',
                'short_description': '12-piece mineral and ore specimen collection for learning',
                'description': '''
                    <h3>Start Your Collection</h3>
                    <p>An excellent introduction to mineral and ore identification.
                    Each specimen is labeled and includes an identification card.</p>

                    <h4>Collection Includes</h4>
                    <ul>
                        <li>Native Gold (California)</li>
                        <li>Native Silver (Mexico)</li>
                        <li>Pyrite (Peru)</li>
                        <li>Chalcopyrite (Arizona)</li>
                        <li>Galena (Missouri)</li>
                        <li>Sphalerite (Tennessee)</li>
                        <li>Malachite (Congo)</li>
                        <li>Azurite (Arizona)</li>
                        <li>Quartz Crystal (Arkansas)</li>
                        <li>Magnetite (Utah)</li>
                        <li>Hematite (Michigan)</li>
                        <li>Cassiterite (Bolivia)</li>
                    </ul>
                ''',
                'price_cents': 12999,
                'product_type': 'physical',
                'sku': 'GR-SPEC-001',
                'inventory_count': 50,
                'weight_grams': 800,
                'is_featured': True,
                'badges': ['new_arrival'],
            },
        ]

        self._create_products(category, products)
        self.stdout.write(f'  Created {len(products)} Field Gear products')

    def create_library_products(self, category):
        """Create resource library products"""
        products = [
            {
                'name': 'Complete Gold Prospecting Guide',
                'slug': 'gold-prospecting-guide-ebook',
                'short_description': 'Comprehensive digital guide covering all aspects of gold prospecting',
                'description': '''
                    <h3>Master the Art of Gold Prospecting</h3>
                    <p>Our most comprehensive guide covers everything from basic panning techniques
                    to advanced placer mining methods. Written by experienced prospectors.</p>

                    <h4>Topics Covered</h4>
                    <ul>
                        <li>Gold geology fundamentals</li>
                        <li>Reading the landscape</li>
                        <li>Panning techniques</li>
                        <li>Sluicing and dredging</li>
                        <li>Claim staking and regulations</li>
                        <li>Equipment selection</li>
                        <li>Safety considerations</li>
                    </ul>

                    <p><strong>Format:</strong> PDF, 285 pages</p>
                ''',
                'price_cents': 2999,
                'product_type': 'digital',
                'sku': 'LIB-EBK-001',
                'inventory_count': 999,
                'is_featured': True,
                'badges': ['community_favorite'],
                'digital_assets': [
                    {
                        'file_name': 'gold-prospecting-guide-v2.pdf',
                        'file_size_bytes': 45000000,
                        'download_limit': 5,
                        'expiry_hours': 720,
                    }
                ],
            },
            {
                'name': 'Nevada Gold Districts Map Collection',
                'slug': 'nevada-gold-districts-maps',
                'short_description': 'High-resolution digital maps of major Nevada gold districts',
                'description': '''
                    <h3>Detailed Mining District Maps</h3>
                    <p>A collection of professionally prepared maps covering the major
                    gold-producing districts of Nevada.</p>

                    <h4>Included Maps</h4>
                    <ul>
                        <li>Carlin Trend Overview</li>
                        <li>Battle Mountain-Eureka Trend</li>
                        <li>Getchell Trend</li>
                        <li>Walker Lane Belt</li>
                        <li>Historical Comstock Region</li>
                    </ul>

                    <p><strong>Format:</strong> High-resolution PDF (300 DPI, suitable for printing)</p>
                ''',
                'price_cents': 4999,
                'product_type': 'digital',
                'sku': 'LIB-MAP-001',
                'inventory_count': 999,
                'is_featured': True,
                'badges': ['new_arrival'],
                'digital_assets': [
                    {
                        'file_name': 'nevada-gold-districts-maps.zip',
                        'file_size_bytes': 125000000,
                        'download_limit': 3,
                        'expiry_hours': 720,
                    }
                ],
            },
            {
                'name': 'Introduction to Economic Geology',
                'slug': 'intro-economic-geology-course',
                'short_description': 'Self-paced video course on mineral deposit formation',
                'description': '''
                    <h3>Understand How Ore Deposits Form</h3>
                    <p>This comprehensive video course teaches the geological processes
                    that create economically significant mineral deposits.</p>

                    <h4>Course Modules</h4>
                    <ul>
                        <li>Module 1: Fundamentals of Ore Genesis</li>
                        <li>Module 2: Magmatic Ore Deposits</li>
                        <li>Module 3: Hydrothermal Systems</li>
                        <li>Module 4: Sedimentary Ore Deposits</li>
                        <li>Module 5: Supergene Enrichment</li>
                        <li>Module 6: Placer Deposits</li>
                    </ul>

                    <p><strong>Duration:</strong> 8+ hours of video content</p>
                    <p><strong>Format:</strong> Streaming access (lifetime)</p>
                ''',
                'price_cents': 9999,
                'product_type': 'digital',
                'sku': 'LIB-CRS-001',
                'inventory_count': 999,
                'is_featured': False,
                'badges': [],
            },
            {
                'name': 'Geological Field Methods Handbook',
                'slug': 'field-methods-handbook',
                'short_description': 'Printed handbook covering essential geological field techniques',
                'description': '''
                    <h3>Your Field Reference Companion</h3>
                    <p>A practical, pocket-sized handbook covering the essential techniques
                    every geologist needs in the field.</p>

                    <h4>Contents</h4>
                    <ul>
                        <li>Rock and mineral identification</li>
                        <li>Structural measurements</li>
                        <li>Sampling protocols</li>
                        <li>GPS and mapping basics</li>
                        <li>Field safety procedures</li>
                        <li>Report writing guidelines</li>
                    </ul>

                    <p><strong>Format:</strong> Spiral-bound, water-resistant cover, 180 pages</p>
                ''',
                'price_cents': 3499,
                'product_type': 'physical',
                'sku': 'LIB-HB-001',
                'inventory_count': 100,
                'weight_grams': 200,
                'is_featured': False,
                'badges': [],
            },
        ]

        self._create_products(category, products)
        self.stdout.write(f'  Created {len(products)} Resource Library products')

    def _create_products(self, category, products_data):
        """Helper to create products with images and variants"""
        for product_data in products_data:
            variants_data = product_data.pop('variants', [])
            digital_assets_data = product_data.pop('digital_assets', [])

            product, created = StoreProduct.objects.update_or_create(
                slug=product_data['slug'],
                defaults={
                    'category': category,
                    **product_data
                }
            )

            # Create a placeholder image
            StoreProductImage.objects.update_or_create(
                product=product,
                is_primary=True,
                defaults={
                    'image_url': f'https://placehold.co/600x600/1e293b/d4a12a?text={product.name[:20]}',
                    'alt_text': product.name,
                    'display_order': 0,
                }
            )

            # Create variants
            for i, variant_data in enumerate(variants_data):
                StoreProductVariant.objects.update_or_create(
                    product=product,
                    name=variant_data['name'],
                    defaults={
                        'sku': variant_data.get('sku', f"{product.sku}-V{i}"),
                        'inventory_count': variant_data.get('inventory_count', 10),
                        'price_cents_override': variant_data.get('price_cents_override'),
                        'is_active': True,
                    }
                )

            # Create digital assets
            for asset_data in digital_assets_data:
                StoreDigitalAsset.objects.update_or_create(
                    product=product,
                    file_name=asset_data['file_name'],
                    defaults={
                        'file_url': f"https://storage.example.com/digital/{asset_data['file_name']}",
                        'file_size_bytes': asset_data['file_size_bytes'],
                        'download_limit': asset_data.get('download_limit', 5),
                        'expiry_hours': asset_data.get('expiry_hours', 720),
                    }
                )
