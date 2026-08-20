/** @odoo-module **/

import {registry} from "@web/core/registry";
import {patch} from "@web/core/utils/patch";

async function openDmsUiWorkspaceList(renderer, domain, context) {
    if (!context?.dms_ui_workspace) {
        return false;
    }
    await renderer.env.searchModel.splitAndAddDomain(domain);
    await renderer.actionService.switchView("list");
    return true;
}

function patchOptionalWorkspaceDrilldown(viewType) {
    let view = false;
    try {
        view = registry.category("views").get(viewType);
    } catch {
        return;
    }
    const Renderer = view?.Renderer;
    if (!Renderer?.prototype) {
        return;
    }
    patch(Renderer.prototype, {
        async openView(domain, views, context) {
            if (await openDmsUiWorkspaceList(this, domain, context)) {
                return;
            }
            return super.openView(...arguments);
        },
    });
}

patchOptionalWorkspaceDrilldown("graph");
patchOptionalWorkspaceDrilldown("pivot");
