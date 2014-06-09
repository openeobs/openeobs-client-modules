openerp.t4clinical_ldh = function (instance) {
    instance.web.ListView.include({
        init: function(parent, dataset, view_id, options) {
            if (options.action){
                if (options.action.name == "Patient Clerkings" || options.action.name == "Patient Reviews" || options.action.name == "Patient List"){
                    options.selectable = false;
                };
            }
            this._super.apply(this, [parent, dataset, view_id, options]);
        },

        select_record: function (index, view) {
            view = view || index == null ? 'form' : 'form';
            this.dataset.index = index;
            if (this.fields_view.name != "T4 Clinical Placement Tree View" && this.fields_view.name != "T4 Clinical LDH Review Tree View" && this.fields_view.name != "T4 Clinical LDH Clerking Tree View"){
                _.delay(_.bind(function () {
                    this.do_switch_view(view);
                }, this));
            }
        },
    })

}