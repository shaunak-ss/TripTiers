import { z } from "zod";

export const tripSearchSchema = z
  .object({
    destination: z.string().min(2, "Tell us where you're headed."),
    originCity: z.string().min(2, "Where are you flying from?"),
    startDate: z.string().min(1, "Pick a departure date."),
    endDate: z.string().min(1, "Pick a return date."),
    budget: z
      .number()
      .min(200, "Budgets under $200 won't get you very far — try a bit higher.")
      .max(50000, "That's a big budget — cap it at $50,000 for now."),
    travelers: z
      .number()
      .int()
      .min(1, "At least one traveler, please.")
      .max(12, "For groups over 12, reach out directly."),
  })
  .refine((data) => new Date(data.endDate) > new Date(data.startDate), {
    message: "That return date is before your departure — pick a later one.",
    path: ["endDate"],
  });

export type TripSearchFormValues = z.infer<typeof tripSearchSchema>;
