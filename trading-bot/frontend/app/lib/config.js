export const getApiBaseUrl = () => {
  // We use Next.js rewrites to proxy /api to localhost:8000
  // This avoids CORS issues and firewall port 8000 issues on mobile
  return "/api";
};

export const getDirectApiBaseUrl = () => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname || "localhost";
    return `http://${hostname}:8000/api`;
  }
  return "http://localhost:8000/api";
};

export const getWsBaseUrl = () => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // For WS we still need the absolute address as Next.js doesn't proxy WS easily in dev
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return `ws://${hostname}:8000`;
    }
  }
  return "ws://localhost:8000";
};
