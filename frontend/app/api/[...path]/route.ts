import { NextRequest, NextResponse } from 'next/server';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  const pathStr = resolvedParams.path.join('/');
  const { searchParams } = new URL(request.url);
  const targetUrl = `http://127.0.0.1:5000/api/${pathStr}${searchParams.toString() ? '?' + searchParams.toString() : ''}`;

  try {
    const res = await fetch(targetUrl, {
      method: 'GET',
      headers: {
        'Accept': request.headers.get('accept') || '*/*',
      },
    });

    const contentType = res.headers.get('content-type') || 'application/json';
    const body = contentType.includes('audio')
      ? new Uint8Array(await res.arrayBuffer())
      : await res.text();

    return new NextResponse(body, {
      status: res.status,
      headers: {
        'Content-Type': contentType,
      },
    });
  } catch (error: any) {
    console.error(`[Proxy GET Error] for ${targetUrl}:`, error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const resolvedParams = await params;
  const pathStr = resolvedParams.path.join('/');
  const targetUrl = `http://127.0.0.1:5000/api/${pathStr}`;

  try {
    const bodyText = await request.text();
    const res = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: bodyText,
    });

    const resText = await res.text();
    return new NextResponse(resText, {
      status: res.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error: any) {
    console.error(`[Proxy POST Error] for ${targetUrl}:`, error);
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    },
  });
}
