/** @odoo-module */

import {registry} from "@web/core/registry";
import {DmsListController} from "./dms_list_controller.esm";
import {DmsListArchParser} from "./dms_list_arch_parser.esm";
import {RelationalModel} from "@web/views/relational_model";
import {DmsListRenderer} from "./dms_list_renderer.esm";

export const dmsListView = {
    type: "dms_list",
    display_name: "Dms Tree",
    icon: "fa fa-file-o",
    multiRecord: true,
    Controller: DmsListController,
    ArchParser: DmsListArchParser,
    Renderer: DmsListRenderer,
    Model: RelationalModel,

    props(genericProps, view) {
        const {ArchParser} = view;
        const {arch, relatedModels, resModel} = genericProps;
        const archInfo = new ArchParser().parse(arch, relatedModels, resModel);

        return {
            ...genericProps,
            Model: view.Model,
            Renderer: view.Renderer,
            archInfo,
        };
    },
};

registry.category("views").add("dms_list", dmsListView);
