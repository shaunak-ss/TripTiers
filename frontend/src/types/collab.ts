export interface AuthUser {
  id: string;
  name: string;
  email: string;
  avatarHue: number;
}

export interface CollabMessage {
  id: string;
  roomId: string;
  userId: string;
  displayName: string;
  body: string;
  createdAt: string;
}

export interface CollabMember {
  userId: string;
  displayName: string;
  email?: string;
  joinedAt: string;
}

export interface CollabRoom {
  id: string;
  code: string;
  name: string;
  tripId?: string;
  generatedTripId?: string;
  hostUserId: string;
  members: CollabMember[];
  messages: CollabMessage[];
  createdAt: string;
}
