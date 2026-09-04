import type { Context } from "https://edge.netlify.com";

export default async (request: Request, context: Context) => {
  const url = new URL(request.url);

  if (
    (request.method === "GET" || request.method === "HEAD") &&
    url.pathname === "/" &&
    url.search === "?ref=proof-of-usefulness"
  ) {
    return new Response(null, {
      status: 301,
      headers: { Location: `${url.origin}/` },
    });
  }

  return context.next();
};

export const config = { path: "/" };
