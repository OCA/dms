/* Copyright 2025 Carlos Roca - Tecnativa
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {DMSSelector} from "./dms_selector.esm";
import {MediaDialog} from "@html_editor/main/media/media_dialog/media_dialog";
import {TABS} from "@html_editor/main/media/media_dialog/media_dialog_utils";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

TABS.DMS = {
    id: "DMS",
    title: _t("DMS"),
    Component: DMSSelector,
    sequence: 40,
};

patch(MediaDialog.prototype, {
    get initialActiveTab() {
        const dmsTab = this.tabs.DMS;
        if (
            !this.props.activeTab &&
            dmsTab &&
            this.props.media &&
            this.props.media.classList.contains("o_dms_file")
        ) {
            return dmsTab.id;
        }
        return super.initialActiveTab;
    },
    addTabs() {
        const res = super.addTabs(...arguments);
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
