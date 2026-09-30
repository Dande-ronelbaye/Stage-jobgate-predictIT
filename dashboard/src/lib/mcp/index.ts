import { defineMcp } from "@lovable.dev/mcp-js";
import predictSalaryTool from "./tools/predict-salary";

export default defineMcp({
  name: "predictit-mcp",
  title: "PredictIT MCP",
  version: "0.1.0",
  instructions:
    "PredictIT exposes a data-driven tech salary predictor. Use `predict_salary` to estimate a yearly EUR salary from a city, experience level, contract type, and a list of technologies. All data is public market intelligence — no user account is required.",
  tools: [predictSalaryTool],
});
