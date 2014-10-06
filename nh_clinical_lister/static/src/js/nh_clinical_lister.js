openerp.nh_clinical_lister = function (instance) {
    var QWeb = instance.web.qweb;

    instance.nh_clinical_lister.PBPWidget = instance.web.list.Column.extend({
        _format: function (row_data, options) {
            if (row_data.pbp_flag.value == true){
                return QWeb.render('lister_updown', {
                    'widget': this,
                    'prefix': instance.session.prefix,
                });
            } else {
                return '';
            };
        },
    });

    instance.web.list.columns.add('field.lister_pbp', 'instance.nh_clinical_lister.PBPWidget');
};