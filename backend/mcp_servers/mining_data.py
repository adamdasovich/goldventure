"""
Mining Data MCP Server
Provides tools for querying mining projects, resources, and technical data
"""

from typing import Dict, List, Any
from .base import BaseMCPServer
from django.db.models import Sum, Q, F, Count
from core.models import Company, Project, ResourceEstimate, EconomicStudy


class MiningDataServer(BaseMCPServer):
    """
    MCP Server for mining-specific data queries.
    Provides tools to query projects, resources, and technical data.
    """

    def _register_tools(self):
        """Register all mining data tools"""

        # Tool 1: List all companies
        self.register_tool(
            name="mining_list_companies",
            description=(
                "List all mining companies in the database with basic information. "
                "Returns company name, ticker, exchange, and number of projects."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "active_only": {
                        "type": "boolean",
                        "description": "Only return active companies",
                        "default": True
                    }
                },
                "required": []
            },
            handler=self._list_companies
        )

        # Tool 2: Get company details
        self.register_tool(
            name="mining_get_company_details",
            description=(
                "Get comprehensive details about a specific mining company including "
                "all projects, total resources, and key contact information."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Name or ticker symbol of the company (partial match supported)"
                    }
                },
                "required": ["company_name"]
            },
            handler=self._get_company_details
        )

        # Tool 3: List projects
        self.register_tool(
            name="mining_list_projects",
            description=(
                "List all mining projects with summary information. "
                "Can filter by company, stage, country, or commodity."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Filter by company name (partial match)"
                    },
                    "stage": {
                        "type": "string",
                        "description": "Filter by project stage"
                    },
                    "country": {
                        "type": "string",
                        "description": "Filter by country"
                    },
                    "commodity": {
                        "type": "string",
                        "description": "Filter by primary commodity"
                    }
                },
                "required": []
            },
            handler=self._list_projects
        )

        # Tool 4: Get project details
        self.register_tool(
            name="mining_get_project_details",
            description=(
                "Get comprehensive details about a specific mining project including "
                "location, stage, ownership, resources, and economic studies."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Name of the project (partial match supported)"
                    }
                },
                "required": ["project_name"]
            },
            handler=self._get_project_details
        )

        # Tool 5: Get total resources
        self.register_tool(
            name="mining_get_total_resources",
            description=(
                "Calculate total gold, silver, and copper resources across specified projects. "
                "Can filter by company, resource category, and commodity. "
                "Returns total ounces, tonnes, and average grades."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "company_name": {
                        "type": "string",
                        "description": "Filter by company name (optional)"
                    },
                    "category": {
                        "type": "string",
                        "enum": ["all", "indicated", "inferred", "measured", "mni"],
                        "description": "Resource category. 'mni' = measured & indicated combined.",
                        "default": "all"
                    },
                    "commodity": {
                        "type": "string",
                        "enum": ["gold", "silver", "copper", "all"],
                        "description": "Which commodity to report",
                        "default": "all"
                    }
                },
                "required": []
            },
            handler=self._get_total_resources
        )

    def _list_companies(self, active_only: bool = True) -> Dict:
        """List all companies with summary info"""

        companies_qs = Company.objects.all()
        if active_only:
            companies_qs = companies_qs.filter(is_active=True)

        companies_list = []
        for company in companies_qs.order_by('name'):
            # Count projects
            project_count = company.projects.filter(is_active=True).count()

            companies_list.append({
                'name': company.name,
                'ticker': company.ticker_symbol,
                'exchange': company.get_exchange_display() if company.exchange else None,
                'status': company.get_status_display(),
                'headquarters': f"{company.headquarters_city}, {company.headquarters_country}" if company.headquarters_city else None,
                'website': company.website,
                'number_of_projects': project_count,
                'ceo': company.ceo_name,
            })

        return {
            'total_companies': len(companies_list),
            'companies': companies_list
        }

    def _get_company_details(self, company_name: str) -> Dict:
        """Get detailed information about a company"""

        try:
            # Try to find by name or ticker
            company = Company.objects.filter(
                Q(name__icontains=company_name) |
                Q(ticker_symbol__iexact=company_name)
            ).first()

            if not company:
                # List available companies to help user
                available = list(Company.objects.values_list('name', 'ticker_symbol'))
                return {
                    'error': f"Company '{company_name}' not found",
                    'available_companies': [f"{name} ({ticker})" for name, ticker in available]
                }

        except Company.MultipleObjectsReturned:
            matches = Company.objects.filter(
                Q(name__icontains=company_name) |
                Q(ticker_symbol__iexact=company_name)
            ).values_list('name', 'ticker_symbol')
            return {
                'error': f"Multiple companies match '{company_name}'. Please be more specific.",
                'matching_companies': [f"{name} ({ticker})" for name, ticker in matches]
            }

        # Get all projects
        projects_list = []
        for project in company.projects.filter(is_active=True):
            # Get resource summary for this project
            total_gold = project.resources.aggregate(gold=Sum('gold_ounces'))['gold'] or 0
            total_copper = project.resources.aggregate(copper=Sum('tonnes'))['copper'] or 0

            projects_list.append({
                'name': project.name,
                'stage': project.get_project_stage_display(),
                'commodity': project.get_primary_commodity_display(),
                'country': project.country,
                'province_state': project.province_state,
                'is_flagship': project.is_flagship,
                'ownership': f"{project.ownership_percentage}%",
                'total_gold_oz': self._format_decimal(total_gold),
                'description': project.description[:200] + '...' if len(project.description) > 200 else project.description
            })

        # Get total resources across all projects
        all_resources = ResourceEstimate.objects.filter(
            project__company=company,
            project__is_active=True
        )

        total_gold = all_resources.aggregate(gold=Sum('gold_ounces'))['gold'] or 0
        total_silver = all_resources.aggregate(silver=Sum('silver_ounces'))['silver'] or 0

        return {
            'company_name': company.name,
            'ticker': company.ticker_symbol,
            'exchange': company.get_exchange_display() if company.exchange else None,
            'status': company.get_status_display(),
            'website': company.website,
            'headquarters': {
                'city': company.headquarters_city,
                'country': company.headquarters_country
            },
            'management': {
                'ceo': company.ceo_name,
                'cfo': company.cfo_name,
                'ir_contact': company.ir_contact_name,
                'ir_email': company.ir_contact_email,
                'ir_phone': company.ir_contact_phone
            },
            'market_data': {
                'market_cap_usd': self._format_decimal(company.market_cap_usd),
                'shares_outstanding': company.shares_outstanding,
                'current_price': self._format_decimal(company.current_price)
            },
            'description': company.description,
            'projects': projects_list,
            'total_projects': len(projects_list),
            'total_resources': {
                'gold_oz': self._format_decimal(total_gold),
                'silver_oz': self._format_decimal(total_silver)
            }
        }

    def _list_projects(self, company_name: str = None, stage: str = None,
                      country: str = None, commodity: str = None) -> Dict:
        """List all projects with optional filters"""

        projects = Project.objects.filter(is_active=True)

        # Apply filters
        if company_name:
            projects = projects.filter(
                Q(company__name__icontains=company_name) |
                Q(company__ticker_symbol__iexact=company_name)
            )
        if stage:
            projects = projects.filter(project_stage=stage)
        if country:
            projects = projects.filter(country__iexact=country)
        if commodity:
            projects = projects.filter(primary_commodity=commodity)

        projects_list = []
        for project in projects.select_related('company').order_by('-is_flagship', 'name'):
            # Get total resources for this project
            total_gold = project.resources.aggregate(gold=Sum('gold_ounces'))['gold'] or 0

            projects_list.append({
                'name': project.name,
                'company': project.company.name,
                'ticker': project.company.ticker_symbol,
                'stage': project.get_project_stage_display(),
                'commodity': project.get_primary_commodity_display(),
                'country': project.country,
                'province_state': project.province_state,
                'ownership': f"{project.ownership_percentage}%",
                'total_gold_ounces': self._format_decimal(total_gold),
                'is_flagship': project.is_flagship
            })

        return {
            'total_projects': len(projects_list),
            'projects': projects_list,
            'filters_applied': {
                'company': company_name,
                'stage': stage,
                'country': country,
                'commodity': commodity
            }
        }

    def _get_project_details(self, project_name: str) -> Dict:
        """Get comprehensive project information"""

        try:
            # Find project (case-insensitive partial match)
            project = Project.objects.filter(
                name__icontains=project_name,
                is_active=True
            ).select_related('company').first()

            if not project:
                # List available projects to help
                available = list(Project.objects.filter(is_active=True).values_list('name', 'company__name'))
                return {
                    'error': f"Project '{project_name}' not found",
                    'available_projects': [f"{name} ({company})" for name, company in available]
                }

        except Project.MultipleObjectsReturned:
            matches = Project.objects.filter(
                name__icontains=project_name,
                is_active=True
            ).values_list('name', 'company__name')
            return {
                'error': f"Multiple projects match '{project_name}'. Please be more specific.",
                'matching_projects': [f"{name} ({company})" for name, company in matches]
            }

        # Get all resource categories
        resources_by_category = {}
        for res in project.resources.order_by('-report_date', 'category'):
            if res.category not in resources_by_category:
                resources_by_category[res.category] = {
                    'category': res.get_category_display(),
                    'gold_ounces': self._format_decimal(res.gold_ounces),
                    'gold_grade_gpt': self._format_decimal(res.gold_grade_gpt),
                    'silver_ounces': self._format_decimal(res.silver_ounces),
                    'copper_grade_pct': self._format_decimal(res.copper_grade_pct),
                    'tonnes': self._format_decimal(res.tonnes),
                    'report_date': self._format_date(res.report_date),
                    'standard': res.get_standard_display()
                }

        # Get latest economic study
        latest_study = project.economic_studies.order_by('-release_date').first()

        result = {
            'project_name': project.name,
            'company': project.company.name,
            'ticker': project.company.ticker_symbol,
            'stage': project.get_project_stage_display(),
            'commodity': project.get_primary_commodity_display(),
            'location': {
                'country': project.country,
                'province_state': project.province_state,
                'coordinates': {
                    'latitude': self._format_decimal(project.latitude),
                    'longitude': self._format_decimal(project.longitude)
                } if project.latitude and project.longitude else None
            },
            'ownership_percentage': self._format_decimal(project.ownership_percentage),
            'is_flagship': project.is_flagship,
            'description': project.description,
            'resources_by_category': list(resources_by_category.values()),
            'latest_study': None
        }

        # Add economic study if exists
        if latest_study:
            result['latest_study'] = {
                'type': latest_study.get_study_type_display(),
                'release_date': self._format_date(latest_study.release_date),
                'economics': {
                    'npv_5_usd_millions': self._format_decimal(latest_study.npv_5_usd),
                    'irr_percent': self._format_decimal(latest_study.irr_percent),
                    'payback_years': self._format_decimal(latest_study.payback_years)
                },
                'production': {
                    'annual_production_oz': latest_study.annual_production_oz,
                    'mine_life_years': self._format_decimal(latest_study.mine_life_years)
                },
                'costs': {
                    'aisc_usd_per_oz': self._format_decimal(latest_study.aisc_per_oz),
                    'initial_capex_usd_millions': self._format_decimal(latest_study.initial_capex_usd)
                },
                'assumptions': {
                    'gold_price_usd': self._format_decimal(latest_study.gold_price_assumption)
                }
            }

        return result

    def _get_total_resources(self, company_name: str = None, category: str = "all",
                            commodity: str = "all") -> Dict:
        """Calculate total resources across projects"""

        # Start with all resource estimates
        resources_qs = ResourceEstimate.objects.all()

        # Filter by company if specified
        if company_name:
            resources_qs = resources_qs.filter(
                Q(project__company__name__icontains=company_name) |
                Q(project__company__ticker_symbol__iexact=company_name)
            )

        # Filter by category
        if category != "all":
            if category == "mni":
                resources_qs = resources_qs.filter(category__in=["measured", "indicated"])
            else:
                resources_qs = resources_qs.filter(category=category)

        # Only active projects
        resources_qs = resources_qs.filter(project__is_active=True)

        # Aggregate by commodity
        aggregates = {}

        if commodity in ["gold", "all"]:
            gold_data = resources_qs.aggregate(
                total_gold_oz=Sum('gold_ounces'),
                total_tonnes=Sum('tonnes'),
                project_count=Count('project', distinct=True)
            )
            if gold_data['total_gold_oz']:
                aggregates['gold'] = {
                    'total_ounces': self._format_decimal(gold_data['total_gold_oz']),
                    'total_tonnes': self._format_decimal(gold_data['total_tonnes']),
                    'number_of_projects': gold_data['project_count']
                }

        if commodity in ["silver", "all"]:
            silver_data = resources_qs.aggregate(
                total_silver_oz=Sum('silver_ounces')
            )
            if silver_data['total_silver_oz']:
                aggregates['silver'] = {
                    'total_ounces': self._format_decimal(silver_data['total_silver_oz'])
                }

        if commodity in ["copper", "all"]:
            copper_data = resources_qs.aggregate(
                total_tonnes=Sum('tonnes')
            )
            # Note: This is simplified - copper resources need more sophisticated calculation
            if copper_data['total_tonnes']:
                aggregates['copper'] = {
                    'total_tonnes': self._format_decimal(copper_data['total_tonnes'])
                }

        return {
            'category': category,
            'commodity': commodity,
            'company_filter': company_name,
            'resources': aggregates
        }
