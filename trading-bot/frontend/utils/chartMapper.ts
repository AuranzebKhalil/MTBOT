// Types matching Backend Pydantic Models
export type AnnotationShape = 
  | "HORIZONTAL_LINE" 
  | "VERTICAL_LINE" 
  | "ZONE_RECTANGLE" 
  | "MARKER_UP" 
  | "MARKER_DOWN" 
  | "MARKER_DOT" 
  | "LABEL";

export type AnnotationStyle = 
  | "BULLISH" 
  | "BEARISH" 
  | "NEUTRAL" 
  | "RISK_STOP" 
  | "TARGET_PROFIT" 
  | "INFO";

export interface ChartAnnotation {
    id: string;
    concept_type: string;
    shape: AnnotationShape;
    style: AnnotationStyle;
    time1: number;
    price1: number;
    time2?: number;
    price2?: number;
    text?: string;
    layer_priority: number;
    is_active: boolean;
    metadata_fields: Record<string, any>;
}

export interface TradeChartPayload {
    ticket_id: number;
    symbol: string;
    timeframe: string;
    bars_start_time: number;
    bars_end_time: number;
    annotations: ChartAnnotation[];
}

// Lightweight Charts Mapping Utils

export function getStyleColor(style: AnnotationStyle, opacity: number = 1.0): string {
    const alpha = Math.round(opacity * 255).toString(16).padStart(2, '0');
    switch (style) {
        case "BULLISH": return `#2196F3${alpha}`;      // Blue
        case "BEARISH": return `#F44336${alpha}`;      // Red
        case "NEUTRAL": return `#9E9E9E${alpha}`;      // Gray
        case "RISK_STOP": return `#FF9800${alpha}`;    // Orange
        case "TARGET_PROFIT": return `#4CAF50${alpha}`;// Green
        case "INFO": return `#9C27B0${alpha}`;         // Purple
        default: return `#FFFFFF${alpha}`;
    }
}

/**
 * Converts a backend ChartAnnotation into a Lightweight Charts Marker
 */
export function mapToMarker(ann: ChartAnnotation): any {
    if (!["MARKER_UP", "MARKER_DOWN", "MARKER_DOT"].includes(ann.shape)) return null;

    let position = 'inBar';
    let shape = 'circle';
    let color = getStyleColor(ann.style);

    if (ann.shape === "MARKER_UP") {
        position = 'belowBar';
        shape = 'arrowUp';
    } else if (ann.shape === "MARKER_DOWN") {
        position = 'aboveBar';
        shape = 'arrowDown';
    }

    return {
        time: ann.time1,
        position: position,
        color: color,
        shape: shape,
        text: ann.text || '',
        id: ann.id
    };
}

/**
 * Example utility to draw price lines (Entry, SL, TP) onto a candlestick series
 */
export function drawHorizontalLine(series: any, ann: ChartAnnotation) {
    if (ann.shape !== "HORIZONTAL_LINE") return null;

    return series.createPriceLine({
        price: ann.price1,
        color: getStyleColor(ann.style, 0.8),
        lineWidth: 2,
        lineStyle: 2, // 0 = Solid, 1 = Dotted, 2 = Dashed
        title: ann.text || ann.concept_type,
        axisLabelVisible: true,
    });
}
