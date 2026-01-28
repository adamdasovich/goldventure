# Generated manually for data integrity
# Add CHECK constraints for business rules

from django.db import migrations, models


class Migration(migrations.Migration):
    """
    Add database-level CHECK constraints to enforce data integrity rules
    that can't be reliably enforced at the application level alone.
    """

    dependencies = [
        ('core', '0038_userai_usage'),
    ]

    operations = [
        # =====================================================================
        # COMPANY MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='company',
            constraint=models.CheckConstraint(
                check=models.Q(market_cap_usd__gte=0) | models.Q(market_cap_usd__isnull=True),
                name='company_market_cap_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='company',
            constraint=models.CheckConstraint(
                check=models.Q(current_price__gte=0) | models.Q(current_price__isnull=True),
                name='company_current_price_non_negative',
            ),
        ),

        # =====================================================================
        # PROJECT MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='project',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(ownership_percentage__gte=0, ownership_percentage__lte=100) |
                    models.Q(ownership_percentage__isnull=True)
                ),
                name='project_ownership_percentage_valid',
            ),
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.CheckConstraint(
                check=models.Q(latitude__gte=-90, latitude__lte=90) | models.Q(latitude__isnull=True),
                name='project_latitude_valid',
            ),
        ),
        migrations.AddConstraint(
            model_name='project',
            constraint=models.CheckConstraint(
                check=models.Q(longitude__gte=-180, longitude__lte=180) | models.Q(longitude__isnull=True),
                name='project_longitude_valid',
            ),
        ),

        # =====================================================================
        # RESOURCE ESTIMATE MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='resourceestimate',
            constraint=models.CheckConstraint(
                check=models.Q(tonnes__gte=0),
                name='resource_tonnes_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='resourceestimate',
            constraint=models.CheckConstraint(
                check=models.Q(gold_ounces__gte=0) | models.Q(gold_ounces__isnull=True),
                name='resource_gold_ounces_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='resourceestimate',
            constraint=models.CheckConstraint(
                check=models.Q(silver_ounces__gte=0) | models.Q(silver_ounces__isnull=True),
                name='resource_silver_ounces_non_negative',
            ),
        ),

        # =====================================================================
        # ECONOMIC STUDY MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='economicstudy',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(irr_percent__gte=0, irr_percent__lte=1000) |
                    models.Q(irr_percent__isnull=True)
                ),
                name='study_irr_percent_valid',
            ),
        ),
        migrations.AddConstraint(
            model_name='economicstudy',
            constraint=models.CheckConstraint(
                check=models.Q(payback_years__gte=0) | models.Q(payback_years__isnull=True),
                name='study_payback_years_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='economicstudy',
            constraint=models.CheckConstraint(
                check=models.Q(mine_life_years__gte=0) | models.Q(mine_life_years__isnull=True),
                name='study_mine_life_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='economicstudy',
            constraint=models.CheckConstraint(
                check=models.Q(aisc_per_oz__gte=0) | models.Q(aisc_per_oz__isnull=True),
                name='study_aisc_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='economicstudy',
            constraint=models.CheckConstraint(
                check=models.Q(initial_capex_usd__gte=0) | models.Q(initial_capex_usd__isnull=True),
                name='study_capex_non_negative',
            ),
        ),

        # =====================================================================
        # FINANCING MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='financing',
            constraint=models.CheckConstraint(
                check=models.Q(amount_raised_usd__gte=0),
                name='financing_amount_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='financing',
            constraint=models.CheckConstraint(
                check=models.Q(price_per_share__gte=0) | models.Q(price_per_share__isnull=True),
                name='financing_price_per_share_non_negative',
            ),
        ),

        # =====================================================================
        # MARKET DATA MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='marketdata',
            constraint=models.CheckConstraint(
                check=models.Q(open_price__gte=0),
                name='marketdata_open_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='marketdata',
            constraint=models.CheckConstraint(
                check=models.Q(high_price__gte=0),
                name='marketdata_high_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='marketdata',
            constraint=models.CheckConstraint(
                check=models.Q(low_price__gte=0),
                name='marketdata_low_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='marketdata',
            constraint=models.CheckConstraint(
                check=models.Q(close_price__gte=0),
                name='marketdata_close_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='marketdata',
            constraint=models.CheckConstraint(
                check=models.Q(high_price__gte=models.F('low_price')),
                name='marketdata_high_gte_low',
            ),
        ),
        migrations.AddConstraint(
            model_name='marketdata',
            constraint=models.CheckConstraint(
                check=models.Q(volume__gte=0),
                name='marketdata_volume_non_negative',
            ),
        ),

        # =====================================================================
        # METAL PRICE MODEL CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='metalprice',
            constraint=models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='metalprice_price_non_negative',
            ),
        ),

        # =====================================================================
        # INVESTOR HOLDING CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='investorholding',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(percentage_ownership__gte=0, percentage_ownership__lte=100) |
                    models.Q(percentage_ownership__isnull=True)
                ),
                name='holding_percentage_valid',
            ),
        ),

        # =====================================================================
        # STORE PRODUCT CONSTRAINTS
        # =====================================================================
        migrations.AddConstraint(
            model_name='storeproduct',
            constraint=models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='storeproduct_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='storeproduct',
            constraint=models.CheckConstraint(
                check=(
                    models.Q(compare_at_price__gte=0) |
                    models.Q(compare_at_price__isnull=True)
                ),
                name='storeproduct_compare_price_non_negative',
            ),
        ),
        migrations.AddConstraint(
            model_name='storeproduct',
            constraint=models.CheckConstraint(
                check=models.Q(stock_quantity__gte=0),
                name='storeproduct_stock_non_negative',
            ),
        ),
    ]
