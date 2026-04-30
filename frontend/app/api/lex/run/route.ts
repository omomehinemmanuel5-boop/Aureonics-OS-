import { NextRequest, NextResponse } from 'next/server';

const DEFAULT_BACKEND_URL = 'http://127.0.0.1:8000';

function getBackendBaseUrl() {
  return process.env.LEX_API_BASE_URL ?? process.env.NEXT_PUBLIC_LEX_API_BASE_URL ?? DEFAULT_BACKEND_URL;
}

export async function POST(request: NextRequest) {
  const body = await request.text();
  const backendBaseUrl = getBackendBaseUrl().replace(/\/$/, '');

  try {
    const upstream = await fetch(`${backendBaseUrl}/lex/run`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      cache: 'no-store',
      body
    });

    const responseBody = await upstream.text();

    return new NextResponse(responseBody, {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('Content-Type') ?? 'application/json'
      }
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: 'Failed to reach Lex backend',
        detail: error instanceof Error ? error.message : 'Unknown upstream error'
      },
      { status: 502 }
    );
  }
}
