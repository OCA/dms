/* Copyright 2024 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Field} from "@web/views/fields/field";
import {visitXML} from "@web/core/utils/xml";

export class DmsListArchParser {
    parseFieldNode(node, models, modelName) {
        return Field.parseFieldNode(node, models, modelName, "dms_list");
    }

    parse(xmlDoc, models, modelName) {
        const fieldNodes = {};
        const fieldNextIds = {};
        visitXML(xmlDoc, (node) => {
            if (node.tagName === "field") {
                const fieldInfo = this.parseFieldNode(node, models, modelName);
                if (!(fieldInfo.name in fieldNextIds)) {
                    fieldNextIds[fieldInfo.name] = 0;
                }
                const fieldId = `${fieldInfo.name}_${fieldNextIds[fieldInfo.name]++}`;
                fieldNodes[fieldId] = fieldInfo;
                node.setAttribute("field_id", fieldId);
                return false;
            }
        });
        return {
            fieldNodes,
            xmlDoc,
        };
    }
}
