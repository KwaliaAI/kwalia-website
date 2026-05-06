import type { Context } from "https://edge.netlify.com";

const REALM = 'Basic realm="Google Books Fetch"';

function logFetchAttempt(
  request: Request,
  status: number,
  authState: "missing" | "malformed" | "invalid" | "ok",
  responseStatus?: number,
) {
  const url = new URL(request.url);
  console.log(
    JSON.stringify({
      event: "google_fetch_auth",
      ts: new Date().toISOString(),
      method: request.method,
      path: url.pathname,
      status,
      response_status: responseStatus ?? status,
      auth_state: authState,
      user_agent: request.headers.get("user-agent") || "",
      referer: request.headers.get("referer") || "",
    }),
  );
}

export default async (request: Request, context: Context) => {
  const expectedUser = Deno.env.get("GOOGLE_FETCH_USER") || "googlebooks";
  const expectedPass = Deno.env.get("GOOGLE_FETCH_PASS") || "";

  if (!expectedPass) {
    logFetchAttempt(request, 503, "invalid");
    return new Response("Fetch endpoint not configured", { status: 503 });
  }

  const authHeader = request.headers.get("authorization") || "";
  if (!authHeader.startsWith("Basic ")) {
    logFetchAttempt(request, 401, "missing");
    return new Response("Authentication required", {
      status: 401,
      headers: { "WWW-Authenticate": REALM },
    });
  }

  let decoded = "";
  try {
    decoded = atob(authHeader.slice(6));
  } catch {
    logFetchAttempt(request, 401, "malformed");
    return new Response("Invalid credentials", {
      status: 401,
      headers: { "WWW-Authenticate": REALM },
    });
  }

  const separator = decoded.indexOf(":");
  const user = separator >= 0 ? decoded.slice(0, separator) : decoded;
  const pass = separator >= 0 ? decoded.slice(separator + 1) : "";

  if (user !== expectedUser || pass !== expectedPass) {
    logFetchAttempt(request, 401, "invalid");
    return new Response("Invalid credentials", {
      status: 401,
      headers: { "WWW-Authenticate": REALM },
    });
  }

  const response = await context.next();
  logFetchAttempt(request, 200, "ok", response.status);
  return response;
};

export const config = { path: "/fetch/*" };
