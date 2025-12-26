import React, { useState } from "react";
import { uploadToCloudinary } from "../utils/cloudinaryUpload";
import { db } from "../firebaseConfig";
import { addDoc, collection, serverTimestamp } from "firebase/firestore";

const FileUpload: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFile(e.target.files?.[0] || null);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select a file first!");
      return;
    }

    setUploading(true);
    setMessage("Uploading...");

    // Validate file type and size
    const allowedTypes = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/jpeg", "image/png"];
    if (!allowedTypes.includes(file.type)) {
      setMessage("❌ Invalid file type. Please upload PDF, DOCX, JPG, or PNG.");
      setUploading(false);
      return;
    }
    if (file.size > 10 * 1024 * 1024) { // 10MB size limit
      setMessage("❌ File too large. Max 10MB allowed.");
      setUploading(false);
      return;
    }
    try {
      const fileURL = await uploadToCloudinary(file);
      await addDoc(collection(db, "notes"), {
        title: file.name,
        fileURL,
        createdAt: serverTimestamp(),
      });
      setMessage("✅ File uploaded successfully!");
      setFile(null);
    } catch (error: any) {
      setMessage("❌ Upload failed. " + (error?.message || "Try again!"));
      // Optionally log error for debugging
      // console.error(error);
    }
    setUploading(false);
  };

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-[#161B22] rounded-2xl shadow-lg w-[400px] mx-auto mt-8">
      <h2 className="text-xl font-semibold text-white mb-4">Upload Note 📄</h2>

      <input
        type="file"
        accept=".pdf,.docx,.jpg,.png"
        onChange={handleFileChange}
        className="text-gray-300 mb-3"
      />

      <button
        onClick={handleUpload}
        disabled={uploading}
        className={`px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition ${
          uploading && "opacity-50 cursor-not-allowed"
        }`}
      >
        {uploading ? "Uploading..." : "Upload"}
      </button>

      {message && <p className="mt-3 text-sm text-gray-300">{message}</p>}
    </div>
  );
};

export default FileUpload;
