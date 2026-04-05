"use client";
import { useState, useEffect } from 'react';

export function useMediaQuery(query) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const list = window.matchMedia(query);
    setMatches(list.matches);

    const listener = (event) => setMatches(event.matches);
    list.addEventListener('change', listener);

    return () => list.removeEventListener('change', listener);
  }, [query]);

  return matches;
}
