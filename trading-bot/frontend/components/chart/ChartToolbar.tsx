import React from 'react';

interface ChartToolbarProps {
    visibleConcepts: string[];
    setVisibleConcepts: (concepts: string[]) => void;
    compactMode: boolean;
    setCompactMode: (mode: boolean) => void;
}

export const ChartToolbar: React.FC<ChartToolbarProps> = ({ 
    visibleConcepts, 
    setVisibleConcepts,
    compactMode,
    setCompactMode 
}) => {
    
    const toggleConcept = (concept: string) => {
        if (visibleConcepts.includes(concept)) {
            setVisibleConcepts(visibleConcepts.filter(c => c !== concept));
        } else {
            setVisibleConcepts([...visibleConcepts, concept]);
        }
    };

    return (
        <div className="flex gap-4 p-2 bg-gray-900 border-b border-gray-800 text-sm">
            <button 
                onClick={() => setCompactMode(!compactMode)}
                className={`px-3 py-1 rounded transition-colors ${compactMode ? 'bg-blue-600' : 'bg-gray-800 hover:bg-gray-700'}`}
            >
                {compactMode ? "Compact Mode" : "Detailed Mode"}
            </button>
            
            {!compactMode && (
                <>
                    <button 
                        onClick={() => toggleConcept("ZONES")}
                        className={`px-3 py-1 rounded transition-colors ${visibleConcepts.includes("ZONES") ? 'bg-purple-600' : 'bg-gray-800'}`}
                    >
                        OB & FVGs
                    </button>
                    <button 
                        onClick={() => toggleConcept("LEVELS")}
                        className={`px-3 py-1 rounded transition-colors ${visibleConcepts.includes("LEVELS") ? 'bg-blue-600' : 'bg-gray-800'}`}
                    >
                        Lines & Levels
                    </button>
                    <button 
                        onClick={() => toggleConcept("MARKERS")}
                        className={`px-3 py-1 rounded transition-colors ${visibleConcepts.includes("MARKERS") ? 'bg-green-600' : 'bg-gray-800'}`}
                    >
                        Pivots & Entries
                    </button>
                </>
            )}
        </div>
    );
};
