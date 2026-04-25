import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

export const api = axios.create({ baseURL: API, timeout: 120000 });

export async function analyzeFile({ resumeFile, resumeText, jdText }) {
  const form = new FormData();
  if (resumeFile) form.append("resume", resumeFile);
  if (resumeText) form.append("resume_text", resumeText);
  form.append("jd_text", jdText);
  const { data } = await api.post("/analyze", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getHistory() {
  const { data } = await api.get("/history");
  return data;
}

export async function getHistoryItem(id) {
  const { data } = await api.get(`/history/${id}`);
  return data;
}

export async function deleteHistoryItem(id) {
  const { data } = await api.delete(`/history/${id}`);
  return data;
}

export async function sendChat(sessionId, question) {
  const { data } = await api.post("/chat", {
    session_id: sessionId,
    question,
  });
  return data;
}

export async function getChatHistory(sessionId) {
  const { data } = await api.get(`/chat/${sessionId}`);
  return data;
}
