"""
Django management command to import glossary terms into the database
Usage: python manage.py import_glossary
"""

from django.core.management.base import BaseCommand
from core.models import GlossaryTerm


class Command(BaseCommand):
    help = 'Import initial glossary terms into the database'

    def handle(self, *args, **options):
        """Import all 60 glossary terms"""

        terms_data = [
            {
                "term": "NI 43-101",
                "definition": "Canadian National Instrument 43-101 is a regulatory standard for public disclosure of scientific and technical information concerning mineral projects. It requires independent qualified persons to prepare technical reports and resource estimates, ensuring transparency and accuracy in mining investment information.",
                "category": "regulatory",
                "related_links": [{"text": "View Companies with NI 43-101 Reports", "url": "/companies"}],
                "keywords": "NI 43-101, technical report, Canadian standard, mineral disclosure"
            },
            {
                "term": "Indicated Resource",
                "definition": "A mineral resource for which quantity, grade, densities, shape, and physical characteristics are estimated with sufficient confidence to allow the appropriate application of technical and economic parameters. Indicated resources have a higher level of confidence than inferred resources but lower than measured resources.",
                "category": "reporting",
                "related_links": [{"text": "Browse Mining Projects", "url": "/companies"}],
                "keywords": "indicated resource, mineral resource, resource classification"
            },
            {
                "term": "Inferred Resource",
                "definition": "A mineral resource for which quantity and grade are estimated based on limited geological evidence and sampling. Inferred resources have the lowest level of geological confidence and should not be converted to mineral reserves. Further exploration is required to upgrade to indicated or measured categories.",
                "category": "reporting",
                "keywords": "inferred resource, exploration, geological confidence"
            },
            {
                "term": "Measured Resource",
                "definition": "A mineral resource for which quantity, grade, densities, shape, and physical characteristics are estimated with confidence sufficient for the appropriate application of technical and economic parameters to support production planning. This is the highest level of geological confidence in resource estimation.",
                "category": "reporting",
                "keywords": "measured resource, high confidence, resource estimation"
            },
            {
                "term": "TSXV (TSX Venture Exchange)",
                "definition": "The TSX Venture Exchange is Canada's premier public venture capital marketplace for emerging companies. It is the primary listing exchange for junior mining companies in Canada, providing access to capital for exploration and development projects. Many junior gold mining companies are listed on TSXV.",
                "category": "finance",
                "related_links": [{"text": "Explore TSXV Mining Stocks", "url": "/companies"}],
                "keywords": "TSXV, TSX Venture, stock exchange, junior mining"
            },
            {
                "term": "Grade (g/t)",
                "definition": "The concentration of a valuable mineral within ore, typically expressed in grams per tonne (g/t) for precious metals like gold and silver. Higher grades indicate richer ore deposits and generally better economics. For example, 5 g/t gold means 5 grams of gold per tonne of ore.",
                "category": "geology",
                "keywords": "grade, g/t, ore concentration, metal content"
            },
            {
                "term": "Heap Leaching",
                "definition": "An industrial mining process used to extract precious metals from ore by placing crushed ore in large heaps and percolating a chemical solution through it to dissolve the valuable minerals. This method is economical for processing lower-grade ore deposits and is commonly used in gold mining operations.",
                "category": "operations",
                "keywords": "heap leaching, ore processing, extraction method"
            },
            {
                "term": "Feasibility Study",
                "definition": "A comprehensive technical and economic study of a mineral project used to demonstrate whether the project is economically viable and technically feasible. Feasibility studies are required before a project can proceed to development and must be prepared by qualified persons under NI 43-101 standards.",
                "category": "reporting",
                "related_links": [{"text": "View Economic Studies", "url": "/companies"}],
                "keywords": "feasibility study, economic analysis, project viability"
            },
            {
                "term": "Junior Mining Company",
                "definition": "An exploration or development-stage mining company focused on discovering and developing new mineral deposits. Junior miners typically have market capitalizations under $500 million, limited production or revenue, and rely on equity financing for exploration programs. They carry higher risk but offer significant upside potential.",
                "category": "finance",
                "related_links": [{"text": "Browse Junior Gold Mining Companies", "url": "/companies"}],
                "keywords": "junior mining, exploration company, development stage"
            },
            {
                "term": "Preliminary Economic Assessment (PEA)",
                "definition": "An initial economic analysis of a mineral project that includes estimates of capital and operating costs, metal prices, and project economics. PEAs are less detailed than feasibility studies and carry higher uncertainty, but help determine if a project warrants further study.",
                "category": "reporting",
                "keywords": "PEA, preliminary assessment, economic analysis"
            },
            {
                "term": "Assay",
                "definition": "The chemical analysis of rock, soil, or drill core samples to determine the concentration of valuable minerals or metals. Assay results are critical for resource estimation and are typically reported in parts per million (ppm) or grams per tonne (g/t) for precious metals.",
                "category": "geology",
                "keywords": "assay, chemical analysis, sample testing"
            },
            {
                "term": "Drill Program",
                "definition": "A systematic exploration program using diamond or reverse circulation drilling to obtain subsurface samples for geological and geochemical analysis. Drill programs are essential for resource definition, exploration targeting, and upgrading resource classifications.",
                "category": "operations",
                "keywords": "drilling, exploration, core samples"
            },
            {
                "term": "Cut-off Grade",
                "definition": "The minimum grade of mineralization that can be economically mined and processed. Material below the cut-off grade is considered waste, while material above it is classified as ore. Cut-off grades depend on mining costs, processing costs, metal prices, and metallurgical recovery rates.",
                "category": "geology",
                "keywords": "cut-off grade, economic threshold, ore classification"
            },
            {
                "term": "Metallurgical Recovery",
                "definition": "The percentage of valuable metal that can be extracted from ore during processing. For example, 90% gold recovery means that 90% of the gold in the ore can be recovered through milling and processing, with 10% lost to tailings.",
                "category": "operations",
                "keywords": "recovery rate, metallurgy, processing efficiency"
            },
            {
                "term": "Ounce (Troy Ounce)",
                "definition": "The standard unit of measurement for precious metals, equal to 31.1035 grams. Gold, silver, platinum, and palladium are typically quoted and traded in troy ounces. Not to be confused with the avoirdupois ounce (28.35 grams) used for everyday items.",
                "category": "reporting",
                "keywords": "troy ounce, precious metals, measurement"
            },
            {
                "term": "Greenfield Exploration",
                "definition": "Exploration activities conducted in areas with no previous mining or exploration history. Greenfield projects carry higher geological risk but offer potential for major new discoveries. Contrasts with brownfield exploration near existing mines or known deposits.",
                "category": "operations",
                "keywords": "greenfield, new exploration, discovery"
            },
            {
                "term": "Brownfield Exploration",
                "definition": "Exploration conducted near existing mines or known mineral deposits to find additional resources or extensions. Brownfield exploration has lower geological risk than greenfield work because the geological setting is already understood.",
                "category": "operations",
                "keywords": "brownfield, near-mine exploration, expansion"
            },
            {
                "term": "Qualified Person (QP)",
                "definition": "Under NI 43-101, a qualified person is an engineer or geoscientist with at least five years of relevant experience in mineral exploration, mine development, or operations. QPs are responsible for preparing and approving technical reports and resource estimates.",
                "category": "regulatory",
                "keywords": "qualified person, QP, technical expert"
            },
            {
                "term": "Mineral Reserve",
                "definition": "The economically mineable portion of a measured or indicated mineral resource, demonstrated by at least a preliminary feasibility study. Mineral reserves include consideration of mining, metallurgical, economic, marketing, legal, and environmental factors.",
                "category": "reporting",
                "keywords": "mineral reserve, proven reserve, probable reserve"
            },
            {
                "term": "Proven Reserve",
                "definition": "The economically mineable portion of a measured mineral resource, representing the highest level of confidence in reserve estimation. Proven reserves are suitable for detailed mine planning and financing decisions.",
                "category": "reporting",
                "keywords": "proven reserve, high confidence, mine planning"
            },
            {
                "term": "Probable Reserve",
                "definition": "The economically mineable portion of an indicated and, in some cases, a measured mineral resource. Probable reserves have a lower level of confidence than proven reserves but are still suitable for mine planning purposes.",
                "category": "reporting",
                "keywords": "probable reserve, reserve classification"
            },
            {
                "term": "Strike Length",
                "definition": "The horizontal distance along which a mineralized zone extends. Greater strike lengths indicate larger potential deposits and are important factors in resource estimation and mine planning.",
                "category": "geology",
                "keywords": "strike length, mineralization extent, geology"
            },
            {
                "term": "True Width",
                "definition": "The actual thickness of a mineralized zone measured perpendicular to its orientation. Drill holes rarely intersect mineralization at perfect right angles, so true width calculations are necessary to estimate tonnage accurately.",
                "category": "geology",
                "keywords": "true width, thickness, drill intercept"
            },
            {
                "term": "Intercept",
                "definition": "The length of mineralization encountered in a drill hole, typically reported with grade information. For example, '10 meters at 5 g/t gold' means the drill hole encountered 10 meters of material grading 5 grams of gold per tonne.",
                "category": "geology",
                "keywords": "drill intercept, mineralization, drilling results"
            },
            {
                "term": "Flow-Through Shares",
                "definition": "A Canadian tax incentive that allows mining exploration companies to transfer tax deductions for exploration expenses to investors. Flow-through financing is a common method for junior miners to raise capital for exploration programs.",
                "category": "finance",
                "keywords": "flow-through shares, tax incentive, Canadian financing"
            },
            {
                "term": "Private Placement",
                "definition": "A capital raising method where securities are sold directly to a small number of investors rather than through a public offering. Junior mining companies frequently use private placements to fund exploration and development activities.",
                "category": "finance",
                "related_links": [{"text": "Learn About Private Placements", "url": "/financial-hub"}],
                "keywords": "private placement, financing, capital raising"
            },
            {
                "term": "Warrant",
                "definition": "A security that gives the holder the right to purchase shares at a specified price (strike price) within a certain time period. Warrants are often issued as part of private placement financings in junior mining companies.",
                "category": "finance",
                "keywords": "warrant, stock option, financing sweetener"
            },
            {
                "term": "All-in Sustaining Cost (AISC)",
                "definition": "A comprehensive measure of the total cost to produce an ounce of gold, including mining, processing, administrative costs, sustaining capital, and exploration. AISC is the industry standard metric for comparing mining company costs.",
                "category": "finance",
                "keywords": "AISC, production cost, operating metrics"
            },
            {
                "term": "Stripping Ratio",
                "definition": "The ratio of waste rock that must be removed to extract one tonne of ore in open-pit mining. Lower stripping ratios indicate better economics. For example, a 3:1 stripping ratio means 3 tonnes of waste must be removed for every tonne of ore mined.",
                "category": "operations",
                "keywords": "stripping ratio, waste removal, open pit"
            },
            {
                "term": "Tailings",
                "definition": "The waste material left over after ore has been processed to extract valuable minerals. Tailings are typically stored in engineered facilities called tailings dams and must be managed to prevent environmental impacts.",
                "category": "operations",
                "keywords": "tailings, waste management, environmental"
            },
            {
                "term": "Mill",
                "definition": "A facility where ore is crushed, ground, and processed to extract valuable minerals. Gold mills typically use gravity concentration, flotation, or cyanide leaching to recover gold from ore.",
                "category": "operations",
                "keywords": "mill, processing plant, ore processing"
            },
            {
                "term": "Underground Mining",
                "definition": "Mining method used to extract ore from deposits located deep beneath the surface. Underground mining is more expensive than open-pit but is necessary for deposits that are too deep or have too much overburden for surface mining.",
                "category": "operations",
                "keywords": "underground mining, shaft, tunnel"
            },
            {
                "term": "Open-Pit Mining",
                "definition": "A surface mining method where ore is extracted from an open excavation. Open-pit mining is suitable for deposits near the surface and is generally less expensive than underground mining but creates larger environmental footprints.",
                "category": "operations",
                "keywords": "open pit, surface mining, excavation"
            },
            {
                "term": "Orebody",
                "definition": "A continuous, well-defined mass of material containing a sufficient concentration of valuable minerals to be economically mined. The size, grade, and geometry of the orebody determine the mining method and project economics.",
                "category": "geology",
                "keywords": "orebody, ore body, mineral deposit"
            },
            {
                "term": "Geophysical Survey",
                "definition": "The use of physical measurements (magnetic, electromagnetic, gravity, or seismic) to detect subsurface geological features and potential mineral deposits. Geophysical surveys are cost-effective exploration tools for identifying drill targets.",
                "category": "operations",
                "keywords": "geophysics, survey, exploration method"
            },
            {
                "term": "Geochemical Survey",
                "definition": "The systematic collection and analysis of soil, rock, or water samples to detect anomalous concentrations of target elements. Geochemical surveys help identify areas of mineralization for follow-up drilling.",
                "category": "operations",
                "keywords": "geochemistry, soil sampling, exploration"
            },
            {
                "term": "Alteration",
                "definition": "Chemical and physical changes to rock caused by hydrothermal fluids, often associated with mineralization. Alteration patterns help geologists identify potential ore zones and understand the processes that formed a deposit.",
                "category": "geology",
                "keywords": "alteration, hydrothermal, geological indicator"
            },
            {
                "term": "Vein",
                "definition": "A sheet-like deposit of minerals that fills a fracture or fault in rock. Many gold deposits occur in quartz veins where gold was deposited from hydrothermal fluids. Veins can range from millimeters to meters in width.",
                "category": "geology",
                "keywords": "vein, quartz vein, mineral deposit"
            },
            {
                "term": "Stockwork",
                "definition": "A complex network of small veins or veinlets forming a three-dimensional mesh in rock. Stockwork mineralization is common in porphyry and some gold deposits, where multiple generations of veining create economic grades.",
                "category": "geology",
                "keywords": "stockwork, vein network, mineralization"
            },
            {
                "term": "Porphyry Deposit",
                "definition": "A large, low-grade disseminated ore deposit typically containing copper, molybdenum, and sometimes gold. Porphyry deposits form from hydrothermal fluids associated with intrusive igneous rocks and are among the world's largest metal sources.",
                "category": "geology",
                "keywords": "porphyry, copper deposit, large tonnage"
            },
            {
                "term": "Epithermal Deposit",
                "definition": "A mineral deposit formed at shallow depths and low temperatures from hydrothermal fluids. Epithermal deposits are important sources of gold and silver and are classified as low-sulfidation or high-sulfidation based on their geochemistry.",
                "category": "geology",
                "keywords": "epithermal, gold deposit, hydrothermal"
            },
            {
                "term": "Volcanogenic Massive Sulfide (VMS)",
                "definition": "A type of metal sulfide ore deposit formed on or near the seafloor through volcanic-associated hydrothermal activity. VMS deposits are important sources of copper, zinc, lead, gold, and silver.",
                "category": "geology",
                "keywords": "VMS, massive sulfide, volcanic deposit"
            },
            {
                "term": "Carlin-Type Deposit",
                "definition": "A sediment-hosted disseminated gold deposit type named after the Carlin Trend in Nevada. These deposits contain microscopic gold in altered sedimentary rocks and are processed by heap leaching or roasting.",
                "category": "geology",
                "keywords": "Carlin type, sediment hosted, microscopic gold"
            },
            {
                "term": "Orogenic Gold",
                "definition": "Gold deposits formed during mountain-building (orogenic) events, typically hosted in quartz veins within metamorphic rocks. Orogenic gold deposits are found in greenstone belts worldwide and include many historic gold mining districts.",
                "category": "geology",
                "keywords": "orogenic gold, greenstone, lode gold"
            },
            {
                "term": "Placer Deposit",
                "definition": "A surficial mineral deposit formed by the concentration of heavy minerals through weathering and sedimentary processes. Placer gold deposits in streams and rivers were the target of historic gold rushes and can still be mined economically.",
                "category": "geology",
                "keywords": "placer, alluvial gold, stream deposit"
            },
            {
                "term": "Concentrate",
                "definition": "The product of mineral processing that contains elevated concentrations of valuable metals. Concentrates are typically shipped to smelters for final metal recovery. For example, a copper concentrate might contain 25-30% copper.",
                "category": "operations",
                "keywords": "concentrate, processed ore, smelter feed"
            },
            {
                "term": "Flotation",
                "definition": "A mineral processing method that uses chemical reagents and air bubbles to separate valuable minerals from waste rock based on differences in surface properties. Flotation is widely used for copper, zinc, lead, and some gold ores.",
                "category": "operations",
                "keywords": "flotation, mineral processing, separation"
            },
            {
                "term": "Gravity Separation",
                "definition": "A mineral processing technique that uses differences in specific gravity to separate heavy valuable minerals from lighter waste minerals. Common methods include jigs, spirals, and shaking tables, often used as a first stage in gold recovery.",
                "category": "operations",
                "keywords": "gravity separation, dense media, gold recovery"
            },
            {
                "term": "Cyanide Leaching",
                "definition": "A process that uses cyanide solution to dissolve gold from ore. The gold is then recovered from solution through adsorption on activated carbon or zinc precipitation. This is the most common method for gold extraction worldwide.",
                "category": "operations",
                "keywords": "cyanide leaching, gold extraction, processing"
            },
            {
                "term": "Carbon-in-Pulp (CIP)",
                "definition": "A process for recovering gold from cyanide leach solutions using activated carbon to adsorb gold. The carbon is then treated to recover the gold. CIP is one of the most common gold recovery methods used in modern mills.",
                "category": "operations",
                "keywords": "CIP, carbon in pulp, gold recovery"
            },
            {
                "term": "Net Present Value (NPV)",
                "definition": "The present value of future cash flows from a mining project, discounted at a specified rate (typically 5% for NPV5). Positive NPV indicates a project is economically viable. NPV is a key metric in feasibility studies.",
                "category": "finance",
                "keywords": "NPV, net present value, project economics"
            },
            {
                "term": "Internal Rate of Return (IRR)",
                "definition": "The discount rate at which the net present value of a project equals zero. Higher IRRs indicate better project economics. IRR is used alongside NPV to evaluate mining project attractiveness to investors.",
                "category": "finance",
                "keywords": "IRR, internal rate of return, return on investment"
            },
            {
                "term": "Payback Period",
                "definition": "The time required for a mining project to recover its initial capital investment from net cash flows. Shorter payback periods indicate lower risk and are preferred by investors. Typical payback periods for mining projects range from 2-5 years.",
                "category": "finance",
                "keywords": "payback period, capital recovery, investment metric"
            },
            {
                "term": "Capital Expenditure (CapEx)",
                "definition": "The upfront costs required to build a mine, including equipment, infrastructure, and construction. CapEx is distinguished from operating costs (OpEx) and is a critical factor in project economics and financing requirements.",
                "category": "finance",
                "keywords": "capex, capital costs, initial investment"
            },
            {
                "term": "Operating Expenditure (OpEx)",
                "definition": "The ongoing costs to operate a mine, including labor, energy, consumables, and maintenance. OpEx is typically expressed per tonne of ore processed or per ounce of metal produced and directly affects mine profitability.",
                "category": "finance",
                "keywords": "opex, operating costs, production costs"
            },
            {
                "term": "Dilution",
                "definition": "The unavoidable contamination of ore with waste rock during mining, which lowers the average grade of material sent to the mill. Dilution is expressed as a percentage and must be accounted for in resource estimates and mine planning.",
                "category": "operations",
                "keywords": "dilution, grade reduction, mining loss"
            },
            {
                "term": "Mining Recovery",
                "definition": "The percentage of ore in a deposit that is actually extracted and processed. Some ore is lost due to mining constraints, pillars left for ground support, or ore left in stopes. Typical mining recoveries range from 85-95%.",
                "category": "operations",
                "keywords": "mining recovery, extraction efficiency, ore recovery"
            },
            {
                "term": "Mineral Resource",
                "definition": "A concentration of material of economic interest in or on the Earth's crust in such form, grade, and quantity that there are reasonable prospects for economic extraction. Resources are classified as measured, indicated, or inferred based on confidence level.",
                "category": "reporting",
                "keywords": "mineral resource, resource classification, geological inventory"
            },
            {
                "term": "Accredited Investor",
                "definition": "An investor who meets specific income or net worth requirements and is permitted to participate in certain private investment opportunities, including flow-through share financings. Requirements vary by jurisdiction but generally involve annual income over $200,000 or net worth over $1 million.",
                "category": "finance",
                "related_links": [{"text": "Learn About Accredited Investor Status", "url": "/financial-hub"}],
                "keywords": "accredited investor, qualified investor, private placement"
            },
        ]

        created_count = 0
        updated_count = 0

        for term_data in terms_data:
            term, created = GlossaryTerm.objects.update_or_create(
                term=term_data['term'],
                defaults={
                    'definition': term_data['definition'],
                    'category': term_data['category'],
                    'related_links': term_data.get('related_links', []),
                    'keywords': term_data.get('keywords', ''),
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Created: {term.term}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ Updated: {term.term}'))

        self.stdout.write(self.style.SUCCESS(f'\n=== Import Complete ==='))
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count} terms'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count} terms'))
        self.stdout.write(self.style.SUCCESS(f'Total: {created_count + updated_count} terms'))
