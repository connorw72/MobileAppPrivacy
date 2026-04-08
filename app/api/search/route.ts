import { NextResponse } from "next/server";
import { searchApps } from "@/lib/itunes";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get("q")?.trim();

  if (!query) {
    return NextResponse.json({ error: "Missing search query." }, { status: 400 });
  }

  try {
    const results = await searchApps(query);
    return NextResponse.json({ results });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Search request failed.";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

