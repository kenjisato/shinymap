export declare const neutrals: {
    stroke: string;
    strokeActive: string;
    fill: string;
};
export declare const qualitative: string[];
export declare const sequential: {
    blue: string[];
    green: string[];
    orange: string[];
};
export type Palette = {
    neutrals: typeof neutrals;
    qualitative: string[];
    sequential: typeof sequential;
};
export declare const palette: Palette;
