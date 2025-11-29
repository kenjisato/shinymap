// Lightweight palette helpers (no dependencies).
export const neutrals = {
    stroke: "#1f2937", // slate-800
    strokeActive: "#0f172a", // slate-900
    fill: "#e2e8f0", // slate-200
};
export const qualitative = [
    "#2563eb", // blue-600
    "#16a34a", // green-600
    "#f59e0b", // amber-500
    "#ef4444", // red-500
    "#a855f7", // purple-500
    "#06b6d4", // cyan-500
];
export const sequential = {
    blue: ["#eff6ff", "#bfdbfe", "#93c5fd", "#60a5fa", "#3b82f6", "#2563eb", "#1d4ed8"],
    green: ["#ecfdf3", "#bbf7d0", "#86efac", "#4ade80", "#22c55e", "#16a34a", "#15803d"],
    orange: ["#fff7ed", "#ffedd5", "#fed7aa", "#fdba74", "#fb923c", "#f97316", "#c2410c"],
};
// TODO: Extend palettes to cover popular schemes as needs emerge.
export const palette = {
    neutrals,
    qualitative,
    sequential,
};
