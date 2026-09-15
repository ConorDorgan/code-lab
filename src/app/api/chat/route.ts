import { NextRequest, NextResponse } from 'next/server';

interface GeminiPart { text: string }
interface GeminiContent { role: string; parts: GeminiPart[] }

export async function POST(req: NextRequest) {
  const apiKey = req.headers.get('x-api-key');
  if (!apiKey) {
    return NextResponse.json({ error: 'Missing API key' }, { status: 401 });
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 });
  }

  const { messages, system } = body as { messages: Array<{ role: string; content: string }>; system?: string };

  // Gemini uses "model" for assistant role
  const contents: GeminiContent[] = messages.map((m) => ({
    role: m.role === 'assistant' ? 'model' : 'user',
    parts: [{ text: m.content }],
  }));

  const response = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        system_instruction: system ? { parts: [{ text: system }] } : undefined,
        contents,
        generationConfig: { maxOutputTokens: 1024 },
      }),
    }
  );

  if (!response.ok) {
    const err = await response.text();
    return NextResponse.json({ error: err }, { status: response.status });
  }

  const data = await response.json();
  const text: string = data.candidates?.[0]?.content?.parts?.[0]?.text ?? '';
  return NextResponse.json({ text });
}
