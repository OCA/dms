/** @odoo-module **/

import {MediaDialog, TABS} from "@web_editor/components/media_dialog/media_dialog";
import {DMSSelector} from "./dms_selector.esm";
import {patch} from "@web/core/utils/patch";

patch(TABS, "web_editor_media_dialog_dms.TABS", {
    DMS: {
        id: "DMS",
        title: "DMS",
        Component: DMSSelector,
    },
});

patch(MediaDialog.prototype, "web_editor_media_dialog_dms.MediaDialog", {
    get initialActiveTab() {
        const dmsTab = this.tabs.find((tab) => tab.id === "DMS");
        if (
            !this.props.activeTab &&
            dmsTab &&
            this.props.media &&
            this.props.media.classList.contains("o_dms_file")
        ) {
            return dmsTab.id;
        }
        return this._super(...arguments);
    },
    addTabs() {
        const res = this._super(...arguments);
        const onlyImages =
            this.props.onlyImages ||
            this.props.multiImages ||
            (this.props.media &&
                this.props.media.parentElement &&
                (this.props.media.parentElement.dataset.oeField === "image" ||
                    this.props.media.parentElement.dataset.oeType === "image"));
        const noDMS = onlyImages || this.props.noDMS;
        if (!noDMS) {
            this.addTab(TABS.DMS);
        }
        return res;
    },
});
