const DEFAULT_API_URL = "http://localhost:8000";
const API_BASE_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || DEFAULT_API_URL;

type Params = { params: Promise<{ id: string }> };

async function forward(method: string, id: string, body?: string): Promise<Response> {
  try {
    const upstreamResponse = await fetch(`${API_BASE_URL}/searches/${id}`, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body,
      cache: "no-store",
    });

    const responseText = await upstreamResponse.text();
    return new Response(responseText || null, {
      status: upstreamResponse.status,
      headers: {
        "Content-Type": upstreamResponse.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return Response.json({ detail: "Backend non raggiungibile dal frontend." }, { status: 502 });
  }
}

export async function PATCH(request: Request, { params }: Params): Promise<Response> {
  const { id } = await params;
  const body = await request.text();
  return forward("PATCH", id, body);
}

export async function DELETE(_request: Request, { params }: Params): Promise<Response> {
  const { id } = await params;
  return forward("DELETE", id);
}
