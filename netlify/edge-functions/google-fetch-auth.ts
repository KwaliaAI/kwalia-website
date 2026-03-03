import type { Context } from "@netlify/edge-functions";

const REALM = 'Basic realm="Google Books Fetch"';

export default async (request: Request, context: Context) => {
  const expectedUser = Netlify.env.get("GOOGLE_FETCH_USER") || "googlebooks";
  const expectedPass = Netlify.env.get("GOOGLE_FETCH_PASS") || "";

  if (!expectedPass) {
    return new Response("Fetch endpoint not configured", { status: 503 });
  }

  const authHeader = request.headers.get("authorization") || "";
  if (!authHeader.startsWith("Basic ")) {
    return new Response("Authentication required", {
      status: 401,
      headers: { "WWW-Authenticate": REALM },
    });
  }

  let decoded = "";
  try {
    decoded = atob(authHeader.slice(6));
  } catch {
    return new Response("Invalid credentials", {
      status: 401,
      headers: { "WWW-Authenticate": REALM },
    });
  }

  const separator = decoded.indexOf(":");
  const user = separator >= 0 ? decoded.slice(0, separator) : decoded;
  const pass = separator >= 0 ? decoded.slice(separator + 1) : "";

  if (user !== expectedUser || pass !== expectedPass) {
    return new Response("Invalid credentials", {
      status: 401,
      headers: { "WWW-Authenticate": REALM },
    });
  }

  return context.next();
};
