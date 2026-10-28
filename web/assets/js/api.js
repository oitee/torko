// Cache successful JSON answers in memory by full address.
const cache = new Map();

// Clear the cache. Useful for tests.
export function clearCache() {
  cache.clear();
}

// Build the address with a query string from a params object.
function buildUrl(path, params) {
  if (!params) {
    return path;
  }
  const searchParams = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === null || value === undefined || value === "") {
      continue;
    }
    if (Array.isArray(value)) {
      // The API reads a list as one comma list, for example term=16,17.
      const items = value.filter((item) => item !== null && item !== undefined && item !== "");
      if (items.length > 0) {
        searchParams.append(key, items.join(","));
      }
    } else {
      searchParams.append(key, String(value));
    }
  }
  const queryString = searchParams.toString();
  if (!queryString) {
    return path;
  }
  return path.includes("?") ? `${path}&${queryString}` : `${path}?${queryString}`;
}

// Fetch JSON from the API with timeout, caching, and error handling.
export async function getJSON(path, params, options) {
  const url = buildUrl(path, params);
  const userSignal = options?.signal;

  if (userSignal?.aborted) {
    throw userSignal.reason || new DOMException("The operation was aborted.", "AbortError");
  }

  if (cache.has(url)) {
    return cache.get(url);
  }

  const controller = new AbortController();
  let didTimeout = false;
  let didUserAbort = false;

  const timeoutId = setTimeout(() => {
    didTimeout = true;
    controller.abort();
  }, 20000);

  const onUserAbort = () => {
    didUserAbort = true;
    controller.abort(userSignal.reason);
  };

  if (userSignal) {
    userSignal.addEventListener("abort", onUserAbort, { once: true });
  }

  try {
    const response = await fetch(url, { signal: controller.signal });
    if (!response.ok) {
      if (response.status === 404) {
        throw { status: 404, message: "Not found" };
      }
      throw {
        status: response.status,
        message: "The server could not answer. Try again.",
      };
    }
    const data = await response.json();
    cache.set(url, data);
    return data;
  } catch (error) {
    if (didUserAbort || userSignal?.aborted) {
      throw userSignal.reason || error;
    }
    if (didTimeout) {
      throw {
        status: 0,
        message: "The server took too long to answer. Try again.",
      };
    }
    if (error && typeof error === "object" && "status" in error) {
      throw error;
    }
    throw {
      status: 0,
      message: "Torko could not reach the server. Check the connection and try again.",
    };
  } finally {
    clearTimeout(timeoutId);
    if (userSignal) {
      userSignal.removeEventListener("abort", onUserAbort);
    }
  }
}
