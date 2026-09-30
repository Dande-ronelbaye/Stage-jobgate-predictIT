import { defineTool } from "@lovable.dev/mcp-js";
import { z } from "zod";
import { mockPredict, type PredictPayload } from "@/lib/api";

export default defineTool({
  name: "predict_salary",
  title: "Predict tech salary",
  description:
    "Estimate a tech salary (EUR/year) from city, experience level, contract type, and technologies. Returns the predicted salary plus market min/median/max, the caller's percentile, top cities, and technology demand shares.",
  inputSchema: {
    city: z
      .string()
      .min(1)
      .describe("City name. Known: Paris, Lyon, Bordeaux, Toulouse, Nantes, Remote, Sousse, Tunis."),
    experience: z
      .enum(["junior", "intermediate", "senior"])
      .describe("Experience level."),
    contract: z
      .enum(["cdi", "freelance", "cdd", "alternance"])
      .describe("Contract type."),
    technologies: z
      .array(z.string().min(1))
      .describe("Technologies in the candidate's stack, e.g. ['React','TypeScript','FastAPI']."),
  },
  annotations: {
    readOnlyHint: true,
    idempotentHint: true,
    openWorldHint: false,
  },
  handler: async (input) => {
    const payload: PredictPayload = {
      city: input.city,
      experience: input.experience,
      contract: input.contract,
      technologies: input.technologies,
    };
    const result = await mockPredict(payload);
    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
      structuredContent: result as unknown as Record<string, unknown>,
    };
  },
});
