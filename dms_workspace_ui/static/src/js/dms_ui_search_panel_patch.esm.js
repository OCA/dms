/** @odoo-module **/

import {onMounted, useExternalListener} from "@odoo/owl";
import {browser} from "@web/core/browser/browser";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {SearchPanel} from "@web/search/search_panel/search_panel";
import {TREE_STATE_KEY} from "@dms_workspace_ui/js/dms_ui_core.esm";
import {DmsSearchPanelController} from "@dms_workspace_ui/js/dms_ui_search_panel_controller.esm";

patch(SearchPanel.prototype, {
    setup() {
        super.setup(...arguments);
        this.dmsUiWorkspace = useService("dms_ui_workspace");
        this.dmsUiDialog = useService("dialog");
        this.dmsUiNotification = useService("notification");
        this.dmsUiOrm = useService("orm");
        this.dmsUiTypeahead = {query: "", updatedAt: 0};
        this.dmsUiController = new DmsSearchPanelController(this);
        if (this.dmsUiUsesRegularSearchPanel()) {
            this.state.sidebarExpanded = true;
        }
        onMounted(() => this.dmsUiController.installSearchPanelWidthMemory());
        useExternalListener(window, "resize", () => {
            this.dmsUiController.reconcileSearchPanelWidth();
        });
        useExternalListener(window, "focusin", (event) => {
            const header = event.target.closest?.(".dms_ui_directory_header");
            if (header && this.root?.el?.contains(header)) {
                this.dmsUiWorkspace.rememberFocus(
                    this.dmsUiController.focusTokenForHeader(header),
                    this.dmsUiController.focusSnapshotOptionsForHeader(header)
                );
            }
        });
    },

    dmsUiUsesRegularSearchPanel() {
        return this.dmsUiController?.usesRegularSearchPanel() || false;
    },

    _onStartResize(ev) {
        this.dmsUiController.onStartResize(ev);
    },

    expandDefaultValue() {
        super.expandDefaultValue(...arguments);
        for (const section of this.sections) {
            if (!this.dmsUiController.isDirectorySection(section)) {
                continue;
            }
            this.state.expanded[section.id] = {};
            try {
                const expanded = JSON.parse(
                    browser.localStorage.getItem(TREE_STATE_KEY) || "[]"
                );
                for (const valueId of expanded) {
                    if (section.values.has(valueId)) {
                        this.state.expanded[section.id][valueId] = true;
                    }
                }
            } catch {
                browser.localStorage.removeItem(TREE_STATE_KEY);
            }
        }
    },

    async toggleCategory(section, value) {
        if (!this.dmsUiController.isDirectorySection(section) || !value) {
            return super.toggleCategory(...arguments);
        }
        this.dmsUiController.selectDirectory(section, value);
        await super.toggleCategory(...arguments);
        this.dmsUiController.persistExpanded(section);
    },

    dmsUiOnFolderKeydown(section, value, event) {
        this.dmsUiController.onFolderKeydown(section, value, event);
    },

    clearSelection(sectionId = 0) {
        const clearsDirectory =
            !sectionId ||
            this.sections.some(
                (section) =>
                    section.id === sectionId &&
                    this.dmsUiController.isDirectorySection(section)
            );
        const result = super.clearSelection(...arguments);
        if (clearsDirectory) {
            this.dmsUiWorkspace.selectDirectory(false);
        }
        return result;
    },

    dmsUiOpenFolderContextMenu(section, value, event) {
        this.dmsUiController.openFolderContextMenu(section, value, event);
    },
});
