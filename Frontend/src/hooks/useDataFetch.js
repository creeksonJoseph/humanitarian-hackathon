import { useState, useEffect, useRef } from 'react';

const cache = new Map();
const CACHE_DURATION = 30000;

export function useDataFetch(fetchFn, dependencies = [], cacheKey = null) {
    const [data, setData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const abortController = useRef(null);

    useEffect(() => {
        const fetchData = async () => {
            if (abortController.current) abortController.current.abort();
            abortController.current = new AbortController();

            const key = cacheKey || JSON.stringify(dependencies);
            const cached = cache.get(key);
            
            if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
                setData(cached.data);
                setIsLoading(false);
                return;
            }

            setIsLoading(true);
            try {
                const result = await fetchFn();
                cache.set(key, { data: result, timestamp: Date.now() });
                setData(result);
                setError(null);
            } catch (err) {
                if (err.name !== 'AbortError') {
                    setError(err);
                }
            } finally {
                setIsLoading(false);
            }
        };

        fetchData();
        return () => abortController.current?.abort();
    }, dependencies);

    return { data, isLoading, error };
}
