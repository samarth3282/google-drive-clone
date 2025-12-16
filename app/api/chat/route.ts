import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
    try {
        // Get the session cookie from the request
        const cookieStore = await cookies();
        const sessionCookie = cookieStore.get("appwrite-session");

        if (!sessionCookie || !sessionCookie.value) {
            return NextResponse.json(
                { error: "Session expired. Please log in again." },
                { status: 401 }
            );
        }

        // Get the request body
        const body = await request.json();

        // Forward the request to the Python AI backend
        const fastApiUrl = process.env.FASTAPI_URL || "http://localhost:8000";
        const response = await fetch(`${fastApiUrl}/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${sessionCookie.value}`,
            },
            body: JSON.stringify(body),
        });

        if (!response.ok) {
            const errorText = await response.text();
            return NextResponse.json(
                { error: errorText || "Failed to communicate with AI agent" },
                { status: response.status }
            );
        }

        // Stream the response back to the client
        return new NextResponse(response.body, {
            headers: {
                "Content-Type": "text/plain",
                "Transfer-Encoding": "chunked",
            },
        });
    } catch (error) {
        console.error("Chat API error:", error);
        return NextResponse.json(
            { error: "Internal server error" },
            { status: 500 }
        );
    }
}
