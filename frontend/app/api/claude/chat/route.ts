import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export const maxDuration = 300; // 5 minutes max duration for Vercel/edge

export async function POST(request: NextRequest) {
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
      console.error('Backend error:', response.status, errorText);
      return NextResponse.json(
        { error: `Backend error: ${response.status}`, details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Claude chat proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to chat service', details: String(error) },
      { status: 500 }
    );
  }
}
