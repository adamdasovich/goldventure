import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL;
if (!BACKEND_URL) {
  // Fail at startup, not at request time
  console.error('FATAL: BACKEND_URL environment variable is required');
}

export const maxDuration = 300; // 5 minutes max duration for Vercel/edge

export async function POST(request: NextRequest) {
  if (!BACKEND_URL) {
    return NextResponse.json(
      { error: 'Chat service is not configured' },
      { status: 503 }
    );
  }

  try {
    const body = await request.json();

    // Forward authorization header from the original request
    const authHeader = request.headers.get('Authorization');

    const response = await fetch(`${BACKEND_URL}/api/claude/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      // Log full error server-side only — never send to client
      console.error('Backend error:', response.status, errorText);
      return NextResponse.json(
        { error: 'An error occurred processing your request' },
        { status: response.status >= 500 ? 502 : response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    // Log full error server-side only — never send to client
    console.error('Claude chat proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to chat service' },
      { status: 502 }
    );
  }
}
