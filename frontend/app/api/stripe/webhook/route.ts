import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  const type = body?.type ?? "unknown";

  if (type === "checkout.session.completed") {
    return NextResponse.json({ ok: true, provisioned: true });
  }

  return NextResponse.json({ ok: true, ignored: true });
}
