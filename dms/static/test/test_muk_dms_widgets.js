odoo.define_section('muk_dms.test_widgets', ['muk_dms_widgets.form_widgets'], function (test, mock) {

	 test('FieldPath', function(assert, widgets) {
		 var fake_field_manager = {
			 get_field_desc: function() {
				 return {
					 'string': 'Path',
				 };
			 },
			 on: function() {},
			 off: function() {},
			 get: function() {},
			 $el: jQuery(),
		 },
		 widget = new widgets.FieldPath(
			 fake_field_manager,
			 {
				 attrs: {
					 modifiers: '{}',
					 name: 'field_name',
					 widget: 'path',
				 },
			 }
		),
		$container = jQuery('<div/>'),
		async_result = assert.async();
		 
		widget.get = function(key) {
			return '[{"model": "muk_dms.directory", "id": 1, "name": "Root_Directory"},' +
			        '{"model": "muk_dms.directory", "id": 4, "name": "Images"},' +
			        '{"model": "muk_dms.directory", "id": 6, "name": "PNG"},' +
			        '{"model": "muk_dms.file", "id": 3, "name": "PNG_Sample"}]';
		};
		 
		widget.attachTo($container).then(function() {
			widget.renderElement();
			assert.deepEqual(
				$container.find('.oe_form_uri').map(function() {
					return jQuery.trim(jQuery(this).text())
				}).get(),
				["Root_Directory", "Images", "PNG", "PNG_Sample"],
				'Check if the widget shows the correct path.'
			);
			async_result();
		});

		 
    });
});
