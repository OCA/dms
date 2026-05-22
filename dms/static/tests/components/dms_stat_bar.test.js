// /** ********************************************************************************
//     Copyright 2026 ledoent — Don Kendall
//     License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
//
//     Verifies the DmsStatBar pure-logic getters (isLoading, valueFor,
//     sparkPath, deltaText). The component is mounted-tested implicitly
//     via the directory kanban renderer test (separate file); here we lock
//     down the pure-function contract for the sparkline geometry + delta
//     interpolation so a regression won't silently make sparklines invisible
//     or flat.
//  **********************************************************************************/
import {describe, expect, test} from "@odoo/hoot";
import {DmsStatBar} from "@dms/js/components/dms_stat_bar.esm";

// Instantiate without mounting — we only test pure-function logic on the
// prototype. Components in OWL 2 still resolve `this.props` through Object
// access, so a plain object stand-in is enough for the assertions below.
function _instance(stats, tiles = undefined) {
    const inst = Object.create(DmsStatBar.prototype);
    inst.props = {
        stats: stats,
        tiles: tiles ?? DmsStatBar.defaultProps.tiles,
    };
    return inst;
}

describe("isLoading", () => {
    test("true when stats is null", () => {
        expect(_instance(null).isLoading).toBe(true);
    });

    test("false when stats is present", () => {
        expect(_instance({files_total: 5}).isLoading).toBe(false);
    });
});

describe("valueFor", () => {
    test("returns em-dash when loading", () => {
        const inst = _instance(null);
        const tile = {key: "files_total"};
        expect(inst.valueFor(tile)).toBe("—");
    });

    test("returns the raw stats value by tile.key", () => {
        const inst = _instance({files_total: 1247});
        expect(inst.valueFor({key: "files_total"})).toBe(1247);
    });

    test("returns em-dash for missing key", () => {
        const inst = _instance({});
        expect(inst.valueFor({key: "absent"})).toBe("—");
    });
});

describe("sparkPath — line chart", () => {
    test("returns hasData=false when series is missing", () => {
        const inst = _instance({files_total: 5});
        const tile = {sparklineKey: "absent_series"};
        expect(inst.sparkPath(tile).hasData).toBe(false);
    });

    test("returns hasData=false for an all-zero series", () => {
        const inst = _instance({zeros: [0, 0, 0, 0]});
        const tile = {sparklineKey: "zeros"};
        // Max=0 → hasData reads as false (the template skips the chart).
        expect(inst.sparkPath(tile).hasData).toBe(false);
    });

    test("returns a points array + line path for a non-empty series", () => {
        const inst = _instance({s: [0, 5, 10]});
        const tile = {sparklineKey: "s", chart: "line"};
        const result = inst.sparkPath(tile);
        expect(result.hasData).toBe(true);
        expect(result.points.length).toBe(3);
        // First point sits at the left edge.
        expect(result.points[0].x).toBe(0);
        // Last point sits at the right edge (80px stat-bar width).
        expect(result.points[2].x).toBe(80);
        // Series max maps to the top of the chart (y=0).
        expect(result.points[2].y).toBe(0);
        // `linePath` is a space-separated set of "x,y" pairs.
        expect(result.linePath.split(" ").length).toBe(3);
    });

    test("areaPath closes the polygon at the baseline", () => {
        const inst = _instance({s: [1, 2, 3]});
        const tile = {sparklineKey: "s"};
        const result = inst.sparkPath(tile);
        // Area path starts at 0,26 (bottom-left) and ends at 80,26 (bottom-
        // right) so the SVG polygon fills downward to the baseline.
        expect(result.areaPath.startsWith("0,26 ")).toBe(true);
        expect(result.areaPath.endsWith(" 80,26")).toBe(true);
    });
});

describe("sparkPath — bar chart", () => {
    test("returns bar rectangles with width = 70% of slot", () => {
        const inst = _instance({s: [1, 2, 3]});
        const tile = {sparklineKey: "s", chart: "bar"};
        const result = inst.sparkPath(tile);
        expect(result.bars.length).toBe(3);
        // Each slot is 80/3 ≈ 26.67px; bar fills 70% → ~18.67.
        expect(result.bars[0].width).toBeCloseTo(18.67, 1);
    });
});

describe("deltaText", () => {
    test("returns empty string when loading", () => {
        const inst = _instance(null);
        const tile = {deltaKey: "files_delta_week", deltaSuffix: " this week"};
        expect(inst.deltaText(tile)).toBe("");
    });

    test("interpolates prefix + value + suffix", () => {
        const inst = _instance({new_today_avg_per_day: 14.2});
        const tile = {
            deltaKey: "new_today_avg_per_day",
            deltaPrefix: "vs avg ",
            deltaSuffix: "/day",
        };
        expect(inst.deltaText(tile)).toBe("vs avg 14.2/day");
    });

    test("returns empty string when delta value is undefined", () => {
        const inst = _instance({});
        const tile = {deltaKey: "missing"};
        expect(inst.deltaText(tile)).toBe("");
    });
});
