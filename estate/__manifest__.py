{
    'name': 'Real Estate',
    'version': '1.0',
    'author': 'Your Name',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',

        # مهم: خلي العروض (offers) قبل أي ملف يستخدمها
        'views/estate_property_offer_views.xml',

        'views/estate_property_tag_views.xml',
        'views/estate_property_type_views.xml',
        'views/estate_property_views.xml',
        'views/res_users_views.xml',
        'views/estate_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # ملف الستايل الجديد لإصلاح الشريط العلوي والخطوط
            'estate/static/src/css/fix.css',
        ],
    },
    'application': True,
}
