import { generateSummary } from './api';

export async function summarizeText(text: string, resourceId?: number): Promise<string> {
  try {
    // Use backend API for summarization
    return await generateSummary(text, resourceId);
  } catch (error) {
    console.error("Error generating summary:", error);
    throw new Error("Failed to get summary. Please try again.");
  }
}