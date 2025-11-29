import type React from "react";
export type RegionId = string;
export type GeometryMap = Record<RegionId, string>;
export type TooltipMap = Record<RegionId, string>;
type BaseInputProps = {
    geometry: GeometryMap;
    tooltips?: TooltipMap;
    viewBox?: string;
    className?: string;
    style?: React.CSSProperties;
    defaultFill?: string;
    stroke?: string;
    highlightFill?: string;
    hoverFill?: string;
};
export type SingleSelectionProps = BaseInputProps & {
    mode?: "single";
    value?: RegionId | null;
    onChange?: (value: RegionId | null) => void;
};
export type MultipleSelectionProps = BaseInputProps & {
    mode: "multiple";
    value?: RegionId[];
    onChange?: (value: RegionId[]) => void;
};
export type CountSelectionProps = BaseInputProps & {
    mode: "count";
    value?: Record<RegionId, number>;
    onChange?: (value: Record<RegionId, number>) => void;
    maxCount?: number;
};
export type InputMapProps = SingleSelectionProps | MultipleSelectionProps | CountSelectionProps;
type BaseOutputProps = {
    geometry: GeometryMap;
    tooltips?: TooltipMap;
    viewBox?: string;
    className?: string;
    style?: React.CSSProperties;
    defaultFill?: string;
    stroke?: string;
};
export type OutputMapProps = BaseOutputProps & {
    fills?: Record<RegionId, string>;
    activeIds?: RegionId | RegionId[] | null;
    onRegionClick?: (id: RegionId) => void;
    styleForRegion?: (args: {
        id: RegionId;
        baseFill: string;
        isActive: boolean;
        tooltip?: string;
    }) => {
        fill?: string;
        fillOpacity?: number;
        stroke?: string;
        strokeWidth?: number;
    };
};
export {};
