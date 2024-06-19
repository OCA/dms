/** @odoo-module */
/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {addFieldDependencies} from "@web/views/utils";
import {Field} from "@web/views/fields/field";
import {XMLParser} from "@web/core/utils/xml";

export class DmsListArchParser extends XMLParser {
    parseFieldNode(node, models, modelName) {
        return Field.parseFieldNode(node, models, modelName, "dms_list");
    }

    parse(arch, models, modelName) {
        const fieldNodes = {};
        const activeFields = {};
        this.visitXML(arch, (node) => {
            if (node.tagName === "field") {
                const fieldInfo = this.parseFieldNode(node, models, modelName);
                fieldNodes[fieldInfo.name] = fieldInfo;
                node.setAttribute("field_id", fieldInfo.name);
                addFieldDependencies(
                    activeFields,
                    models[modelName],
                    fieldInfo.FieldComponent.fieldDependencies
                );
                return false;
            }
        });
        for (const [key, field] of Object.entries(fieldNodes)) {
            activeFields[key] = field; // TODO process
        }
        return {
            activeFields,
            __rawArch: arch,
        };
    }
}
