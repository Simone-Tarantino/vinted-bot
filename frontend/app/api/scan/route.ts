const DEFAULT_API_URL = "http://localhost:8000";
const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;

export async function POST(): Promise<Response> {
  try {
    const upstreamResponse = await fetch(`${API_BASE_URL}/scan/run`, {
      method: "POST",
      cache: "no-store",
    });
    const responseText = await upstreamResponse.text();
    return new Response(responseText, {
      status: upstreamResponse.status,
      headers: {
        "Content-Type": upstreamResponse.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return Response.json({ detail: "Backend non raggiungibile dal frontend." }, { status: 502 });
  }
}
