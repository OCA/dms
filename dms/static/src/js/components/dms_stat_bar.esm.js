// Copyright 2026 ledoent — Don Kendall
// License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import {Component} from "@odoo/owl";

// Reusable stat bar. Driven by a `stats` prop shaped like:
//   {files_total, storage_total_human, new_today,
//    files_sparkline, storage_sparkline, new_today_sparkline,
//    files_delta_week, storage_delta_week_human, new_today_avg_per_day}
// Tile config is declared inline so future dashboards (Phase 3+) can extend
// or remix the same component by passing a different `tiles` prop. Each tile
// names the value key, sparkline key, delta key, and a `chart` hint that
// picks the SVG renderer (line vs bar).
const SPARK_WIDTH = 80;
const SPARK_HEIGHT = 26;

const DEFAULT_TILES = [
    {
        key: "files_total",
        label: "Files",
        icon: "fa-file-text-o",
        tint: "files",
        sparklineKey: "files_sparkline",
        chart: "line",
        deltaKey: "files_delta_week",
        deltaSuffix: " this week",
        deltaTrend: "up",
    },
    {
        key: "storage_total_human",
        label: "Storage",
        icon: "fa-database",
        tint: "storage",
        sparklineKey: "storage_sparkline",
        chart: "bar",
        deltaKey: "storage_delta_week_human",
        deltaSuffix: " added this week",
        deltaTrend: "neutral",
    },
    {
        key: "new_today",
        label: "New today",
        icon: "fa-clock-o",
        tint: "fresh",
        sparklineKey: "new_today_sparkline",
        chart: "line",
        deltaKey: "new_today_avg_per_day",
        deltaPrefix: "vs avg ",
        deltaSuffix: "/day",
        deltaTrend: "neutral",
    },
];

export class DmsStatBar extends Component {
    static template = "dms.StatBar";
    static props = {
        stats: {type: [Object, {value: null}], optional: true},
        tiles: {type: Array, optional: true},
    };
    static defaultProps = {
        tiles: DEFAULT_TILES,
    };

    get isLoading() {
        return !this.props.stats;
    }

    valueFor(tile) {
        if (this.isLoading) {
            return "—";
        }
        const raw = this.props.stats[tile.key];
        return raw === undefined || raw === null ? "—" : raw;
    }

    // Returns {points, polygon, max, min, hasData} for the tile's series.
    // Empty / all-zero series → hasData=false so the template can skip the
    // chart and still keep the tile's vertical rhythm.
    sparkPath(tile) {
        if (this.isLoading || !tile.sparklineKey) {
            return {hasData: false};
        }
        const series = this.props.stats[tile.sparklineKey];
        if (!Array.isArray(series) || series.length === 0) {
            return {hasData: false};
        }
        const max = Math.max(...series, 0);
        const min = Math.min(...series, 0);
        const range = max - min || 1;
        const stepX = series.length > 1 ? SPARK_WIDTH / (series.length - 1) : 0;
        const points = series.map((v, i) => {
            const x = +(i * stepX).toFixed(2);
            const y = +(SPARK_HEIGHT - ((v - min) / range) * SPARK_HEIGHT).toFixed(2);
            return {x, y, value: v};
        });
        const linePath = points.map((p) => `${p.x},${p.y}`).join(" ");
        const areaPath = `0,${SPARK_HEIGHT} ${linePath} ${SPARK_WIDTH},${SPARK_HEIGHT}`;
        const barWidth = series.length ? (SPARK_WIDTH / series.length) * 0.7 : 0;
        const bars = points.map((p, i) => ({
            x: +(i * (SPARK_WIDTH / series.length)).toFixed(2),
            y: p.y,
            width: barWidth,
            height: +(SPARK_HEIGHT - p.y).toFixed(2),
        }));
        return {
            hasData: max > 0,
            points,
            linePath,
            areaPath,
            bars,
            last: points[points.length - 1],
        };
    }

    deltaText(tile) {
        if (this.isLoading || !tile.deltaKey) {
            return "";
        }
        const raw = this.props.stats[tile.deltaKey];
        if (raw === undefined || raw === null) {
            return "";
        }
        const prefix = tile.deltaPrefix || "";
        const suffix = tile.deltaSuffix || "";
        return `${prefix}${raw}${suffix}`;
    }

    sparkWidth() {
        return SPARK_WIDTH;
    }

    sparkHeight() {
        return SPARK_HEIGHT;
    }
}
