import React, { useEffect, useState } from 'react';
import { ChartAnnotation, mapToMarker, drawHorizontalLine } from '../../utils/chartMapper';

interface AnnotationRendererProps {
    series: any; // Lightweight Charts ISeriesApi instance
    annotations: ChartAnnotation[];
    visibleConcepts: string[]; // e.g. ["ZONES", "LEVELS", "MARKERS"]
}

export const AnnotationRenderer: React.FC<AnnotationRendererProps> = ({ series, annotations, visibleConcepts }) => {
    const [activeLines, setActiveLines] = useState<any[]>([]);

    useEffect(() => {
        if (!series) return;

        // Clean up previous primitives
        activeLines.forEach(line => series.removePriceLine(line));
        const newLines: any[] = [];
        const markers: any[] = [];

        annotations.forEach(ann => {
            // Respect Filter Toggles
            if (ann.shape.includes("MARKER") && !visibleConcepts.includes("MARKERS")) return;
            if (ann.shape === "HORIZONTAL_LINE" && !visibleConcepts.includes("LEVELS")) return;
            if (ann.shape.includes("ZONE") && !visibleConcepts.includes("ZONES")) return;

            // Render Price Lines
            if (ann.shape === "HORIZONTAL_LINE") {
                const line = drawHorizontalLine(series, ann);
                if (line) newLines.push(line);
            }

            // Render Markers
            if (ann.shape.includes("MARKER")) {
                const marker = mapToMarker(ann);
                if (marker) markers.push(marker);
            }

            // Note: ZONE_RECTANGLE typically requires Canvas API plugins with Lightweight Charts
            // This is handled via custom `series.attachPrimitive()` in a real LC v4 implemention
        });

        // Batch update markers
        // Sort markers by time as required by Lightweight Charts
        markers.sort((a, b) => a.time - b.time);
        series.setMarkers(markers);
        setActiveLines(newLines);

        return () => {
            newLines.forEach(line => series.removePriceLine(line));
        };
    }, [series, annotations, visibleConcepts]);

    return null; // Purely a rendering engine for the chart instance
};
