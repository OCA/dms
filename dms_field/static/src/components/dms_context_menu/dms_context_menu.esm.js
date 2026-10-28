/* Copyright 2026 Tecnativa - Carlos Roca
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
import {Component, onMounted, signal, t, useProps} from "@odoo/owl";

/**
 * @typedef DmsAction
 * @property {String} key
 * @property {String} label
 * @property {String} icon Material Symbols icon name
 * @property {Boolean} [separatorBefore]
 * @property {Boolean} disabled
 * @property {() => any} run
 */

export class DmsContextMenu extends Component {
    static template = "dms_field.DmsContextMenu";

    props = useProps({
        /** @type {DmsAction[]} */
        actions: t.array(),
        // Given by the popover service
        close: t.function(),
    });

    rootRef = signal.ref();

    setup() {
        onMounted(() => this.getItems()[0]?.focus());
    }

    getItems() {
        return [
            ...(this.rootRef()?.querySelectorAll(".dropdown-item:not(:disabled)") ||
                []),
        ];
    }

    /**
     * @param {DmsAction} action
     */
    onClickAction(action) {
        if (action.disabled) {
            return;
        }
        this.props.close();
        action.run();
    }

    /**
     * @param {KeyboardEvent} ev
     */
    onKeydown(ev) {
        const items = this.getItems();
        if (!items.length) {
            return;
        }
        const index = items.indexOf(document.activeElement);
        let next = null;
        switch (ev.key) {
            case "ArrowDown":
                next = items[(index + 1) % items.length];
                break;
            case "ArrowUp":
                next = items[(index - 1 + items.length) % items.length];
                break;
            case "Home":
                next = items[0];
                break;
            case "End":
                next = items[items.length - 1];
                break;
            case "Tab":
                this.props.close();
                return;
            default:
                return;
        }
        ev.preventDefault();
        next.focus();
    }
}
