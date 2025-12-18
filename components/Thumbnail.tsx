import React from "react";
import Image from "next/image";
import { cn, getFileIcon, constructAuthenticatedFileUrl } from "@/lib/utils";

interface Props {
  type: string;
  extension: string;
  url?: string;
  fileId?: string;
  imageClassName?: string;
  className?: string;
}

export const Thumbnail = ({
  type,
  extension,
  url = "",
  fileId,
  imageClassName,
  className,
}: Props) => {
  const isImage = type === "image" && extension !== "svg";
  
  // Use authenticated URL if fileId is provided, otherwise fall back to url
  const imageUrl = isImage && fileId 
    ? constructAuthenticatedFileUrl(fileId)
    : isImage 
    ? url 
    : getFileIcon(extension, type);

  return (
    <figure className={cn("thumbnail", className)}>
      <Image
        src={imageUrl}
        alt="thumbnail"
        width={100}
        height={100}
        unoptimized={isImage && !!fileId}
        className={cn(
          "size-8 object-contain",
          imageClassName,
          isImage && "thumbnail-image",
        )}
      />
    </figure>
  );
};
export default Thumbnail;
