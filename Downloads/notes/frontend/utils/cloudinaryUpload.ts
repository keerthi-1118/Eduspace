// Simple Cloudinary unsigned upload utility
export async function uploadToCloudinary(file: File): Promise<string> {
  const url = `https://api.cloudinary.com/v1_1/ddtn8mu1t/auto/upload`;
  const formData = new FormData();
  formData.append("file", file);
  formData.append("upload_preset", "ml_default"); // Set your unsigned preset

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error("Cloudinary upload failed");
  }

  const data = await response.json();
  return data.secure_url;
}
