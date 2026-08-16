interface DestinationImage {
  keywords: string[];
  photoId: string;
  alt: string;
}

/**
 * Curated cover photography per destination, keyed by keyword match against
 * the free-text destination string. Purely a presentation concern — kept
 * separate from the trip data contract (types/trip.ts) so it never needs to
 * change shape when real agents are wired in.
 */
const DESTINATION_IMAGES: DestinationImage[] = [
  { keywords: ["bali", "indonesia"], photoId: "1537996194471-e657df975ab4", alt: "Terraced rice paddies in Bali" },
  { keywords: ["tokyo", "japan"], photoId: "1540959733332-eab4deabeeaf", alt: "Tokyo skyline at dusk" },
  { keywords: ["lisbon", "portugal"], photoId: "1585208798174-6cedd86e019a", alt: "Yellow tram on the streets of Lisbon" },
  { keywords: ["paris", "france"], photoId: "1502602898657-3e91760cbb34", alt: "The Eiffel Tower in Paris" },
  { keywords: ["bangkok", "thailand"], photoId: "1508009603885-50cf7c579365", alt: "Ornate temple rooftops in Bangkok" },
  { keywords: ["santorini", "greece"], photoId: "1570077188670-e3a8d69ac5ff", alt: "Blue-domed churches of Santorini" },
  { keywords: ["dubai", "uae"], photoId: "1512453979798-5ea266f8880c", alt: "Dubai skyline" },
  { keywords: ["new york", "usa"], photoId: "1496442226666-8d4d0e62e6e9", alt: "New York City skyline" },
];

const FALLBACK_IMAGE: DestinationImage = {
  keywords: [],
  photoId: "1488646953014-85cb44e25828",
  alt: "A scenic travel landscape",
};

function toUrl(photoId: string, width: number, quality = 75) {
  return `https://images.unsplash.com/photo-${photoId}?auto=format&fit=crop&w=${width}&q=${quality}`;
}

export function getDestinationImage(destination: string, width = 1200) {
  const normalized = destination.toLowerCase();
  const match =
    DESTINATION_IMAGES.find((entry) => entry.keywords.some((keyword) => normalized.includes(keyword))) ??
    FALLBACK_IMAGE;

  return { url: toUrl(match.photoId, width), alt: match.alt };
}
