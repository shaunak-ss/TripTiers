import { ImageOff } from "lucide-react";
import { useState } from "react";
import { getDestinationImage } from "@/lib/destinationImages";
import { cn } from "@/lib/utils";

interface DestinationImageProps {
  destination: string;
  className?: string;
  width?: number;
  priority?: boolean;
}

export function DestinationImage({ destination, className, width = 1200, priority }: DestinationImageProps) {
  const [errored, setErrored] = useState(false);
  const { url, alt } = getDestinationImage(destination, width);

  if (errored) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-gradient-to-br from-brand-100 to-brand-50 text-brand-300",
          className
        )}
        aria-hidden
      >
        <ImageOff className="size-6" />
      </div>
    );
  }

  return (
    <img
      src={url}
      alt={alt}
      loading={priority ? "eager" : "lazy"}
      decoding="async"
      onError={() => setErrored(true)}
      className={cn("bg-neutral-100 object-cover", className)}
    />
  );
}
