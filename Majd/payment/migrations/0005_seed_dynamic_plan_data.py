from django.db import migrations


def seed_dynamic(apps, schema_editor):
    PlanType = apps.get_model('payment', 'PlanType')
    defaults = {
        'starter': {
            'description': 'Perfect for small academies getting started',
            'monthly_price': 299,
            'icon_class': 'bi-app',
            'is_featured': False,
            'display_order': 1,
            'features': [
                'Up to 50 students',
                '2 coaches included',
                'Basic progress tracking',
                'Email support',
                'Mobile app access',
                'Basic reporting',
                'Student profiles',
                'Limited to 2 sports programs',
                'Basic analytics only',
            ],
        },
        'professional': {
            'description': 'Ideal for growing academies with multiple programs',
            'monthly_price': 599,
            'icon_class': 'bi-stars',
            'is_featured': True,
            'display_order': 2,
            'features': [
                'Up to 200 students',
                '10 coaches included',
                'Advanced progress tracking',
                'Priority email & phone support',
                'Mobile app access',
                'Advanced reporting & analytics',
                'Student & parent portals',
                'Unlimited sports programs',
                'Custom branding',
                'Payment processing',
                'Event management',
                'Marketing tools',
            ],
        },
        'enterprise': {
            'description': 'Complete solution for large academies and organizations',
            'monthly_price': 1299,
            'icon_class': 'bi-award',
            'is_featured': False,
            'display_order': 3,
            'features': [
                'Unlimited students',
                'Unlimited coaches',
                'AI-powered analytics',
                '24/7 dedicated support',
                'Mobile app access',
                'White-label solution',
                'Multi-location management',
                'Advanced integrations',
                'Custom development',
                'API access',
                'Priority feature requests',
                'Dedicated account manager',
                'Advanced security features',
                'Custom reporting',
                'Bulk operations',
            ],
        },
    }

    for name, data in defaults.items():
        obj, _ = PlanType.objects.get_or_create(name=name.capitalize())
        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()


def unseed_dynamic(apps, schema_editor):
    # keep plan types; only clear dynamic fields
    PlanType = apps.get_model('payment', 'PlanType')
    for name in ['Starter', 'Professional', 'Enterprise']:
        try:
            obj = PlanType.objects.get(name=name)
            obj.features = []
            obj.monthly_price = 0
            obj.icon_class = 'bi-app'
            obj.is_featured = False
            obj.display_order = 0
            obj.description = ''
            obj.save()
        except PlanType.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_plantype_display_order_plantype_features_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_dynamic, reverse_code=unseed_dynamic),
    ]
