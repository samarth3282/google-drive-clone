import { NextRequest, NextResponse } from "next/server";
import { createAdminClient } from "@/lib/appwrite";
import { appwriteConfig } from "@/lib/appwrite/config";
import { getCurrentUser } from "@/lib/actions/user.actions";

// Enable dynamic route
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ fileId: string }> }
) {
  console.log("[File API] Route handler called");
  
  try {
    const { fileId } = await params;
    const { searchParams } = new URL(request.url);
    const action = searchParams.get("action") || "view";

    console.log(`[File API] Request for file ${fileId}, action: ${action}`);

    // Get the current user to ensure they're authenticated
    let currentUser;
    try {
      currentUser = await getCurrentUser();
    } catch (error) {
      console.error("[File API] Error getting current user:", error);
      return NextResponse.json(
        { error: "Authentication error", details: error instanceof Error ? error.message : String(error) },
        { status: 401 }
      );
    }

    if (!currentUser) {
      console.log("[File API] No authenticated user found");
      return NextResponse.json(
        { error: "Unauthorized - Please sign in" },
        { status: 401 }
      );
    }

    console.log(`[File API] User ${currentUser.email} requesting file`);

    // Use admin client to access database and storage
    const { databases, storage } = await createAdminClient();
    console.log("[File API] Admin client created");

    // Check if user has access to this file
    let file;
    try {
      file = await databases.getDocument(
        appwriteConfig.databaseId,
        appwriteConfig.filesCollectionId,
        fileId
      );
      console.log(`[File API] File found: ${file.name}`);
    } catch (error) {
      console.error("[File API] Error getting file document:", error);
      return NextResponse.json(
        { error: "File not found", details: error instanceof Error ? error.message : String(error) },
        { status: 404 }
      );
    }

    // Verify user owns the file or is in the shared users list
    // file.owner can be either a string (user ID) or an object with $id property
    const ownerId = typeof file.owner === 'string' ? file.owner : file.owner?.$id;
    
    const hasAccess =
      ownerId === currentUser.$id ||
      (file.users && file.users.includes(currentUser.email));

    console.log(`[File API] Access check - owner: ${ownerId}, currentUser: ${currentUser.$id}, hasAccess: ${hasAccess}`);

    if (!hasAccess) {
      return NextResponse.json(
        { error: "You don't have permission to access this file" },
        { status: 403 }
      );
    }

    // Get the file from Appwrite storage using direct fetch to REST API
    // The SDK seems to return an unexpected object type in Next.js API routes
    console.log(`[File API] Fetching file from storage: ${file.bucketFileId}`);
    let buffer: Buffer;
    try {
      const fileUrl = `${appwriteConfig.endpointUrl}/storage/buckets/${appwriteConfig.bucketId}/files/${file.bucketFileId}/download?project=${appwriteConfig.projectId}`;
      
      console.log(`[File API] Fetching from URL with admin key`);
      const response = await fetch(fileUrl, {
        method: 'GET',
        headers: {
          'X-Appwrite-Project': appwriteConfig.projectId,
          'X-Appwrite-Key': appwriteConfig.secretKey,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch file: ${response.status} ${response.statusText}`);
      }

      const arrayBuffer = await response.arrayBuffer();
      buffer = Buffer.from(arrayBuffer);
      console.log(`[File API] File downloaded via fetch, size: ${buffer.byteLength}`);
    } catch (error) {
      console.error("[File API] Error downloading file from storage:", error);
      return NextResponse.json(
        { error: "Failed to download file from storage", details: error instanceof Error ? error.message : String(error) },
        { status: 500 }
      );
    }
    
    console.log(`[File API] Buffer ready, size: ${buffer.byteLength}`);

    // Determine content type based on file extension
    const getContentType = (filename: string) => {
      const ext = filename.split('.').pop()?.toLowerCase();
      const contentTypes: { [key: string]: string } = {
        'pdf': 'application/pdf',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'svg': 'image/svg+xml',
        'mp4': 'video/mp4',
        'mp3': 'audio/mpeg',
        'txt': 'text/plain',
        'doc': 'application/msword',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'xls': 'application/vnd.ms-excel',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      };
      return contentTypes[ext || ''] || 'application/octet-stream';
    };

    // Create response with appropriate headers
    const contentType = getContentType(file.name);
    console.log(`[File API] Content-Type: ${contentType}, File: ${file.name}`);
    
    const headers = new Headers();
    headers.set("Content-Type", contentType);
    headers.set("Content-Length", String(buffer.byteLength));
    headers.set("Cache-Control", "private, max-age=3600");

    if (action === "download") {
      headers.set("Content-Disposition", `attachment; filename="${file.name}"`);
    } else {
      headers.set("Content-Disposition", `inline; filename="${file.name}"`);
    }

    console.log("[File API] Returning file successfully");
    
    // Return the file
    return new NextResponse(buffer, {
      status: 200,
      headers,
    });
  } catch (error) {
    console.error("[File API] Unhandled error:", error);
    return NextResponse.json(
      { error: "Failed to fetch file", details: error instanceof Error ? error.message : String(error) },
      { status: 500 }
    );
  }
}
