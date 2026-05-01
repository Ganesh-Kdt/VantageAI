import axios from "axios";

const api = axios.create({ baseURL: "" }); // uses proxy to localhost:8000

export const analyzeCompany = (company) =>
  api.post("/analyze", { company});
