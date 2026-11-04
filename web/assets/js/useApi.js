import { useEffect, useState } from "react";
import { getJSON } from "./api.js";

// Run one API call when its key changes. A null key runs no call.
// A new call cancels the call before it, so an old answer cannot replace a new one.
// The last answer stays while the next one loads. dataKey is the key of that answer.
export function useApi(key, load) {
  const [state, setState] = useState({ key: null, data: null, loading: false, error: null });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!key) {
      setState({ key: null, data: null, loading: false, error: null });
      return undefined;
    }
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    load(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setState({ key, data, loading: false, error: null });
      })
      .catch((error) => {
        if (!controller.signal.aborted) setState((s) => ({ ...s, key, loading: false, error }));
      });
    return () => controller.abort();
  }, [key, retry]);
  return {
    data: state.data,
    dataKey: state.key,
    error: state.error,
    // The render before the effect has the new key and the old state. That render is also loading.
    loading: state.loading || (Boolean(key) && state.key !== key),
    retry: () => setRetry((n) => n + 1),
  };
}

// Load one API answer by its path and its params. A null path loads nothing.
export function useAnswer(path, params) {
  const key = path ? `${path}?${JSON.stringify(params ?? null)}` : null;
  return useApi(key, (signal) => getJSON(path, params, { signal }));
}
