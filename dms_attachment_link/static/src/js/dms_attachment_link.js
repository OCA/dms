odoo.define("dms_attachment_link", function (require) {
    "use strict";

    var AttachmentBox = require("mail.AttachmentBox");

    AttachmentBox.include({
        events: _.extend(AttachmentBox.prototype.events, {
            "click span.o_add_dms_file_button": "_onAddDmsFile",
        }),
        _onAddDmsFile: function () {
            this.do_action(
                "dms_attachment_link.action_dms_file_wizard_selector_dms_attachment_link",
                {
                    additional_context: {
                        active_id: this.currentResID,
                        active_ids: [this.currentResID],
                        active_model: this.currentResModel,
                    },
                    on_close: this._onAddedUrl.bind(this),
                }
            );
        },
        _onAddedUrl: function () {
            this.trigger_up("reload_attachment_box");
        },
    });
});
